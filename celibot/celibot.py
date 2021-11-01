import telebot
from telebot import types
from datetime import datetime
from datetime import date
import sqlite3

bot = telebot.TeleBot('token')

def write(table,id,data):
    try:
        with sqlite3.connect('celibat.db', check_same_thread=False) as con:
            con.execute("INSERT into {} values (\"{}\", \"{}\");".format(table,id,data))
    except Exception as e:
        print(e)

def read_break(id):
    try:
        with sqlite3.connect('celibat.db', check_same_thread=False) as con:
            result=[x for x in con.execute("SELECT data from {} WHERE id=(\"{}\");".format(id))]
            return len(result),'\n'.join(result)
    except StopIteration as e:
	        print(e)
		
def update_user(id, data):
    try:
        with sqlite3.connect('celibat.db', check_same_thread=False) as con:
            con.execute("UPDATE users set data =(\"{}\") WHERE id=(\"{}\");".format(data,id))
    except Exception as e:
        print(e)


def read_user(id):
    try:
        with sqlite3.connect('celibat.db', check_same_thread=False) as con:
            return next(con.execute("SELECT data from users WHERE id=(\"{}\");".format(id)))
    except StopIteration as e:
	        print(e)
			
def count_user():
    try:
        with sqlite3.connect('celibat.db', check_same_thread=False) as con:
            all=int(next(con.execute("SELECT count(id) from users;"))[0])
            breaks=len(set([x for x in con.execute("SELECT id from breakdowns;")]))
            return all,all-breaks,'{:.1%}'.format((all-breaks)/all)
    except StopIteration as e:
	        print(e)

@bot.message_handler(commands=['start'])
def start(message):
    if not read_user(message.from_user.id):
        write('users',message.from_user.id, datetime.now().strftime('%Y-%m-%d'))
        bot.reply_to(message, 'Время пошло')

@bot.message_handler(commands=['restart'])
def restart(message):
    if read_user(message.from_user.id):
        update_user(message.from_user.id, datetime.now().strftime('%Y-%m-%d'))
        write('breakdowns', datetime.now().strftime('%Y-%m-%d'),message.from_user.id)
        bot.reply_to(message, 'Время пошло заново')

@bot.message_handler(commands=['check'])
def check(message):
    try:
        if read_user(message.from_user.id):
            bot.reply_to(message, 'Выдержал дней: {}'.format((datetime.now() - datetime.strptime(*read_user(message.from_user.id), '%Y-%m-%d')).days))
			#bot.reply_to(message, 'Выдержал дней: {}\nCрывов: {}\n{}'.format((datetime.now() - datetime.strptime(*read_user(message.from_user.id), '%Y-%m-%d')).days),*read_break(message.from_user.id))
        else:
	        bot.reply_to(message, 'Сначала нужно использовать /start')
    except Exception as e:
        print(e)

@bot.message_handler(commands=['statistics'])
def statistics(message):
    bot.reply_to(message, 'Всего участников: {}\nВыдержало: {}  ({})'.format(*count_user()))
	
info="""команды вводятся после /;
start - начать воздерживаться,
check - проверить количество дней;
statistics - общая статистика;
restart - обнулить дни;
"""

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, info)

#Сделать полноценное inline menu
#Проблема в том что весь код выполняется сразу, а не после выбора пользователем.
@bot.inline_handler(lambda query: len(query.query) == 0)
def default_query(inline_query):
    try:
        if read_user(inline_query.from_user.id):
            days1=(datetime.now() - datetime.strptime(*read_user(inline_query.from_user.id), '%Y-%m-%d')).days
            r1 = types.InlineQueryResultArticle('1', 'Проверить дни', types.InputTextMessageContent('Выдержал дней: {}'.format(days1)))
            r2 = types.InlineQueryResultArticle('2', 'Общая статистика', types.InputTextMessageContent('Всего участников: {}\nВыдержало: {}  ({})'.format(*count_user())))
            r3 = types.InlineQueryResultArticle('3', 'Справка', types.InputTextMessageContent(info))
            bot.answer_inline_query(inline_query.id, [r1,r2,r3])
        else:
            r1 = types.InlineQueryResultArticle('1', 'Справка', types.InputTextMessageContent(info))
            bot.answer_inline_query(inline_query.id, [r1])
    except Exception as e:
        print(e)

if __name__ == '__main__':
    bot.infinity_polling()
