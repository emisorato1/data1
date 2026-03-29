"""Script para cargar datos sintéticos orientados a Escenarios xECM (CAT y RRHH).

Este script crea la jerarquía, grupos, usuarios y documentos requeridos
para ejecutar los escenarios de prueba T6-S6-02.
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
    """Ejecuta el proceso de seed sintético para escenarios xECM."""
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
            Kuaf(id=5001, name="CAT_Users", type=1),
            Kuaf(id=5002, name="RRHH_Team", type=1),
            Kuaf(id=5003, name="Public_All", type=1),
            Kuaf(id=5004, name="Management", type=1),
        ]
        session.add_all(groups)

        # 2. Crear Usuarios (Type=0)
        users = [
            Kuaf(id=6001, name="agente_cat_1", type=0),
            Kuaf(id=6002, name="agente_cat_2", type=0),
            Kuaf(id=6003, name="analista_rrhh_1", type=0),
            Kuaf(id=6004, name="analista_rrhh_2", type=0),
            Kuaf(id=6005, name="manager_cross", type=0),
            Kuaf(id=6006, name="empleado_base", type=0),
        ]
        session.add_all(users)

        # 3. Asignar Membresías (KuafChildren)
        memberships = [
            # CAT Team
            KuafChildren(group_id=5001, child_id=6001),
            KuafChildren(group_id=5001, child_id=6002),
            # RRHH Team
            KuafChildren(group_id=5002, child_id=6003),
            KuafChildren(group_id=5002, child_id=6004),
            # Manager_Cross pertenece a Management, CAT y RRHH
            KuafChildren(group_id=5004, child_id=6005),
            KuafChildren(group_id=5001, child_id=6005),
            KuafChildren(group_id=5002, child_id=6005),
            # Todos en Public
            *[KuafChildren(group_id=5003, child_id=user.id) for user in users],
        ]
        session.add_all(memberships)

        # 4. Crear Jerarquía (Carpetas)
        folders = [
            DTree(data_id=7001, parent_id=None, name="CAT_Knowledge_Base", sub_type=0),
            DTree(data_id=7002, parent_id=None, name="RRHH_Portal", sub_type=0),
            DTree(data_id=7003, parent_id=None, name="Public_Policies", sub_type=0),
        ]
        session.add_all(folders)

        # 5. Generar Documentos y ACLs
        docs = []
        acls = []
        doc_id_counter = 8001

        def add_doc_with_acl(name: str, parent_id: int, group_id: int, permissions: int):
            nonlocal doc_id_counter
            doc_id = doc_id_counter
            docs.append(DTree(data_id=doc_id, parent_id=parent_id, name=name, sub_type=144))
            # ACL: 5=Assigned
            acls.append(DTreeACL(data_id=doc_id, right_id=group_id, acl_type=5, permissions=permissions))
            doc_id_counter += 1
            return doc_id

        # Documentos CAT (Accesibles solo por CAT_Users - Permiso 2: SeeContents)
        add_doc_with_acl("Procedimiento_Bloqueo_Tarjetas.pdf", 7001, 5001, 2)
        add_doc_with_acl("Normativa_Hipotecas_Premier.pdf", 7001, 5001, 2)
        add_doc_with_acl("Circulares_Operativas_Marzo.pdf", 7001, 5001, 2)

        # Documentos RRHH (Accesibles solo por RRHH_Team)
        add_doc_with_acl("Convenio_Colectivo_2026.pdf", 7002, 5002, 2)
        add_doc_with_acl("Beneficios_Directores_Privado.pdf", 7002, 5002, 2)

        # Documento Cross-Area (Carpeta RRHH, pero compartido con CAT)
        cross_doc_id = add_doc_with_acl("Protocolo_Evacuacion_CallCenter.pdf", 7002, 5002, 2)
        # Agregamos ACL explícito para que CAT lo vea
        acls.append(DTreeACL(data_id=cross_doc_id, right_id=5001, acl_type=5, permissions=2))

        # Documentos Públicos
        add_doc_with_acl("Politica_Uso_Correo.pdf", 7003, 5003, 2)

        session.add_all(docs)
        session.add_all(acls)

        # Confirmar datos
        await session.commit()
        logger.info("✅ Escenarios xECM Seed completado: Usuarios, Grupos y Docs CAT/RRHH listos.")

        # 6. Refrescar Vista Materializada para el PermissionResolver
        logger.info("Refrescando la vista materializada kuaf_membership_flat...")
        await session.execute(text("REFRESH MATERIALIZED VIEW kuaf_membership_flat"))
        await session.commit()
        logger.info("✅ Vista materializada actualizada.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
