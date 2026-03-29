"""Modelos del espejo de seguridad OpenText (Security Mirror).

Replica fiel del modelo de permisos de OpenText Content Server.
Se mantienen nombres originales (dtree, kuaf, etc.) para garantizar
que la logica de bitmasking (permissions & 2) sea portable.
"""

from sqlalchemy import BigInteger, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class Kuaf(Base):
    """Tabla maestra de entidades OpenText (usuarios y grupos)."""

    __tablename__ = "kuaf"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="Identificador unico en OpenText",
    )
    name: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[int | None] = mapped_column(
        Integer,
        doc="0=User, 1=Group, 5=Role",
    )
    deleted: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))


class KuafChildren(Base):
    """Membresia de grupos/roles OpenText."""

    __tablename__ = "kuafchildren"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="Surrogate PK",
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del Grupo (Rol) en KUAF",
    )
    child_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del Miembro en KUAF",
    )


class DTree(Base):
    """Jerarquia de objetos y documentos OpenText."""

    __tablename__ = "dtree"

    data_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="ID unico del documento u objeto",
    )
    parent_id: Mapped[int | None] = mapped_column(BigInteger)
    owner_id: Mapped[int | None] = mapped_column(BigInteger)
    name: Mapped[str | None] = mapped_column(String(255))
    sub_type: Mapped[int | None] = mapped_column(
        Integer,
        doc="144=Doc, 0=Folder",
    )


class DTreeACL(Base):
    """Lista de control de acceso OpenText."""

    __tablename__ = "dtreeacl"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="Surrogate PK",
    )
    data_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del objeto (DTREE.DataID)",
    )
    right_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del Usuario o Grupo (KUAF.ID)",
    )
    acl_type: Mapped[int | None] = mapped_column(
        Integer,
        doc="1=Owner, 2=OwnerGroup, 3=Public, 5=Assigned",
    )
    permissions: Mapped[int | None] = mapped_column(
        Integer,
        doc="Bitmask de permisos. See=1, SeeContents=2, Modify=65536",
    )


class DTreeAncestors(Base):
    """Jerarquia ancestral de documentos OpenText (para Chinese Walls)."""

    __tablename__ = "dtreeancestors"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="Surrogate PK",
    )
    data_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del nodo hijo",
    )
    ancestor_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        doc="ID del nodo ancestro",
    )
    depth: Mapped[int | None] = mapped_column(
        Integer,
        doc="Profundidad en la jerarquia",
    )
