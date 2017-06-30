# -*- coding: utf-8 -*-
import config
import telebot
import sqlite3
import time
import re
import datetime
import threading
from telebot import types

cursor = 0
conn = 0
users_actions = dict()
lock = threading.Lock()
#old_time = 3600*24
old_time = 15

def set_user_action(user, action):
    users_actions[user] = action

def get_user_action(user):
    return users_actions.get(user, "")

def create_tables():
    global cursor
    lock.acquire()
    cursor.execute("CREATE TABLE emus(emu_id INTEGER PRIMARY KEY AUTOINCREMENT, emu_name CHAR(255) default '', emu_ip CHAR(255) default '0.0.0.0', emu_arch CHAR(255) default 'x68', emu_play_ip CHAR(255) default '', owner_id INTEGER default -1, owner_name CHAR(255) default '', last_change_date INTEGER default 0);");
    lock.release()
    pass

def open_db():
    global conn
    global cursor
    conn = sqlite3.connect('emus.sqlite', check_same_thread=False)
    cursor = conn.cursor()
    lock.acquire()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emus';")
    res = cursor.fetchall()
    lock.release()
    if (len(res) == 0):
        create_tables()
    lock.acquire()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emus';")
    res = cursor.fetchall()
    lock.release()
    print res
    pass

# full:
#  0 - only free and old
#  1 - all 
#  2 - all with description
#  3 - only my

def get_emu_list(full, myid):
    global cursor
    lock.acquire()
    if full == 0:
        cursor.execute("SELECT * from emus WHERE owner_id = -1 OR last_change_date < ? OR owner_id = ? ORDER BY emu_ip;", (int(time.time() - old_time), int(myid)))
    elif full == 3:
        cursor.execute("SELECT * from emus WHERE owner_id = ? ORDER BY emu_ip", (int(myid),))
    else: # 1,2 and other
        cursor.execute("SELECT * from emus ORDER BY emu_ip")
    res = cursor.fetchall()
    lock.release()
    return res

def set_emu_owner(oid, oname, eid):
    global cursor
    lock.acquire()
    cursor.execute("UPDATE emus SET owner_id=?, owner_name=?, last_change_date=? WHERE emu_id=?;", (int(oid), str(oname), int(time.time()), int(eid)))
    conn.commit()
    lock.release()
    pass

def get_emu_owner(eid):
    global cursor
    lock.acquire()
    cursor.execute("SELECT owner_id FROM emus WHERE emu_id=?;", (int(eid),))
    res = cursor.fetchall()
    lock.release()
    if len(res) > 0:
        row = res[0]
        return row[0]
    return -1

def get_emu_age(eid):
    global cursor
    lock.acquire()
    cursor.execute("SELECT last_change_date FROM emus WHERE emu_id=?;", (int(eid),))
    res = cursor.fetchall()
    lock.release()
    if len(res) > 0:
        row = res[0]
        return int((int(time.time()) - int(row[0])))
    return -1

def free_emu(eid):
    global cursor
    lock.acquire()
    cursor.execute("UPDATE emus SET owner_id=-1, owner_name='' WHERE emu_id=?;", (int(eid),))
    conn.commit()
    lock.release()
    pass

def add_emu(ename, eip, eplayip, earch):
    global cursor
    lock.acquire()
    cursor.execute("INSERT INTO emus(emu_name, emu_ip, emu_play_ip, emu_arch) VALUES(?,?,?,?);", (str(ename), str(eip), str(eplayip), str(earch)))
    conn.commit()
    lock.release()
    pass


def delete_emu(eid):
    global cursor
    lock.acquire()
    cursor.execute("DELETE FROM emus WHERE emu_id=?;", (int(eid),))
    conn.commit()
    lock.release()
    pass

bot = telebot.TeleBot(config.bottoken)

def is_admin(message):
    return 0

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
    markup = types.ReplyKeyboardMarkup()
    markup.row('Get EMU', 'Release EMU')
    markup.row('List all EMUs')
    if is_admin(message):
        markup.row('Add new EMU', 'Delete existing EMU')
    set_user_action(message.from_user.id, "")
    bot.send_message(message.from_user.id, "Choose:", reply_markup=markup)
    pass

# full:
#  0 - only free and old
#  1 - all 
#  2 - all with description
#  3 - only my

def show_emu_list(message, full):
    res = get_emu_list(full, int(message.from_user.id))
    markup = types.ReplyKeyboardMarkup()
    for row in res:
        own = ""
        if row[5] != -1:
            own = " Owner : " + str(row[6]) + " " + str(datetime.datetime.fromtimestamp(int(row[7])).strftime('%d-%m-%Y %H:%M:%S'))
        markup.row('/'+str(row[0]) + ' ' + 'EMU: ' + str(row[2]) + own)
    markup.row("Back")
    bot.send_message(message.from_user.id, "Main menu:", reply_markup=markup)
    pass

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.from_user.id, "Hello, " + get_username(message))
    show_main_menu(message)
    pass

@bot.message_handler(regexp="\d+")
def handle_list_select(message):
    m = re.search('(\d+) (.*)', message.text)
    lid = int(m.groups()[0])
    if get_user_action(message.from_user.id) == "get":
        oid = get_emu_owner(lid)
        age = get_emu_age(lid)
        if (oid != -1) and (oid != message.from_user.id) and (age < old_time):
            bot.send_message(message.from_user.id, "Emu busy!")
        else:
            set_emu_owner(message.from_user.id, get_username(message), lid);
            new_oid = get_emu_owner(lid)
            if new_oid == message.from_user.id:
                bot.send_message(message.chat.id, str(m.groups()[1]) + " taken by " + get_username(message))
                if (oid != -1) and (oid != message.from_user.id):
                    bot.send_message(oid, "You lost " + str(m.groups()[1]) + "!")
            else:
                bot.send_message(message.from_user.id, "Emu busy!")
            show_main_menu(message)
    elif get_user_action(message.from_user.id) == "release":
        oid = get_emu_owner(lid)
        if (oid == -1):
            bot.send_message(message.from_user.id, "Emu already free!")
        elif (oid != message.from_user.id):
            bot.send_message(message.from_user.id, "Emu busy!")
        else:
            free_emu(lid);
            bot.send_message(message.chat.id, str(m.groups()[1]) + " relesed.")
            show_main_menu(message)
    else:
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
            set_user_action(message.from_user.id, "get")
            show_emu_list(message, 0)
        elif command == "Release":
            set_user_action(message.from_user.id, "release")
            show_emu_list(message, 3)
        elif command == "List":
            set_user_action(message.from_user.id, "list")
            show_emu_list(message, 1)
        elif command == "Add":
            bot.send_message(message.from_user.id, "Not implemented yet!")
        elif command == "Delete":
            bot.send_message(message.from_user.id, "Not implemented yet!")
        else:
            show_main_menu(message)

#if __name__ == '__main__':
open_db()
#add_emu("xz", "192.168.3.80", "192.168.3.180", "---");
bot.polling(none_stop=True)



