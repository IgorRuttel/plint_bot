from sqlalchemy import select, ScalarResult

from db_handler.models import async_session
from db_handler.models import Address


async def insert_address(street: str, house: str, entrance: str, floor: str, photo: str) -> None:
    async with async_session() as session:
        address = await session.scalar(select(Address).where(Address.street == street,
                                                             Address.house == house, Address.entrance == entrance,
                                                             Address.floor == floor))
        if not address:
            session.add(Address(street=street, house=house, entrance=entrance, floor=floor, photo=photo))

        else:
            address.photo = photo

        await session.commit()


async def find_photo(street: str, house: str, entrance: str, floor: str) -> Address:
    async with async_session() as session:
        return await session.scalar(select(Address).where(Address.street == street,
                                                           Address.house == house, Address.entrance == entrance,
                                                           Address.floor == floor))


async def delete_address(street: str, house: str, entrance: str, floor: str) -> None:
    async with async_session() as session:
        address = await session.scalar(select(Address).where(Address.street == street,
                                                             Address.house == house, Address.entrance == entrance,
                                                             Address.floor == floor))
        if address:
            await session.delete(address)
            await session.commit()


async def houses_list(street: str) -> ScalarResult:
    async with async_session() as session:
        return await session.scalars(select(Address).where(Address.street == street))


async def like_streets(street: str) -> ScalarResult:
    async with async_session() as session:
        return await session.scalars(select(Address).where(Address.street.like(f'{street.strip()[0]}%')))


async def entrances_list(street: str, house: str) -> ScalarResult:
    async with async_session() as session:
        return await session.scalars(select(Address).where(Address.street == street,
                                                           Address.house == house))


async def find_locations(street: str, house: str) -> ScalarResult:
    async with async_session() as session:
        return await session.scalars(select(Address).where(Address.street == street,
                                                           Address.house == house))
