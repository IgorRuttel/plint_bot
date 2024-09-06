import asyncio
from collections import OrderedDict

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from create_bot import bot
from keyboards.all_kb import *
import db_handler.requests as rq


class Address(StatesGroup):
    street = State()
    house = State()
    entrance = State()
    floor = State()
    check_state = State()


admin_router = Router()


@admin_router.message(F.text == "Админ панель")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        if message.from_user.id not in admins:
            await message.answer(text="Вы не обладаете правами администратора",
                                 reply_markup=main_kb(message.from_user.id))
        else:
            await message.answer(text="Вы можете удалить адрес существующий адрес или вернуться",
                                 reply_markup=admin_kb())


@admin_router.message((F.text == "Удалить адрес") | (F.text == "Ввести адрес заново"))
async def delete_address(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        if message.from_user.id not in admins:
            await message.answer(text="Для удаления адреса обратитесь к администратору",
                                 reply_markup=main_kb(message.from_user.id))
        else:
            await message.answer(text="Введите улицу:", reply_markup=None)
            await state.set_state(Address.street)


@admin_router.message(F.text == "Посмотреть список улиц на ту же букву", Address.street)
async def streets_list(message: Message, state: FSMContext):
    address = await state.get_data()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        addresses = await rq.like_streets(address.get('street').lower())
        streets = list(OrderedDict.fromkeys(list(map(lambda add: add.street, addresses))))
    if streets:
        text = '\n'.join(list(map(lambda street: street.title(), streets)))

        await message.answer(text="Вот список улиц, начинающихся также: \n \n" + text,
                             reply_markup=main_kb(message.from_user.id))
    else:
        await message.answer(text="В базе данных нет улиц, начинающихся также.",
                             reply_markup=main_kb(message.from_user.id))
    await state.clear()


@admin_router.message(F.text, Address.street)
async def capture_street(message: Message, state: FSMContext):
    await state.update_data(street=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        find = await rq.houses_list(message.text.lower())
    if not find:
        await message.answer(text="Введённой улицы нет в базе данных. Вы можете посмотреть список всех улиц, "
                             "имеющихся в базе данных и начинающихся на ту же букву; попробовать ввести название улицы"
                             " заново или вернуться в главное меню.", reply_markup=wrong_street_kb())
        await state.clear()
    else:
        await message.answer(text="Введите номер дома:")
        await state.set_state(Address.house)


@admin_router.message(F.text, Address.house)
async def delete_house(message: Message, state: FSMContext):
    await state.update_data(house=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        await message.answer(text="Введите номер подъезда:")
    await state.set_state(Address.entrance)


@admin_router.message(F.text, Address.entrance)
async def delete_house(message: Message, state: FSMContext):
    await state.update_data(entrance=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.1)
        await message.answer(text="Введите номер этажа:")
    await state.set_state(Address.floor)


@admin_router.message(F.text, Address.floor)
async def delete_house(message: Message, state: FSMContext):
    await state.update_data(floor=message.text)
    data = await state.get_data()
    async with ChatActionSender.choose_sticker(bot=bot, chat_id=message.chat.id):
        address = await rq.find_photo(data.get('street').lower().strip(), data.get('house').lower().strip(),
                                      data.get('entrance').lower().strip(), data.get('floor').lower().strip())
    if address:

        caption = f"По адресу: \n\n" \
                  f"<b>Улица</b>:{data.get('street').title()}\n" \
                  f"<b>Дом</b>:{data.get('house')}\n" \
                  f"<b>Подъезд</b>: {data.get('entrance').title()}\n" \
                  f"<b>Этаж</b>: {data.get('floor').title()}\n" \
                  f"нашлось такое фото. Хотите его удалить?"

        await message.answer_photo(photo=address.photo, caption=caption, reply_markup=check_photo_adm())
        await state.set_state(Address.check_state)
    else:
        await message.answer(text="По искомому адресу не нашлось фото в базе данных. Провертье правильность адреса "
                             "и попробуйте ввести адрес заново или вернитесь в начало.",
                             reply_markup=wrong_address_kb())

        await state.clear()


@admin_router.callback_query(F.data == 'delete', Address.check_state)
async def delete_address(call: CallbackQuery, state: FSMContext):
    address = await state.get_data()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.1)
        await rq.delete_address(address.get('street').lower(), address.get('house').lower(),
                                address.get('entrance').lower(), address.get('floor').lower())

    await call.message.answer("Адрес успешно удалён")
    await call.message.edit_reply_markup(reply_markup=None)
    await state.clear()


@admin_router.callback_query(F.data == 'thx', Address.check_state)
async def not_delete_address(call: CallbackQuery, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Отменяю удаление")
    await call.message.edit_reply_markup(reply_markup=None)
    await state.clear()
