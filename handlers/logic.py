import asyncio
from collections import OrderedDict

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from create_bot import bot
from keyboards.all_kb import *
from db_handler.requests import insert_address, find_photo, houses_list, like_streets


class Address(StatesGroup):
    new_street = State()
    new_house = State()
    new_entrance = State()
    new_floor = State()
    new_photo = State()
    check_state = State()
    old_street = State()
    old_house = State()
    old_entrance = State()
    old_floor = State()
    old_photo = State()
    check_photo = State()


address_router = Router()


@address_router.callback_query(F.data == 'return')
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Выберите опцию:", reply_markup=main_kb(call.message.from_user.id))


@address_router.message(F.text == "Добавить новый адрес")
async def new_address(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите улицу нового адреса:")
    await state.set_state(Address.new_street)


@address_router.message((F.text == "Найти адрес") | (F.text == "Заменить фото плинта существующего адреса") |
                        (F.text == "Ввести улицу заново"))
async def old_address(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите улицу:")
    await state.set_state(Address.old_street)


@address_router.message(F.text == "Посмотреть список улиц на ту же букву", Address.old_street)
async def streets_list(message: Message, state: FSMContext):
    address = await state.get_data()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        addresses = await like_streets(address.get('old_street').lower())
        streets = list(OrderedDict.fromkeys(list(map(lambda add: add.street, addresses))))
    if streets:
        text = '\n'.join(list(map(lambda street: street.title(), streets)))

        await message.answer("Вот список улиц, начинающихся также: \n \n" + text,
                             reply_markup=main_kb(message.from_user.id))
    else:

        await message.answer("В базе данных нет улиц, начинающихся также.",
                             reply_markup=main_kb(message.from_user.id))
    await state.clear()


@address_router.message(F.text, Address.old_street)
async def capture_street(message: Message, state: FSMContext):
    await state.update_data(old_street=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        addresses = await houses_list(message.text.lower())
        houses = list(OrderedDict.fromkeys(list(map(lambda add: add.house, addresses))))
    if not houses:
        await message.answer("Введённой улицы нет в базе данных. Вы можете посмотреть список всех улиц, "
                             "имеющихся в базе данных и начинающихся на ту же букву; попробовать ввести"
                             " название улицы заново или вернуться в главное меню.", reply_markup=wrong_street_kb())
    else:
        text = '\n'.join(list(map(lambda house: house.title(), houses)))

        await message.answer(
            "Вот список домов на этой улице, для которых есть фото плинта в базе данных: \n \n" + text,
            reply_markup=None)

        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            await asyncio.sleep(0.3)
            await message.answer("Введите номер дома:")
        await state.set_state(Address.old_house)


@address_router.message(F.text, Address.new_street)
async def capture_street(message: Message, state: FSMContext):
    await state.update_data(new_street=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите номер дома:")
    await state.set_state(Address.new_house)


@address_router.message(F.text, Address.new_house)
async def capture_house(message: Message, state: FSMContext):
    await state.update_data(new_house=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите номер подъезда:")
    await state.set_state(Address.new_entrance)


@address_router.message(F.text, Address.old_house)
async def capture_house(message: Message, state: FSMContext):
    await state.update_data(old_house=message.text)
    data = await state.get_data()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)

        await message.answer("Выберите интересующий подъезд и этаж этого дома, которые есть в базе данных.",
                             reply_markup=await floors_list_kb(data.get('old_street').lower().strip(),
                                                               data.get('old_house').lower().strip()))


@address_router.callback_query(F.data.startswith('address_'))
async def show_photo(call: CallbackQuery, state: FSMContext):
    await call.answer()
    [entrance, floor] = call.data.replace('address_', '').split(', ')
    await state.update_data(old_entrance=entrance.strip())
    await state.update_data(old_floor=floor.strip())
    data = await state.get_data()
    async with ChatActionSender.upload_photo(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)

        address = await find_photo(data.get('old_street').lower(), data.get('old_house').lower(),
                                   data.get('old_entrance').lower(), data.get('old_floor').lower())

        caption = f"По адресу: \n\n" \
                  f"<b>Улица</b>: {data.get("old_street").title()}\n" \
                  f"<b>Дом</b>: {data.get("old_house")}\n" \
                  f"<b>Подъезд</b>: {data.get("old_entrance").title()}\n" \
                  f"<b>Этаж</b>: {data.get("old_floor").title()}\n" \
                  f"нашлось такое фото. Хотите его заменить?"

        await call.message.answer_photo(photo=address.photo, caption=caption, reply_markup=check_photo())
    await state.set_state(Address.check_photo)


@address_router.callback_query(F.data == 'change', Address.check_photo)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    await state.update_data(new_street=data.get('old_street'))
    await state.update_data(new_house=data.get('old_house'))
    await state.update_data(new_entrance=data.get('old_entrance'))
    await state.update_data(new_floor=data.get('old_floor'))
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Добавьте фото плинта:")
    await state.set_state(Address.new_photo)


@address_router.callback_query(F.data == 'all', Address.old_house)
async def show_all_photos(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    async with ChatActionSender.upload_photo(bot=bot, chat_id=call.message.chat.id):
        addresses = await find_locations(data.get('old_street').lower(), data.get('old_house').lower())
        entrances_and_floors = list(map(lambda add: (add.entrance, add.floor), addresses))
    for entrance, floor in entrances_and_floors:
        async with ChatActionSender.upload_photo(bot=bot, chat_id=call.message.chat.id):
            await asyncio.sleep(0.1)
            address = await find_photo(data.get('old_street').lower(), data.get('old_house').lower(), entrance, floor)

            caption = f"По адресу: \n\n" \
                      f"<b>Улица</b>: {data.get('old_street').title()}\n" \
                      f"<b>Дом</b>: {data.get('old_house')}\n" \
                      f"<b>Подъезд</b>: {entrance.title()}\n" \
                      f"<b>Этаж</b>: {floor.title()}\n" \
                      f"нашлось такое фото."

            await call.message.answer_photo(photo=address.photo, caption=caption)

    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Хотите ли заменить какое-то из этих фото?",
                                  reply_markup=await change_kb(entrances_and_floors))

    await state.set_state(Address.check_photo)


@address_router.callback_query(F.data == 'thx', Address.check_photo)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Был рад помочь!", reply_markup=main_kb(call.message.from_user.id))
    await state.clear()


@address_router.callback_query(F.data.startswith('change_'), Address.check_photo)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    [entrance, floor] = call.data.replace('change_', '').split(', ')
    data = await state.get_data()
    await state.update_data(new_street=data.get('old_street'))
    await state.update_data(new_house=data.get('old_house'))
    await state.update_data(new_entrance=entrance)
    await state.update_data(new_floor=floor)
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Добавьте фото плинта:")
    await state.set_state(Address.new_photo)


@address_router.callback_query(F.data == 'new', Address.old_house)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    await state.update_data(new_street=data.get('old_street'))
    await state.update_data(new_house=data.get('old_house'))
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Введите номер подъезда:")
    await state.set_state(Address.new_entrance)


@address_router.message(F.text, Address.new_entrance)
async def capture_house(message: Message, state: FSMContext):
    await state.update_data(new_entrance=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите номер этажа:")
    await state.set_state(Address.new_floor)


@address_router.message(F.text, Address.old_entrance)
async def capture_house(message: Message, state: FSMContext):
    await state.update_data(old_entrance=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await asyncio.sleep(0.3)
        await message.answer("Введите номер этажа:")
    await state.set_state(Address.old_floor)


@address_router.message(F.text, Address.new_floor)
async def capture_house(message: Message, state: FSMContext):
    await state.update_data(new_floor=message.text)
    data = await state.get_data()
    address = await find_photo(data.get('new_street').lower().strip(), data.get('new_house').lower().strip(),
                               data.get('new_entrance').lower().strip(), data.get('new_floor').lower().strip())

    if address:
        caption = f"По адресу: \n\n" \
                  f"<b>Улица</b>: {data.get("new_street").title()}\n" \
                  f"<b>Дом</b>: {data.get("new_house")}\n" \
                  f"<b>Подъезд</b>: {data.get("new_entrance").title()}\n" \
                  f"<b>Этаж</b>: {data.get("new_floor").title()}\n" \
                  f"нашлось такое фото. Хотите его заменить?"

        await message.answer_photo(photo=address.photo, caption=caption, reply_markup=check_photo())

        await state.set_state(Address.check_photo)
    else:
        await message.answer("Добавьте фото плинта:")
        await state.set_state(Address.new_photo)


@address_router.message(F.photo, Address.new_photo)
async def capture_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(new_photo=photo_id)
    data = await state.get_data()

    caption = f"Пожалуйста проверьте, всё ли верно: \n\n" \
              f"<b>Улица</b>: {data.get('new_street').title()}\n" \
              f"<b>Дом</b>: {data.get('new_house')}\n" \
              f"<b>Подъезд</b>: {data.get('new_entrance').title()}\n" \
              f"<b>Этаж</b>: {data.get('new_floor').title()}\n"

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.chat.id):
        await message.answer_photo(photo=data.get('new_photo'), caption=caption, reply_markup=check_address())
    await state.set_state(Address.check_state)


@address_router.callback_query(F.data == 'correct', Address.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    address = await state.get_data()
    await call.message.edit_reply_markup(reply_markup=None)
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.1)
        await insert_address(address.get('new_street').lower().strip(), address.get('new_house').lower().strip(),
                             address.get('new_entrance').lower().strip(), address.get('new_floor').lower().strip(),
                             address.get('new_photo'))
        await call.message.answer("Данные сохранены", reply_markup=main_kb(call.message.from_user.id))
    await state.clear()


@address_router.callback_query(F.data == 'incorrect', Address.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await asyncio.sleep(0.3)
        await call.message.answer("Введите улицу нового адреса:")
    await state.set_state(Address.new_street)
