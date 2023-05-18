from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from sqlite import *
from config import GROUP_ID


cb = CallbackData('ikb', 'action')


def get_ikb(like, dislike) -> InlineKeyboardMarkup:

    ikb = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [InlineKeyboardButton(text=f'👍 {like}', callback_data=cb.new('like')),
         InlineKeyboardButton(text=f'👎 {dislike}', callback_data=cb.new('dislike'))],
        [InlineKeyboardButton(text=f'Оставить комментарий', url='https://t.me/c/{}/'.format(GROUP_ID))]
    ])

    return ikb

def get_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('/cancel'))