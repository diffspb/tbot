# -*- coding: utf-8 -*-
import config
import telebot
import time
import re
import datetime
import threading
from telebot import types

bot = telebot.TeleBot(config.bottoken)

def get_username(message):
    #print vars(message.from_user)
    if message.from_user.username is not None:
        return message.from_user.username
    elif (message.from_user.first_name is not None) and (message.from_user.last_name is not None):
        return message.from_user.first_name + " " + message.from_user.last_name
    elif (message.from_user.first_name is not None) and (message.from_user.last_name is None):
        return message.from_user.first_name
    else:
        return str(message.from_user.id)

def show_main_menu(message):
    #markup = types.ReplyKeyboardMarkup()
    #markup.row('Get EMU', 'Release EMU')
    #markup.row('List all EMUs')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="test1", callback_data="callback_data1"))
    markup.add(types.InlineKeyboardButton(text="test2", callback_data="callback_data2"))
    bot.send_message(message.from_user.id, "Choose:", reply_markup=markup)
    pass

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(message):
    print(message.data)
    pass

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.from_user.id, "Hello, " + get_username(message))
    show_main_menu(message)
    pass

@bot.message_handler(commands=['test'])
def handle_add_emu(message):
    bot.send_message(message.chat.id, "Not implemented yet!")
    pass

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе
    #bot.send_message(message.from_user.id, message.text + ' ' + get_username(message))
    if len(message.text) > 0:
        command = message.text.split(' ', 1)[0]
        if command == "Get":
            #set_user_action(message.from_user.id, "list")
            #bot.send_message(message.from_user.id, "Choose:")
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.from_user.id, "E:", reply_markup=markup)
            pass
        else:
            show_main_menu(message)

#if __name__ == '__main__':
#add_emu("xz", "192.168.3.80", "192.168.3.180", "---");
bot.polling(none_stop=True)



