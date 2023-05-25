#!/bin/python3

from config import TOKEN_GRAM, HELP_COMMAND, CHANEL_ID
import uuid, asyncio, logging
import logging.config
from log_settings import log_config
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from keyboard import *
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import current_handler, CancelHandler
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext, DEFAULT_RATE_LIMIT
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import top_month
from sqlite import *

logging.config.dictConfig(log_config)
bot_log = logging.getLogger('bot')


storage = MemoryStorage()
bot = Bot(TOKEN_GRAM)
dp = Dispatcher(bot=bot, storage=storage)
sheduler = AsyncIOScheduler()


class AdminsMiddleware(BaseMiddleware):

    async def on_pre_process_update(self, update: types.Update, data: dict):
        users = await check_rights()
        print(f'on_pre_process_update {update}')

        if 'channel_post' in update:
            bot_log.debug(f'on_pre_process_update: channel_post: {update}')
            if update.channel_post.video:
                num = await get_num()
                num += 1
                await set_num(num)

        elif 'message' in update:
            bot_log.debug(f'on_pre_process_update: message: {update}')
            if update.message.from_user.id not in users:
                # print(f'ACCESS DENIED FOR {update.message.from_user.id}')
                if (update.message.chat.type != 'group') or (update.message.sender_chat.type != 'channel'):
                    await update.message.answer(
                        text=f'Доступа нет. Отправь свой ID {update.message.from_user.id} админу.')
                raise CancelHandler()

        elif 'callback_query' in update:
            bot_log.debug(f'on_pre_process_update: callback_query: {update}')
            pass
            # if update.callback_query.from_user.id not in users:
            #     print(f'ACCESS DENIED FOR {update.callback_query.from_user.id}')
            #     await update.callback_query.answer(
            #         text=f'Доступа нет. Отправь свой ID {update.callback_query.from_user.id} админу.')
            #     raise CancelHandler()

            # print(f'ACCESS GRANTED FOR {update.callback_query.from_user.id}')
        else:
            bot_log.debug(f'on_pre_process_update: апдейт не прошел по условию {update}')
            raise CancelHandler()


    async def on_post_process_message(self, message: types.Message, data: dict, handler):
        try:
            if 'video' in message:
                text = message.caption
                is_post = 1
            else:
                text = message.text
                is_post = 0
            await add_message(message_id=message.message_id,
                              text=text,
                              user_id=message.from_user.id,
                              first_name=message.from_user.first_name,
                              username=message.from_user.username,
                              is_post=is_post)
        except Exception:
            bot_log.exception(f'on_post_process_message: непредвиденная ошибка: {message}')

    async def on_post_process_update(self, update: types.Update, data: dict, handler):
        print(f'post-proc-update {update}')

    # async def on_post_process_callback_query(self, callback_query: types.CallbackQuery, data: dict, handler):
    #
    #     # print(f'POST CALLBACK {callback_query}')
    #     # print(handler)
    #
    #     like = await like_count(callback_query.message.message_id)
    #     dislike = await dislike_count(callback_query.message.message_id)
    #     await callback_query.message.edit_reply_markup(reply_markup=get_ikb(like, dislike))

    # async def on_post_process_update(self, update: types.Update, data: dict, handler):
    #     print(f'POST PROCESS^ {update.message}')


class AdminStateGroups(StatesGroup):
    user_id = State()
    name = State()

class NumStateGroups(StatesGroup):
    num = State()


async def on_startup(_):
    await start_db()
    schedul_job()
    bot_log.info('Бот успешно запущен')
    print('Бот успешно запущен')

def schedul_job():
    sheduler.add_job(top_month, 'cron', year='*', month='*', day=24, hour=8, minute=1, second=0)

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    if state is None:
        return
    await message.answer(text='Отменено')
    await state.finish()
    bot_log.debug(f'Применена команда /cancel: {message}')


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer(text='<b>Бот для пересылки видео..</b>',
                         parse_mode='HTML')
    await message.delete()
    bot_log.debug(f'Применена команда /start: {message}')


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer(text=HELP_COMMAND,
                         parse_mode='HTML')
    await message.delete()
    bot_log.debug(f'Применена команда /help: {message}')


@dp.message_handler(commands=['admin'])
async def admin_command(message: types.Message):
    await message.answer(text='Укажи ID пользователя, которого нужно сделать админом.',
                         reply_markup=get_cancel())
    await AdminStateGroups.user_id.set()
    bot_log.debug(f'Применена команда /admin: {message}')

@dp.message_handler(commands=['top'])
async def top_command(message: types.Message):
    topss = await check_top()
    t = ''
    for tops in topss:
        top = ' '.join(str(to) for to in tops)
        t = t + '\n' + top
    await message.answer(text=f'<b>TOP:\n {t}</b>',
                         parse_mode='HTML')
    bot_log.debug(f'Применена команда /top: {message}')

