"""Script para cargar datos sintéticos de OpenText Content Server (Permisos y Jerarquía).

Este script crea:
- 10+ usuarios
- 5+ grupos
- 50+ documentos
- Membresía de usuarios a grupos
- Asignación de permisos usando bitmasking (See=1, SeeContents=2, Modify=65536)
- Refresco de la vista materializada kuaf_membership_flat.
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.config.settings import settings
from src.infrastructure.database.models.permission import DTree, DTreeACL, Kuaf, KuafChildren

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Ejecuta el proceso de seed sintético."""
    engine = create_async_engine(settings.database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        # Limpiar datos previos
        await session.execute(text("TRUNCATE TABLE dtreeacl CASCADE"))
        await session.execute(text("TRUNCATE TABLE dtree CASCADE"))
        await session.execute(text("TRUNCATE TABLE kuafchildren CASCADE"))
        await session.execute(text("TRUNCATE TABLE kuaf CASCADE"))

        # 1. Crear Grupos (Type=1)
        groups = [
            Kuaf(id=1001, name="Riesgos_Corp", type=1),
            Kuaf(id=1002, name="Compliance_Team", type=1),
            Kuaf(id=1003, name="Audit_Internal", type=1),
            Kuaf(id=1004, name="IT_Sec_Admins", type=1),
            Kuaf(id=1005, name="Executive_Board", type=1),
            Kuaf(id=1006, name="Public_All", type=1),  # Grupo general
            # Grupos anidados para probar Recursive CTE (3 niveles)
            Kuaf(id=1007, name="Global_Directors", type=1),  # Nivel 1
            Kuaf(id=1008, name="Regional_Managers", type=1),  # Nivel 2
            Kuaf(id=1009, name="Local_Supervisors", type=1),  # Nivel 3
        ]
        session.add_all(groups)

        # 2. Crear Usuarios (Type=0)
        users = [
            Kuaf(id=2001, name="alice_riesgos", type=0),
            Kuaf(id=2002, name="bob_riesgos", type=0),
            Kuaf(id=2003, name="charlie_comp", type=0),
            Kuaf(id=2004, name="diana_comp", type=0),
            Kuaf(id=2005, name="edward_audit", type=0),
            Kuaf(id=2006, name="fiona_audit", type=0),
            Kuaf(id=2007, name="george_it", type=0),
            Kuaf(id=2008, name="helen_it", type=0),
            Kuaf(id=2009, name="ian_exec", type=0),
            Kuaf(id=2010, name="julia_exec", type=0),
            Kuaf(id=2011, name="kevin_temp", type=0),
            Kuaf(id=2012, name="laura_temp", type=0),
            # Usuario para tests de anidamiento
            Kuaf(id=2013, name="mike_nested", type=0),
        ]
        session.add_all(users)

        # 3. Asignar Membresías (KuafChildren)
        memberships = [
            # Riesgos
            KuafChildren(group_id=1001, child_id=2001),
            KuafChildren(group_id=1001, child_id=2002),
            # Compliance
            KuafChildren(group_id=1002, child_id=2003),
            KuafChildren(group_id=1002, child_id=2004),
            # Audit
            KuafChildren(group_id=1003, child_id=2005),
            KuafChildren(group_id=1003, child_id=2006),
            # IT Sec
            KuafChildren(group_id=1004, child_id=2007),
            KuafChildren(group_id=1004, child_id=2008),
            # Executive (Los execs también están en todos los grupos base o en Public)
            KuafChildren(group_id=1005, child_id=2009),
            KuafChildren(group_id=1005, child_id=2010),
            # Jerarquía Anidada: Global (1007) -> Regional (1008) -> Local (1009) -> Mike (2013)
            KuafChildren(group_id=1007, child_id=1008),  # Global_Directors contiene a Regional_Managers
            KuafChildren(group_id=1008, child_id=1009),  # Regional_Managers contiene a Local_Supervisors
            KuafChildren(group_id=1009, child_id=2013),  # Local_Supervisors contiene a Mike
            # Un ciclo de membresía intencional (para probar protección contra ciclos)
            # Local_Supervisors (1009) es miembro de Global_Directors (1007)
            KuafChildren(group_id=1009, child_id=1007),
            # Todos en Public
            *[KuafChildren(group_id=1006, child_id=user.id) for user in users],
        ]
        session.add_all(memberships)

        # 4. Crear Jerarquía y Documentos
        # Carpetas (SubType=0)
        folders = [
            DTree(data_id=3001, parent_id=None, name="Politicas_Riesgo", sub_type=0),
            DTree(data_id=3002, parent_id=None, name="Reportes_Compliance", sub_type=0),
            DTree(data_id=3003, parent_id=None, name="Auditorias_2024", sub_type=0),
            DTree(data_id=3004, parent_id=None, name="IT_Security_Logs", sub_type=0),
            DTree(data_id=3005, parent_id=None, name="Directorio", sub_type=0),
            DTree(data_id=3006, parent_id=None, name="Documentos_Publicos", sub_type=0),
        ]
        session.add_all(folders)

        # Generar 50+ Documentos (SubType=144)
        docs = []
        acls = []
        doc_id_counter = 4001

        # Función helper para crear un documento y su permiso
        def add_doc_with_acl(name: str, parent_id: int, group_id: int, permissions: int):
            nonlocal doc_id_counter
            doc_id = doc_id_counter
            docs.append(DTree(data_id=doc_id, parent_id=parent_id, name=name, sub_type=144))

            # ACL: 1=Owner, 2=OwnerGroup, 3=Public, 5=Assigned
            acls.append(DTreeACL(data_id=doc_id, right_id=group_id, acl_type=5, permissions=permissions))

            # Añadir siempre acceso a los ejecutivos si no es público (solo como ejemplo extra)
            if group_id != 1006:
                acls.append(DTreeACL(data_id=doc_id, right_id=1005, acl_type=5, permissions=permissions))

            doc_id_counter += 1

        # Generar docs para Riesgos (Permiso SeeContents=2 | Modify=4 -> 6)
        for i in range(1, 11):
            add_doc_with_acl(f"Riesgo_Crediticio_{i}.pdf", 3001, 1001, 6)

        # Generar docs para Compliance (Permiso SeeContents=2)
        for i in range(1, 11):
            add_doc_with_acl(f"Normativa_Compliance_{i}.pdf", 3002, 1002, 2)

        # Generar docs para Audit (Permiso SeeContents=2)
        for i in range(1, 11):
            add_doc_with_acl(f"Auditoria_Trimestral_{i}.pdf", 3003, 1003, 2)

        # Generar docs para IT Sec (Permiso See=1, SeeContents=2 -> 3)
        for i in range(1, 11):
            add_doc_with_acl(f"Log_Seguridad_{i}.txt", 3004, 1004, 3)

        # Generar docs Públicos (Permiso See=1, SeeContents=2 -> 3)
        for i in range(1, 11):
            add_doc_with_acl(f"Politica_General_{i}.pdf", 3006, 1006, 3)

        # Generar docs Restringidos a Exec (Permiso SeeContents=2 | Modify=4 -> 6)
        for i in range(1, 6):
            add_doc_with_acl(f"Acta_Directorio_{i}.pdf", 3005, 1005, 6)

        session.add_all(docs)
        session.add_all(acls)

        # Confirmar datos
        await session.commit()
        logger.info("✅ Insertados 12 Usuarios, 6 Grupos, 55 Documentos y sus ACLs.")

        # 5. Refrescar la Vista Materializada
        logger.info("Refrescando la vista materializada kuaf_membership_flat...")
        await session.execute(text("REFRESH MATERIALIZED VIEW kuaf_membership_flat"))
        await session.commit()
        logger.info("✅ Vista materializada refrescada con éxito.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
