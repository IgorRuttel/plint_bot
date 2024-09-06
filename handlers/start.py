from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.all_kb import main_kb

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет!\nЯ - бот, который может показать фото плинта на искомом адресе, "
                         "если он добавлен в базу данных, или добавить новый адрес в базу данных.",
                         reply_markup=main_kb(message.from_user.id))


@start_router.message(F.text == "Вернуться в начало")
async def return_to_main(message: Message):
    await message.answer("Выберите опцию:", reply_markup=main_kb(message.from_user.id))