@dp.message_handler(commands=['getnum'])
async def getnum_command(message: types.Message):
    num = await get_num()
    await message.answer(text=f'Текущий порядковый номер записи: {num}')
    bot_log.debug(f'Применена команда /getnum: {message}')

@dp.message_handler(commands=['setnum'])
async def setnum_command(message: types.Message):
    await message.answer(text='Введи порядкой номер.',
                         reply_markup=get_cancel())
    await NumStateGroups.num.set()
    bot_log.debug(f'Применена команда /setnum: {message}')

@dp.message_handler(commands=['comment'])
async def comment_command(message: types.Message):
    comm = await check_comment()
    comm = 1 if comm == 0 else 0
    await set_comment(comm)
    if comm == 1:
        await message.answer(text='Комментарии включены')
        bot_log.debug(f'Применена команда /comment на включение комментариев: {message}')
    else:
        await message.answer(text='Комментарии отключены')
        bot_log.debug(f'Применена команда /comment на отключение комментариев: {message}')


@dp.message_handler(lambda message: not message.text.isdigit(), content_types=['text'], state=AdminStateGroups.user_id)
async def check_id(message: types.Message) -> None:
    bot_log.info(f'При назначении админа указан некорректный ID: {message.text}')
    return await message.reply(text='Это не ID')


@dp.message_handler(content_types=['text'], state=AdminStateGroups.user_id)
async def load_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['user_id'] = message.text
    await message.reply(text='Укажи имя пользователя.')
    await AdminStateGroups.next()


@dp.message_handler(lambda message: not message.text, content_types=['text'], state=AdminStateGroups.name)
async def check_name(message: types.Message) -> None:
    bot_log.info(f'При назначении админа указано некорректное имя: {message.text}')
    return await message.reply(text='Это не имя.')


@dp.message_handler(content_types=['text'], state=AdminStateGroups.name)
async def load_desc(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await add_admin(state)
    bot_log.debug(f'Назначен админ: {message.text}')
    await message.reply(text='Готово.')
    await state.finish()

@dp.message_handler(lambda message: not message.text.isdigit(), content_types=['text'], state=NumStateGroups.num)
async def check_num(message: types.Message) -> None:
    bot_log.info(f'Указан неверный порядковый номер: {message.text}')
    return await message.reply(text='Это не номер.')


@dp.message_handler(content_types=['text'], state=NumStateGroups.num)
async def setnum_handle(message: types.Message, state: FSMContext) -> None:
    await set_num(message.text)
    bot_log.debug(f'Задан порядковый номер записи: {message.text}')
    await message.reply(text=f'Задан порядковый номер записи: {message.text}')
    await state.finish()

@dp.message_handler(lambda message: message.video, content_types=['video'])
async def resend_video(message: types.Message):
    # print(message.video)
    num = await get_num()
    caption = f"№{num}: {message.caption if message.caption else 'Video'}"
    like = await like_count(message.message_id)
    dislike = await dislike_count(message.message_id)
    await bot.send_video(chat_id=CHANEL_ID,
                         video=message.video.file_id,
                         caption=caption,
                         supports_streaming=True,
                         reply_markup=await get_ikb(like, dislike))
    num += 1
    bot_log.info(f'Успешно переслано видео от {message.from_user.username}')
    await set_num(num)


@dp.callback_query_handler(cb.filter(action='like'))
# @rate_limit(4, 'start')
async def like_handle(callback: types.CallbackQuery, callback_data=dict) -> None:
    await add_user(callback.from_user.id, callback.from_user.first_name, callback.from_user.username)
    if await check_if_voted(callback.message.message_id, callback.from_user.id, 1):
        await callback.answer(text='ALREADY VOTED', cache_time=1)
    else:
        await set_vote(callback.message.message_id, callback.from_user.id, 1)
        like = await like_count(callback.message.message_id)
        dislike = await dislike_count(callback.message.message_id)
        await callback.message.edit_reply_markup(reply_markup=await get_ikb(like, dislike))
        await callback.answer(text='LIKE', cache_time=1)


@dp.callback_query_handler(cb.filter(action='dislike'))
# @rate_limit(4, 'start')
async def dislike_handle(callback: types.CallbackQuery, callback_data=dict) -> None:
    await add_user(callback.from_user.id, callback.from_user.first_name, callback.from_user.username)

    if await check_if_voted(callback.message.message_id, callback.from_user.id, 0):
        await callback.answer(text='ALREADY VOTED', cache_time=1)
    else:
        await set_vote(callback.message.message_id, callback.from_user.id, 0)
        like = await like_count(callback.message.message_id)
        dislike = await dislike_count(callback.message.message_id)
        await callback.message.edit_reply_markup(reply_markup=await get_ikb(like, dislike))
        await callback.answer(text='DISLIKE', cache_time=1)


if __name__ == '__main__':
    # dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(AdminsMiddleware())
    sheduler.start()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
