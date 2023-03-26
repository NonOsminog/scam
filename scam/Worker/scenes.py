from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from environs import Env

env = Env()
env.read_env()

UserInfoCallback = CallbackData("Questionnaire", "status", "username", "user_id")

pt1 = InlineKeyboardButton('Отмена', callback_data='cancel')
cancel = InlineKeyboardMarkup(row_width=1).add(pt1)

agree = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text = '✅Ознакомлен с правилами', callback_data = 'rules')
		]
	]
)

trading_users = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text = '🦣 Список мамонтов', callback_data = 'list_users_trading'),
            InlineKeyboardButton(text = '⚙️ Изменить минималку', callback_data = 'setMinDeposit_trading')
		]
	]
)

casino_users = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text = '🦣 Список мамонтов', callback_data = 'list_users_casino'),
            InlineKeyboardButton(text = '⚙️ Изменить минималку', callback_data = 'setMinDeposit_casino')
		]
	]
)

links = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text='📃 Мануалы', url=env.str('LINK_MANUAL')),
            InlineKeyboardButton(text='💰 Выплаты', url=env.str('LINK_WITHDRAWS')),
            InlineKeyboardButton(text='💬 Чат', url=env.str('LINK_CHAT'))
        ]
	]
)

main = ReplyKeyboardMarkup(
    resize_keyboard=True,
	keyboard = [
		[
            KeyboardButton(text='💻 Мой профиль')
		],
        [
            KeyboardButton(text='📈 Трейдинг'),
            KeyboardButton(text='🎰 Казино')
        ],
        [
            KeyboardButton(text='🗃 О проекте')
		]
	]
)

main_admin = ReplyKeyboardMarkup(
    resize_keyboard=True,
	keyboard = [
		[
            KeyboardButton(text='💻 Мой профиль')
		],
        [
            KeyboardButton(text='📈 Трейдинг'),
            KeyboardButton(text='🎰 Казино')
        ],
        [
            KeyboardButton(text='🗃 О проекте'),
            KeyboardButton(text='💻 Админ-меню')
		]
	]
)

admin_menu = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text = '📲 Сменить Qiwi', callback_data = 'change_qiwi'),
            InlineKeyboardButton(text = '📨 Рассылка', callback_data = 'newsletter')
		]
	]
)

changeQiwiBot = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text = '📈 Трейдинг', callback_data = 'change_qiwi_trading'),
            InlineKeyboardButton(text = '🎰 Казино', callback_data = 'change_qiwi_casino')
		]
	]
)

def admin_solution(username: str, user_id: int) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton(text = '✅ Подтвердить заявку', callback_data = UserInfoCallback.new(status = 'Accept', username = username, user_id = user_id))
    false = InlineKeyboardButton(text = '🚫 Отклонить заявку', callback_data = UserInfoCallback.new(status = 'Decline', username = username, user_id = user_id))
    return InlineKeyboardMarkup().add(accept, false)