from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from create_bot import admins
from db_handler.requests import find_locations


def main_kb(user_telegram_id: int) -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="Добавить новый адрес"), KeyboardButton(text="Найти адрес")],
        [KeyboardButton(text="Заменить фото плинта существующего адреса")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="Админ панель")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True,
                                   one_time_keyboard=True, input_field_placeholder="Воспользуйтесь меню:")
    return keyboard


def wrong_street_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="Ввести улицу заново"), KeyboardButton(text="Посмотреть список улиц на ту же букву")],
        [KeyboardButton(text="Вернуться в начало")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


def wrong_address_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="Ввести адрес заново"), KeyboardButton(text="Вернуться в начало")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


def check_address() -> InlineKeyboardMarkup:
    kb_list = [
        [InlineKeyboardButton(text="Всё верно", callback_data='correct')],
        [InlineKeyboardButton(text="Ввести адрес заново", callback_data='incorrect')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


def check_photo() -> InlineKeyboardMarkup:
    kb_list = [
        [InlineKeyboardButton(text="Заменить фото", callback_data='change')],
        [InlineKeyboardButton(text="Нет, спасибо", callback_data='thx')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


def check_photo_adm() -> InlineKeyboardMarkup:
    kb_list = [
        [InlineKeyboardButton(text="Удалить адрес", callback_data='delete')],
        [InlineKeyboardButton(text="Нет, спасибо", callback_data='thx')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


def admin_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="Удалить адрес")],
        [KeyboardButton(text="Вернуться в начало")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)

    return keyboard


async def floors_list_kb(street: str, house: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    addresses = await find_locations(street, house)

    entrances_and_floors = list(map(lambda add: (add.entrance, add.floor), addresses))

    for entrance, floor in entrances_and_floors:
        builder.row(
            InlineKeyboardButton(text='Подъезд ' + entrance + ', ' 'этаж ' + floor,
                                 callback_data=f'address_{entrance}, {floor}')
        )

    if entrances_and_floors:
        builder.row(
            InlineKeyboardButton(text='Показать все фото', callback_data='all')
        )
    builder.row(
        InlineKeyboardButton(text='Вернуться в начало', callback_data='return')
    )

    builder.adjust(1)
    return builder.as_markup(one_time_keyboard=True)


async def change_kb(entrances_and_floors: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for entrance, floor in entrances_and_floors:
        builder.row(
            InlineKeyboardButton(text="Заменить фото: " + 'подъезд ' + entrance + ', ' + 'этаж ' + floor,
                                 callback_data=f'change_{entrance}, {floor}')
        )
    builder.row(
        InlineKeyboardButton(text="Нет, спасибо", callback_data="thx")
    )
    builder.adjust(1)
    return builder.as_markup(one_time_keyboard=True)
