"""xECM synchronisation service — keeps the Security Mirror up to date.

Orchestrates data flow from OpenText Content Server (via OpenTextClient)
into the PostgreSQL security mirror tables (kuaf, kuafchildren, dtree,
dtreeacl, dtreeancestors).

Two sync modes:
- **Full sync**: Bulk-load all entities (initial setup or recovery).
- **Delta sync**: Process DAUDITNEW events since the last checkpoint.

The DB models already exist in ``src.infrastructure.database.models.permission``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import delete

from src.infrastructure.database.models.permission import (
    DTree,
    DTreeACL,
    Kuaf,
    KuafChildren,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.infrastructure.ecm.opentext_client import OpenTextClient

logger = logging.getLogger(__name__)


class XECMSyncService:
    """Synchronises OpenText permission data into the local Security Mirror.

    Usage
    -----
    ```python
    async with async_session_maker() as session:
        client = ConcreteOpenTextClient(base_url=..., credentials=...)
        sync = XECMSyncService(session=session, client=client)
        await sync.full_sync()
        await session.commit()
    ```
    """

    def __init__(self, session: AsyncSession, client: OpenTextClient) -> None:
        self._session = session
        self._client = client

    # ── Full Sync ────────────────────────────────────────────────────

    async def full_sync(self) -> dict[str, int]:
        """Run a full synchronisation of all security mirror tables.

        Returns
        -------
        dict[str, int]
            Count of rows upserted per table.
        """
        await self._client.authenticate()

        counts: dict[str, int] = {}

        # 1. Users & Groups → kuaf
        users = await self._client.fetch_users_and_groups()
        for user in users:
            await self._session.merge(Kuaf(id=user.id, name=user.name, type=user.type, deleted=user.deleted))
        counts["kuaf"] = len(users)
        logger.info("sync_kuaf_complete count=%d", len(users))

        # 2. Group memberships → kuafchildren
        memberships = await self._client.fetch_group_memberships()
        # Clear and re-insert (membership is cheap and idempotent)
        await self._session.execute(delete(KuafChildren))
        for mem in memberships:
            self._session.add(KuafChildren(group_id=mem.group_id, child_id=mem.child_id))
        counts["kuafchildren"] = len(memberships)
        logger.info("sync_kuafchildren_complete count=%d", len(memberships))

        # 3. Document nodes → dtree
        nodes = await self._client.fetch_nodes()
        for node in nodes:
            await self._session.merge(
                DTree(
                    data_id=node.data_id,
                    parent_id=node.parent_id,
                    owner_id=node.owner_id,
                    name=node.name,
                    sub_type=node.sub_type,
                )
            )
        counts["dtree"] = len(nodes)
        logger.info("sync_dtree_complete count=%d", len(nodes))

        # 4. Permissions → dtreeacl
        data_ids = [n.data_id for n in nodes]
        if data_ids:
            permissions = await self._client.fetch_permissions(data_ids)
            # Clear and re-insert for authoritative snapshot
            await self._session.execute(delete(DTreeACL))
            for perm in permissions:
                self._session.add(
                    DTreeACL(
                        data_id=perm.data_id,
                        right_id=perm.right_id,
                        acl_type=perm.acl_type,
                        permissions=perm.permissions,
                    )
                )
            counts["dtreeacl"] = len(permissions)
            logger.info("sync_dtreeacl_complete count=%d", len(permissions))

        # 5. Ancestors → dtreeancestors
        # TODO: Compute ancestor paths from dtree parent_id hierarchy
        # and populate dtreeancestors for Chinese Wall enforcement.
        counts["dtreeancestors"] = 0
        logger.info("sync_dtreeancestors_skipped reason=not_yet_implemented")

        await self._session.flush()
        logger.info("full_sync_complete counts=%s", counts)
        return counts

    # ── Delta Sync (CDC via DAUDITNEW) ───────────────────────────────

    async def delta_sync(self, since_event_id: int = 0) -> dict[str, int]:
        """Process incremental changes from DAUDITNEW audit events.

        Parameters
        ----------
        since_event_id:
            Process events with ID > this value. Track externally
            (e.g. in a ``sync_checkpoints`` table).

        Returns
        -------
        dict[str, int]
            Count of events processed by type.
        """
        await self._client.authenticate()

        events = await self._client.fetch_audit_events(since_event_id=since_event_id)
        counts: dict[str, int] = {"processed": 0, "skipped": 0}

        for event in events:
            # TODO: Dispatch on event type:
            #   - AuditCreate / AuditModify → re-fetch node + permissions
            #   - AuditDelete → mark deleted or remove from mirror
            #   - AuditMoveNode → update parent_id + ancestors
            #   - AuditChangePermissions → re-fetch ACL for data_id
            #   - AuditAddMember / AuditRemoveMember → update kuafchildren
            event_type = event.get("type", "unknown")
            logger.debug("delta_sync_event type=%s data_id=%s", event_type, event.get("data_id"))
            counts["skipped"] += 1

        # TODO: After processing, refresh kuaf_membership_flat materialized view:
        #   await self._session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY kuaf_membership_flat"))

        await self._session.flush()
        logger.info("delta_sync_complete since=%d counts=%s", since_event_id, counts)
        return counts

    # ── Helpers ──────────────────────────────────────────────────────

    async def _rebuild_ancestors(self, data_ids: list[int] | None = None) -> int:
        """Rebuild dtreeancestors from dtree parent_id hierarchy.

        Parameters
        ----------
        data_ids:
            If provided, only rebuild for these nodes. Otherwise rebuild all.

        Returns
        -------
        int
            Number of ancestor rows inserted.
        """
        # TODO: Implement recursive CTE to walk parent_id chain
        # and populate DTreeAncestors for Chinese Wall enforcement.
        _ = data_ids  # suppress unused warning
        logger.warning("rebuild_ancestors not_yet_implemented")
        return 0
