from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

main = ReplyKeyboardMarkup(
    resize_keyboard=True,
	keyboard = [
		[
            KeyboardButton(text='💼 Личный Кабинет'),
            KeyboardButton(text='📈 Мой ECN счёт')
		],
        [
            KeyboardButton(text='ℹ️ Информация'),
            KeyboardButton(text='🧑🏻‍💻Тех. Поддержка')
        ]
	]
)

ts = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text='Тех. поддержка', url='https://t.me/TradesSuppBinance'),
        ]
	]
)

profile = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text='💳 Пополнить', callback_data='deposit'),
            InlineKeyboardButton(text='🏦 Вывести', callback_data='withdraw')
        ]
	]
)

information = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text='📈 Состояние сети', callback_data='stats_network'),
        ],
        [
            InlineKeyboardButton(text='⚙️ Реферальная система', callback_data='referal_system')
        ],
        [
            InlineKeyboardButton(text='ℹ️ Пользовательское соглашение', url='https://telegra.ph/Polzovatelskoe-soglashenie-BINANCE-TRADE-11-08')
        ]
	]
)

pt1 = InlineKeyboardButton('Отмена', callback_data='cancel')
cancel = InlineKeyboardMarkup(row_width=1).add(pt1)

# selectPay = InlineKeyboardMarkup(
# 	inline_keyboard = [
#         [
#             InlineKeyboardButton(text = '💵 Оплатить Qiwi/Картой', callback_data = 'selectPay_qiwi')
# 		]
# 	]
# )