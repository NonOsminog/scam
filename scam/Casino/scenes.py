from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

main = ReplyKeyboardMarkup(
    resize_keyboard=True,
	keyboard = [
		[
            KeyboardButton(text='🎰 Играть'),
            KeyboardButton(text='🙎‍♂ Мой профиль')
		],
        [
            KeyboardButton(text='ℹ️ Информация')
        ]
	]
)

games = InlineKeyboardMarkup(
    inline_keyboard = [
        [
            InlineKeyboardButton(text='Random Number', callback_data='random_number')
        ],
        [
            InlineKeyboardButton(text='Орёл & Решка', callback_data='orel_reshka')
        ],
        [
            InlineKeyboardButton(text='Random Dice', callback_data='random_dice')
        ]
    ]
)

information = InlineKeyboardMarkup(
	inline_keyboard = [
        [
            InlineKeyboardButton(text='👨‍💻 Тех. поддержка', url="tg://resolve?domain=RoyalCasSupps"),
        ],
        [
            InlineKeyboardButton(text='💾 Пользовательское соглашение', url='https://telegra.ph/Polzovatelskoe-soglashenie-11-13-5'),
            InlineKeyboardButton(text='💼 Лицензия', callback_data='license')
        ]
	]
)

def interval(amount) -> InlineKeyboardMarkup:
    biggest_50 = InlineKeyboardButton(text='> 50', callback_data=f'RandomNumberr,{amount},biggest')
    equals_50 = InlineKeyboardButton(text='= 50', callback_data=f'RandomNumberr,{amount},equals')
    smaller_50 = InlineKeyboardButton(text='< 50', callback_data=f'RandomNumberr,{amount},smaller')
    return InlineKeyboardMarkup(row_width=3).add(biggest_50, equals_50, smaller_50)

def coin(amount) -> InlineKeyboardMarkup:
    biggest_50 = InlineKeyboardButton(text='Орёл', callback_data=f'Coinflip,{amount},Orel')
    equals_50 = InlineKeyboardButton(text='Решка', callback_data=f'Coinflip,{amount},Reshka')
    return InlineKeyboardMarkup(row_width=3).add(biggest_50, equals_50)

pt1 = InlineKeyboardButton('Отмена', callback_data='cancel')
cancel = InlineKeyboardMarkup(row_width=1).add(pt1)