import enum
from typing import List
import datetime
from sqlalchemy import ForeignKey, func, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, TEXT, INTEGER, ARRAY, BOOLEAN, JSON
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    pass


class Sources(Base):
    __tablename__ = "sources"
    __table_args__ = {'schema': 'maps'}
    source_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    primary_table: Mapped[str] = mapped_column(VARCHAR(255))
    url: Mapped[str] = mapped_column(VARCHAR(255))
    ref_title: Mapped[str] = mapped_column(TEXT)
    authors: Mapped[str] = mapped_column(VARCHAR(255))
    ref_year: Mapped[str] = mapped_column(TEXT)
    ref_source: Mapped[str] = mapped_column(VARCHAR(255))
    isbn_doi: Mapped[str] = mapped_column(VARCHAR(100))
    scale: Mapped[str] = mapped_column(VARCHAR(20))
    primary_line_table: Mapped[str] = mapped_column(VARCHAR(50))
    licence: Mapped[str] = mapped_column(VARCHAR(100))
    features: Mapped[int] = mapped_column(INTEGER)
    area: Mapped[int] = mapped_column(INTEGER)
    priority: Mapped[bool] = mapped_column(BOOLEAN)
    rgeom: Mapped[str] = mapped_column(Geometry('POLYGON'))
    display_scales: Mapped[list[str]] = mapped_column(ARRAY(TEXT))
    web_geom: Mapped[str] = mapped_column(Geometry('POLYGON'))
    new_priority: Mapped[int] = mapped_column(INTEGER)
    status_code: Mapped[str] = mapped_column(TEXT)


class GroupMembers(Base):
    __tablename__ = "group_members"
    __table_args__ = {'schema': 'macrostrat_auth'}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("macrostrat_auth.group.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("macrostrat_auth.user.id"))


class Group(Base):
    __tablename__ = "group"
    __table_args__ = {'schema': 'macrostrat_auth'}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    users: Mapped[List["User"]] = relationship(secondary="macrostrat_auth.group_members", lazy="joined", back_populates="groups")


class User(Base):
    __tablename__ = "user"
    __table_args__ = {'schema': 'macrostrat_auth'}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sub: Mapped[str] = mapped_column(VARCHAR(255))
    name: Mapped[str] = mapped_column(VARCHAR(255))
    email: Mapped[str] = mapped_column(VARCHAR(255))
    groups: Mapped[List[Group]] = relationship(secondary="macrostrat_auth.group_members", lazy="joined", back_populates="users")
    created_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Token(Base):
    __tablename__ = "token"
    __table_args__ = {'schema': 'macrostrat_auth'}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    group: Mapped[Group] = mapped_column(ForeignKey("macrostrat_auth.group.id"))
    used_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    created_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SchemeEnum(enum.Enum):
    http = "http"
    s3 = "s3"


class Objects(Base):
    __tablename__ = "objects"
    __table_args__ = (
        UniqueConstraint('scheme', 'host', 'bucket', 'key', name='unique_file'),
        {'schema': 'macrostrat'}
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scheme: Mapped[str] = mapped_column(Enum(SchemeEnum))
    host: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    bucket: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    key: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    source: Mapped[dict] = mapped_column(JSON)
    mime_type: Mapped[str] = mapped_column(VARCHAR(255))
    sha256_hash: Mapped[str] = mapped_column(VARCHAR(255))
    created_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
