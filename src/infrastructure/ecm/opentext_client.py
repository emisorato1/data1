"""Abstract OpenText Content Server client.

Defines the contract for interacting with OpenText REST API v2
(or xECM Extended ECM) to synchronise security mirror tables.
Concrete implementations should handle authentication (OAuth2 / OTDS),
pagination, and retry logic.

See: .opencode/skills/security-mirror/ for the full data model reference.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# ── Data Transfer Objects ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class OTUser:
    """Represents a KUAF row (user or group) from OpenText."""

    id: int
    name: str
    type: int  # 0=User, 1=Group, 5=ProjectGroup
    deleted: int = 0


@dataclass(frozen=True, slots=True)
class OTGroupMembership:
    """Represents a KUAFCHILDREN row (group → member)."""

    group_id: int
    child_id: int


@dataclass(frozen=True, slots=True)
class OTNode:
    """Represents a DTREE row (document/folder node)."""

    data_id: int
    parent_id: int | None
    owner_id: int | None
    name: str
    sub_type: int  # 144=Document, 0=Folder, 202=Project


@dataclass(frozen=True, slots=True)
class OTPermission:
    """Represents a DTREEACL row."""

    data_id: int
    right_id: int
    acl_type: int  # 1=Owner, 2=OwnerGroup, 3=Public, 5=Assigned
    permissions: int  # bitmask: See=1, SeeContents=2, Modify=65536


# ── Abstract Client ─────────────────────────────────────────────────


class OpenTextClient(ABC):
    """Abstract base class for OpenText Content Server API clients.

    Implementations must authenticate via OTDS (OAuth2) and handle
    pagination / throttling per the Content Server REST API v2 spec.
    """

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with OpenText and obtain an access token.

        Raises
        ------
        ExternalServiceError
            If authentication fails.
        """
        # TODO: Implement OTDS OAuth2 authentication flow

    @abstractmethod
    async def fetch_users_and_groups(
        self,
        *,
        since_event_id: int | None = None,
    ) -> list[OTUser]:
        """Fetch users and groups from KUAF.

        Parameters
        ----------
        since_event_id:
            If provided, only return entities modified after this
            DAUDITNEW event ID (delta sync).

        Returns
        -------
        list[OTUser]
            Users and groups to upsert into the security mirror.
        """
        # TODO: GET /api/v2/members with pagination

    @abstractmethod
    async def fetch_group_memberships(
        self,
        group_ids: list[int] | None = None,
    ) -> list[OTGroupMembership]:
        """Fetch group membership records from KUAFCHILDREN.

        Parameters
        ----------
        group_ids:
            If provided, limit to these groups. Otherwise fetch all.

        Returns
        -------
        list[OTGroupMembership]
            Membership edges to upsert.
        """
        # TODO: GET /api/v2/members/{id}/members with pagination

    @abstractmethod
    async def fetch_nodes(
        self,
        *,
        parent_id: int | None = None,
        since_event_id: int | None = None,
    ) -> list[OTNode]:
        """Fetch document/folder nodes from DTREE.

        Parameters
        ----------
        parent_id:
            If provided, only fetch children of this node.
        since_event_id:
            If provided, only return nodes modified after this event.

        Returns
        -------
        list[OTNode]
            Nodes to upsert into the security mirror.
        """
        # TODO: GET /api/v2/nodes/{id}/nodes with pagination

    @abstractmethod
    async def fetch_permissions(
        self,
        data_ids: list[int],
    ) -> list[OTPermission]:
        """Fetch ACL entries for the given node IDs.

        Parameters
        ----------
        data_ids:
            Node IDs to fetch permissions for.

        Returns
        -------
        list[OTPermission]
            ACL entries to upsert into the security mirror.
        """
        # TODO: GET /api/v2/nodes/{id}/permissions

    @abstractmethod
    async def fetch_audit_events(
        self,
        *,
        since_event_id: int = 0,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Fetch DAUDITNEW events for change-data-capture sync.

        Parameters
        ----------
        since_event_id:
            Fetch events with ID greater than this value.
        limit:
            Maximum number of events to return per call.

        Returns
        -------
        list[dict[str, Any]]
            Raw audit event dicts. The caller is responsible for
            dispatching deletes, permission changes, etc.
        """
        # TODO: GET /api/v2/nodes/audit with pagination

    @abstractmethod
    async def close(self) -> None:
        """Release HTTP session and resources."""
        # TODO: Close aiohttp / httpx session
