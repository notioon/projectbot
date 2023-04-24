import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data.config import BOT_TOKEN
from methods.copilot import get_answer
from methods.dalle import create_picture
from methods.sql import Sql_db


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

messages = []

SQL = Sql_db()


class UserState(StatesGroup):
    state0 = State()
    state1 = State()
    state2 = State()
    state3 = State()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    SQL.add_user(message.chat.id, message.chat.username, message.chat.first_name)
    buttons = [[types.KeyboardButton(text="🤖 Нейронки"), types.KeyboardButton(text="⚙ Настройки")],
               [types.KeyboardButton(text="🌺 Профиль")], [types.KeyboardButton("🍀 О проекте")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Welcome !", reply_markup=keyboard)


@dp.message_handler()
async def main_menu(message: types.Message):
    if message.text == "🍀 О проекте":
        await message.answer("На текущий момент у нас две основные функции — диалоги с ChatGPT и создание картинок "
                             "через DALL-E и аналог Midjourney, каждая из них оплачивается отдельно, в зависимости от "
                             "вашего Запроса.\n\n💎 Диалоги с ChatGPT работают на токенах\n\nТокен — это топливо для "
                             "работы нейросети и общения с СhatGPT. После каждого запроса количество токенов "
                             "уменьшается.\n\n☀ Генерации изображений работают на запросах\n\nПроект сделан в "
                             "ознакомительных целях.")

    elif message.text == "🤖 Нейронки":
        buttons = [
            [types.InlineKeyboardButton("💬 ChatGPT", callback_data="gpt")],
            [types.InlineKeyboardButton("🎨 DALL-E", callback_data="dalle")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Выберите нейронную сеть: ", reply_markup=keyboard)

    elif message.text == "🌺 Профиль":
        data = SQL.find_user(message.chat.id)
        await message.answer(f"👋 @{data[2]}\n❤ {data[3]}\n\n"
                             f"💰 Баланс: 0 ¥\n\n🔹 Запросов на генерацию картинок осталось: ∞\n"
                             f"🔹 Токенов ChatGPT осталось: ∞\n\n💎 Подписка ChatGPT:  SuperUltraMega")

    elif message.text == "⚙ Настройки":
        data = SQL.find_user(message.chat.id)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton("✏ Изменить токен", callback_data="change_token")]])
        await message.answer(f"🔑 Актуальный OpenAI токен:\n       *{data[-1]}*", parse_mode="Markdown", reply_markup=keyboard)


@dp.callback_query_handler(text="change_token")
async def change_token_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton("Отмена", callback_data="cancel")]])
    await callback.message.answer("✏ Введите новый токен:", reply_markup=keyboard)
    await UserState.state2.set()


@dp.message_handler(state=UserState.state2)
async def change_token(message: types.Message, state: FSMContext):
    SQL.change_token(message.chat.id, message.text)
    await message.answer("🔑 Токен успешно изменен!")
    await state.finish()


@dp.callback_query_handler(text='dalle', state='*')
async def dalle_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer()
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton("Отмена", callback_data='cancel')]])
    await callback.message.answer("💬 Введите максимально точный Запрос текстом", reply_markup=keyboard)
    await UserState.state1.set()


@dp.message_handler(state=UserState.state1)
async def generate_picture(message: types.Message, state: FSMContext):
    token = SQL.find_user(message.chat.id)[-1]
    buttons = [[types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.update_data(dalle=message.text)
    await message.answer('⌛ Работаем над запросом...')
    await message.answer_photo(photo=create_picture(message.text, token), reply_markup=keyboard)
    await state.finish()


@dp.callback_query_handler(text='gpt', state='*')
async def chatpgt_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton("Отмена", callback_data='cancel')]])
    await callback.message.answer("💬 Введите максимально точный Запрос текстом", reply_markup=keyboard)
    await UserState.state0.set()


@dp.message_handler(state=UserState.state0)
async def get_message_gpt(message: types.Message, state: FSMContext):
    token = SQL.find_user(message.chat.id)[-1]
    buttons = [[types.InlineKeyboardButton("Новый диалог", callback_data='new_dialog'),
         types.InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.update_data(gpt=message.text)
    await message.answer('⌛ Работаем над запросом...')
    messages.append({"role": "user", "content": message.text})
    response = get_answer(messages, token)
    result = response.choices[0]['message']
    messages.append(result)
    await message.answer(result['content'], reply_markup=keyboard)
    await UserState.state0.set()


@dp.callback_query_handler(text='new_dialog', state='*')
async def new_dialog(callback: types.CallbackQuery, state: FSMContext):
    global messages
    await state.finish()
    await callback.answer()
    messages = []
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton("Отмена", callback_data='cancel')]])
    await callback.message.answer("💬 Введите максимально точный Запрос текстом", reply_markup=keyboard)
    await UserState.state0.set()


@dp.callback_query_handler(text='cancel', state='*')
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer("🛑 Действие отменено")


@dp.callback_query_handler(text='back_to_menu', state='*')
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.answer()
    buttons = [
        [types.InlineKeyboardButton("💬 ChatGPT", callback_data="gpt")],
        [types.InlineKeyboardButton("🎨 Dall-E", callback_data="dalle")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Выберите нейронную сеть: ", reply_markup=keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)