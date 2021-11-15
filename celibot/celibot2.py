#!venv/bin/python
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from aiogram.utils.exceptions import BotBlocked
import aiosqlite
from datetime import datetime

bot = Bot(token="")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

info="""Доступные команды:
/start - меню;
/start_timer - запустить счётчик;
/reset_timer - обнулить дни;
/check - проверить количество дней;
/statistics - общая статистика;
/help - это сообщение.
"""

async def write(table,id,data):
    async with aiosqlite.connect('celibat.db') as con:
        await con.execute("INSERT into {} values (\"{}\", \"{}\");".format(table,id,data))
        await con.commit()
		
async def read_break(id):
    try:
        async with aiosqlite.connect('celibat.db') as con:
            result= await [x for x in con.execute("SELECT data from {} WHERE id=(\"{}\");".format(id))]
            return len(result),'\n'.join(result)
    except StopIteration:
	        return
		
async def update_user(id, data):
    async with aiosqlite.connect('celibat.db') as con:
        await con.execute("UPDATE users set data =(\"{}\") WHERE id=(\"{}\");".format(data,id))
		
async def read_user(id):
    try:
        async with aiosqlite.connect('celibat.db') as con:
            async with con.execute("SELECT data from users WHERE id=(\"{}\");".format(id)) as cursor:
                return await cursor.fetchone()
    except StopIteration:
	        return
			
async def count_user():
    try:
        async with aiosqlite.connect('celibat.db') as con:
            async with con.execute("SELECT count(id) from users;") as cursor:
                async for row in cursor:
                    all=int(row[0])
            async with con.execute("SELECT id from breakdowns;") as cursor:
                breaks=await cursor.fetchall()
            breaks= len(set(breaks))
            return all,all-breaks,'{:.1%}'.format((all-breaks)/all)
    except StopIteration:
	        return


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    buttonStartTimer = types.InlineKeyboardButton('▶️ Запустить таймер')
    buttonRestartTimer = types.InlineKeyboardButton('🔄 Сбросить таймер')
    buttonCheck = types.InlineKeyboardButton('🔎 Проверить')
    buttonStats = types.InlineKeyboardButton('📊 Общая статистика')

    markup.row(buttonStartTimer, buttonRestartTimer)
    markup.row(buttonCheck, buttonStats)
    await message.answer(f'{info}', reply_markup=markup)

@dp.message_handler(commands='start_timer')
async def start_timer(message):
    if not await read_user(message.from_user.id):
        await write('users',message.from_user.id, datetime.now().strftime('%Y-%m-%d'))
        await message.reply('Время пошло')
    else:
        await message.reply('Время уже пошло. Если хочешь сбросить таймер, то используй /reset_timer')

@dp.message_handler(commands='reset_timer')
async def reset_timer(message):
    if await read_user(message.from_user.id):
        await update_user(message.from_user.id, datetime.now().strftime('%Y-%m-%d'))
        await write('breakdowns', datetime.now().strftime('%Y-%m-%d'),message.from_user.id)
        await message.reply('Время пошло заново')


@dp.message_handler(commands='check')
async def check(message):
    try:
        readed=await read_user(message.from_user.id)
        if readed:
            await message.reply('Выдержал дней: {}'.format((datetime.now() - datetime.strptime(*readed, '%Y-%m-%d')).days))
        else:
	        await message.reply('Сначала нужно использовать /start')
    except Exception as e:
        print(e)

@dp.message_handler(commands='statistics')
async def statistics(message):
    stat=await count_user()
    await message.reply('Всего участников: {}\nВыдержало: {}  ({})'.format(*stat))

@dp.message_handler()
async def after_text(message):
    if message.text == '▶️ Запустить таймер':
        await start_timer(message)
    if message.text == '🔄 Сбросить таймер':
        await reset_timer(message)
    if message.text == '🔎 Проверить':
        await check(message)
    if message.text == '📊 Общая статистика':
        await statistics(message)
    if message.text == '❓ Справка':
        await help(message)

@dp.inline_handler()
async def default_query(inline_query: InlineQuery):
    try:
        readed = await read_user(inline_query.from_user.id)
        if readed:
            counted=await count_user()
            days1= (datetime.now() - datetime.strptime(*readed, '%Y-%m-%d')).days
            r1 = InlineQueryResultArticle(id='1', title='🔎 Проверить дни', input_message_content=types.InputTextMessageContent('Выдержал дней: {}'.format(days1)))
            r2 = InlineQueryResultArticle(id='2', title='📊 Общая статистика', input_message_content=types.InputTextMessageContent('Всего участников: {}\nВыдержало: {}  ({})'.format(*counted)))
            r3 = InlineQueryResultArticle(id='3', title='❓ Справка', input_message_content=types.InputTextMessageContent(info))
            await bot.answer_inline_query(inline_query.id, [r1,r2,r3], cache_time=1)
        else:
            r1 = InlineQueryResultArticle(id='3', title='❓ Справка', input_message_content=types.InputTextMessageContent(info))
            await bot.answer_inline_query(inline_query.id, [r1])
    except Exception as e:
        print(e)

@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    # Update: объект события от Telegram. Exception: объект исключения
    # Здесь можно как-то обработать блокировку, например, удалить пользователя из БД
    print(f"Меня заблокировал пользователь!\nСообщение: {update}\nОшибка: {exception}")

    # Такой хэндлер должен всегда возвращать True,
    # если дальнейшая обработка не требуется.
    return True

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)