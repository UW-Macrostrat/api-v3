#
# File of all db accesses
#
# When they can be they are made with the SQLAlchemy ORM model
#
# On the bottom you will find the methods that do not use this method
#

from os import environ
from typing import Type

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import text, select, update, Table, MetaData, CursorResult, func
from sqlalchemy.exc import NoResultFound, NoSuchTableError

from starlette.requests import QueryParams

from dotenv import load_dotenv

import api.schemas as schemas
from api.query_parser import query_parser

load_dotenv()

INTEGRATION_DATABASE_URL = environ.get("DB_URL", None)

engine: AsyncEngine = None


def get_engine():
    return engine


async def connect_engine() -> AsyncEngine:
    global engine
    engine = create_async_engine(INTEGRATION_DATABASE_URL)


async def dispose_engine():
    global engine
    await engine.dispose()


def get_async_session(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine)


async def source_id_to_primary_table(async_session: async_sessionmaker[AsyncSession], source_id: id):
    async with async_session() as session:
        stmt = select(schemas.Sources).where(schemas.Sources.source_id == source_id)
        result = await session.scalar(stmt)

        if result is None:
            raise NoResultFound(f"Could not find primary_table corresponding with source_id: {source_id}")

        return result.primary_table


async def get_sources(async_session: async_sessionmaker[AsyncSession], page: int = 0, page_size: int = 100):
    async with async_session() as session:
        stmt = select(schemas.Sources).offset(page_size * page).limit(page_size).order_by(schemas.Sources.source_id)
        result = await session.scalars(stmt)

        return [*result]


async def get_schema_tables(engine: AsyncEngine, schema: str):
    async with engine.begin() as conn:

        q = text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema")
        params = {"schema": schema}
        q = q.bindparams(**params)

        result = await conn.execute(q)

        return map(lambda x: x[0], result.fetchall())


#
# Here starts the use on the engine object directly
#

class SQLResponse:

    def __init__(self, columns, results):
        self.columns = list(columns)
        self.results = results

    def to_dict(self):
        """Converts the response to the 'record' format list"""

        l = []
        for result in self.results:
            d = {}
            for i, v in enumerate(result):

                d[self.columns[i]] = result[i]

            l.append(d)

        return l


async def get_polygon_table_name(engine: AsyncEngine, table_id: int) -> str:
    session = get_async_session(engine)
    try:
        primary_table = await source_id_to_primary_table(session, table_id)
        return f"{primary_table}_polygons"
    except NoResultFound as e:
        raise NoSuchTableError(e)

async def get_sources_sub_table_count(engine: AsyncEngine, table_id: int) -> int:
    async with engine.begin() as conn:

        # Grabbing a table from the database as it is
        metadata = MetaData(schema="sources")
        polygon_table = await get_polygon_table_name(engine, table_id)
        table = await conn.run_sync(lambda sync_conn: Table(polygon_table, metadata, autoload_with=sync_conn))

        stmt = select(func.count()).select_from(table)

        result = await conn.execute(stmt)

        return result.scalar()


async def select_sources_sub_table(engine: AsyncEngine, table_id: int, page: int = 0, page_size: int = 100, query_params: list = None) -> SQLResponse:
    async with engine.begin() as conn:

        # Grabbing a table from the database as it is
        metadata = MetaData(schema="sources")
        polygon_table = await get_polygon_table_name(engine, table_id)
        table = await conn.run_sync(lambda sync_conn: Table(polygon_table, metadata, autoload_with=sync_conn))

        # Extract filters from the query parameters
        column_expressions = query_parser(query_params, table)

        # Strip out the unwanted columns
        ignored_columns = ['geom']  # No reason that this moment to pass this through
        selected_columns = table.c[*[col.key for col in table.c if col.key not in ignored_columns]]

        stmt = select(selected_columns)\
            .limit(page_size)\
            .offset(page_size * page)\
            .where(column_expressions)

        result = await conn.execute(stmt)

        response = SQLResponse(result.keys(), result.fetchall())

        return response


async def patch_sources_sub_table(engine: AsyncEngine, table_id: int, update_values: dict, query_params: list = None) -> CursorResult:
    async with engine.begin() as conn:

        # Grabbing a table from the database as it is
        metadata = MetaData(schema="sources")
        polygon_table = await get_polygon_table_name(engine, table_id)
        table = await conn.run_sync(lambda sync_conn: Table(polygon_table, metadata, autoload_with=sync_conn))

        # Extract filters from the query parameters
        column_expressions = query_parser(query_params, table)

        stmt = update(table).where(column_expressions).values(**update_values)

        x = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        result = await conn.execute(stmt)

        return result