import random
import threading
import psycopg2 as pg
import telebot
from telebot import types
from time import sleep
import time
import requests
from threading import Thread

phone = "79180550501"
token = '5221668103:AAGmoPyhe1c4B3l2A9MHgC_kl8IJcORhaW8'  # Telegram
my_login = "79180550501"
api_access_token = "b128c09e276f5e3ed879209ff26c8549"  # Qiwi token

bot = telebot.TeleBot(token, parse_mode=None)

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
item1 = types.KeyboardButton("Пополнить баланс")
item2 = types.KeyboardButton("Выиграть случайны приз")
item3 = types.KeyboardButton("Баланс")
markup.add(item1)
markup.add(item2)
markup.add(item3)
markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
item0 = types.KeyboardButton("Назад")
markup1.add(item0)
item01 = types.KeyboardButton("Оплатил")
item02 = types.KeyboardButton("Назад")
markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup2.add(item01)
markup2.add(item02)
payments = {}
comment = {}
last_message = {}


@bot.message_handler(commands=["start"])
def start(m):
    connection = pg.connect(database='users', user='code', password='coder', host="127.0.0.1", port="5432")
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users_list VALUES ('" + str(m.chat.id) + "', 0,'@" + str(m.from_user.username) + "' ) on CONFLICT "
                                                                                                      "DO NOTHING;")
    connection.commit()
    connection.close()
    bot.send_message(m.chat.id, 'Я на связи. Напиши мне что-нибудь )', reply_markup=markup)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == "Пополнить баланс":
        last_message[message.chat.id] = "Пополнить баланс"
        bot.send_message(message.chat.id, 'Введите сумму пополнения баланса', reply_markup=markup1)
    elif message.text.strip() == "Выиграть случайны приз":
        bot.send_message(message.chat.id, "Поздравляем! Вот ваш бит: " + randomik(), reply_markup=markup)
    elif message.text.strip() == "Баланс":
        bot.send_message(message.chat.id, "Ваш баланс: " + str(balance(message.chat.id)) + " руб", reply_markup=markup)
    elif message.text.strip() == "Назад":
        bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)
    elif message.text.strip() == "Оплатил":
        bot.send_message(message.chat.id, "Спасибо, за пополнение баланса,"
                                          " как только деньги поступят мы пришлем вам сообщение ", reply_markup=markup)
        threading.currentThread()
        t2 = Thread(target=checker, args=(message, comment[message.chat.id]), daemon=True)
        t2.start()
        t2.join()
    elif last_message[message.chat.id] == "Пополнить баланс":
        try:
            amount = str(int(message.text.strip()))
            comment[message.chat.id] = comment_generate(amount, message.chat.id)
            link = "https://qiwi.com/payment/form/99?amountInteger=" + amount + \
                   "&amountFraction=0&currency=643&extra[%27comment%27]=" + \
                   comment[message.chat.id] + "&extra[%27account%27]=" + \
                   phone + "&blocked[0]=comment&blocked[1]=account&blocked[2]=sum "
            bot.send_message(message.chat.id, link, reply_markup=markup2)
        except ValueError:
            bot.send_message(message.chat.id, "Введена не корректная сумма попробуйте еще раз.")
            bot.send_message(message.chat.id, "Введите сумму пополнения баланса", reply_markup=markup1)
    else:
        bot.send_message(message.chat.id, "Для навигации используйте кнопки, для обращения в тех поддрержку пишите "
                                          "сюда: @tp", reply_markup=markup)


def randomik():
    f = open("beats.txt", 'r')
    a = []
    for line in f:
        a.append(line)
    return random.choice(a)


def balance(login):
    connection = pg.connect(database='users', user='code', password='coder', host="127.0.0.1", port="5432")
    cursor = connection.cursor()
    cursor.execute("SELECT amount FROM users_list WHERE login = '" + str(login) + "';")
    am = cursor.fetchall()
    connection.commit()
    connection.close()
    print(am[0][0])
    return am[0][0]


def checker(mes, com):
    i = 0
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + api_access_token
    parameters = {'rows': 10}
    while i < 11:
        h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + my_login + '/payments', params=parameters)
        for l in h.json()["data"]:
            if (str(l['status']) == "SUCCESS") & (str(l['comment']) == str(com)):
                if str(l['sum']['amount']) == str(payments[com]):
                    bot.send_message(mes.chat.id, "Платеж получен , спасибо")
                    change_balance(mes.chat.id, payments[com])
                    return
        sleep(2)
        i += 1
    bot.send_message(mes.chat.id, "Кажется мы не получили ваш платеж")


def comment_generate(am, ids):
    comment_txt = str(time.time()) + "_" + str(ids)
    payments[comment_txt] = am
    return comment_txt


def change_balance(ids, am):
    connection = pg.connect(database='users', user='code', password='coder', host="127.0.0.1", port="5432")
    cursor = connection.cursor()
    am = int(am) + balance(ids)
    cursor.execute("UPDATE users_list SET amount = " + str(am) + "WHERE login ='" + str(ids) + "';")
    connection.commit()
    connection.close()


bot.polling()
