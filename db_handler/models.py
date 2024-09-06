from sqlalchemy import TEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///../data/db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Address(Base):

    __tablename__ = 'addresses'

    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str] = mapped_column()
    house: Mapped[str] = mapped_column()
    entrance: Mapped[str] = mapped_column()
    floor: Mapped[str] = mapped_column()
    photo = mapped_column(TEXT)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
