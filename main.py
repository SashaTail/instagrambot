#/usr/bin/env python   
from instagrapi import Client
from datetime import datetime, date, time
import time
from requests.sessions import session
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from crontab import CronTab
import json
import requests
import os
import sys
import random
from PIL import Image
import mysql.connector
########################### DATABASE #######################################
db = mysql.connector.connect(
    host="localhost",
    user="username", ###EDIT
    passwd="password", ###EDIT
    port="3306",
    database="Instagram"

    )



cursor = db.cursor()
#cursor.execute("CREATE DATABASE Instagram")
#cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT UNIQUE, username VARCHAR(255), password VARCHAR(255), sessionID VARCHAR(255), user_group INT)")

token = 'yourtoken'  # bot constants EDIT
bot = telebot.TeleBot(token)


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            print("––––––––––––––––––––––––––––––––––––––––––––––––––––––")
            print(f'{m.chat.first_name}[{m.chat.id}][{datetime.now().strftime("%d-%m-%Y_%H-%M")}]: {m.text}')
            with open('logs.txt', 'a', encoding='utf-8') as logs_file:
                logs_file.write("––––––––––––––––––––––––––––––––––––––––––––––––––––––\n")
                logs_file.write(
                    f'{m.chat.first_name}[{m.chat.id}][{datetime.now().strftime("%d-%m-%Y_%H-%M")}]: {m.text}\n')


bot.set_update_listener(listener)



########################### MENU #######################################
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard2 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('Опубликовать фото')
keyboard1.row('Авторизация', 'Выход')
keyboard2.row('Добавить фото', 'Добавить описание', 'Установить время публикации')
keyboard2.row('Отправить', 'Назад')

########################### END #######################################



@bot.message_handler(commands=['start']) #Отправка стартового сообщения
def send_welcome(message):
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.from_user.id,f'Я бот. Приятно познакомиться, {message.from_user.first_name}\nВыбери действие: ', reply_markup=keyboard1)
    #sql= "INSERT INTO users (user_id) VALUES(%s)"
    #cursor.execute(sql,(message.chat.id,))
    #db.commit()
    sql = "SELECT * from users WHERE user_id=%s"
    cursor.execute(sql,(message.chat.id,))
    users = cursor.fetchone()
    print(users)
    if users is None:
        sql= "INSERT INTO users (user_id) VALUES(%s)"
        cursor.execute(sql,(message.chat.id,))
        db.commit()


@bot.message_handler(commands=['see']) # Просмотр постов на публикацию
def see(message):
    try:
        sql= "SELECT * FROM posts where user_id=%s"
        cursor.execute(sql,(message.chat.id,))
        info= cursor.fetchall()

        for elem in info:
            if elem[4] is not None:
                photo=open(elem[4], 'rb')
                if elem[3] is not None:
                    strk=f'ID: {elem[0]} \nВремя публикации :  {elem[3].day}/{elem[3].month}  {elem[3].hour}:{elem[3].minute}'
                    if elem[5] is not None:
                        bot.send_photo(message.chat.id,photo, strk + "\nОписание : " +str(elem[5]),reply_markup=delete_user_post() )
                    else:
                        bot.send_photo(message.chat.id,photo, strk + "\nОписание : Отсутствует " ,reply_markup=delete_user_post() )  
    except Exception as TypeError:
        print("У поста нет данных")

def delete_user_post(): # Удаление
    markup = InlineKeyboardMarkup()
    delete_post = InlineKeyboardButton('Удалить', callback_data='delete_post')
    edit_post = InlineKeyboardButton('Изменить', callback_data='edit_post')
    markup.add(delete_post,edit_post)
    return markup

def edit_user_post(): # Редактирование поста
    markup = InlineKeyboardMarkup()
    edit_time = InlineKeyboardButton('Изменить время', callback_data='edit_time')
    edit_desc = InlineKeyboardButton('Изменить описание', callback_data='edit_desc')
    edit_photo = InlineKeyboardButton('Изменить фотографию', callback_data='edit_photo')
    markup.add(edit_time,edit_desc, edit_photo)
    return markup


########################### ROUTES #######################################

@bot.message_handler(content_types=['text']) 
def mainfunc(message):
    if message.text.lower() == 'опубликовать фото':
        post(message)
    elif message.text.lower() == 'авторизация':
        bot.send_message(message.chat.id, "Введите логин")
        bot.register_next_step_handler(message,get_login_for_settings)
    elif message.text.lower() == 'назад':
        send_welcome(message)
    elif message.text.lower()== 'добавить фото':
        bot.send_message(message.chat.id, "Ваша фотография должна:\n •Размер изображения в Instagram — 600 x 750 (минимальное разрешение)\n •Быть с разрешением стороном минимум 4:5 либо же квадратным")
        bot.register_next_step_handler(message,handle_docs_document)
    elif message.text.lower() == 'добавить описание':
        bot.register_next_step_handler(message,desc)
    elif message.text.lower() == "установить время публикации":
        bot.send_message(message.chat.id, "Пример: 20/12/2021 12:00")
        bot.register_next_step_handler(message,get_time)
    elif message.text.lower() == "отправить":
        posting(message)
    else:
        bot.send_message(message.chat.id, 'Error');
########################### END #######################################


########################### Authorization #######################################

# Авторизация происходит на стороне instagram, в ответ нам прилетает sessiontoken, мы его парсим и сохраняем в бд, после мы его используем везде. Сохранение логина и пароля не обязательно,
# сделано в целях актуализации токена
def get_login_for_settings(message):
    bot.send_message(message.chat.id, "Введите пароль")
    sql="UPDATE users SET username = %s WHERE user_id = %s "
    #sql="INSERT INTO users (user_id, username) VALUES  (%s, %s)  ON DUPLICATE KEY UPDATE username  = VALUES(username) "
    val=(message.text,message.chat.id)
    bot.register_next_step_handler(message, get_password_for_settings)
    cursor.execute(sql, val)
    db.commit()


def get_password_for_settings(message):
    sql="UPDATE users SET password = %s WHERE user_id = %s "
    #sql="INSERT INTO users (user_id, password) VALUES  (%s, %s)  ON DUPLICATE KEY UPDATE password  = VALUES(password)"
    val=(message.text,message.chat.id)
    cursor.execute(sql, val)
    db.commit()
    get_auth(message)
    

def get_auth(message):
    try:
        sql="SELECT username, password FROM users WHERE user_id = %s LIMIT 1"
        val=message.chat.id
        cursor.execute(sql,(message.chat.id,))
        auth= cursor.fetchone()
        cl = Client()
        cl.login(auth[0], auth[1])
        session = cl.cookie_dict
        bot.send_message(message.chat.id, "Вы успешно авторизировались")
        sql="UPDATE users SET sessionID = %s WHERE user_id = %s "
        #sql="INSERT INTO users (user_id,auth) VALUES  (%s,%s)  ON DUPLICATE KEY UPDATE auth  = VALUES(auth)"
        
        val=(session["sessionid"],message.chat.id) # получение токена, сохранения в бд
        cursor.execute(sql, val)
        db.commit()
    except Exception as BadPassword:
        bot.send_message(message.chat.id, "Логин или пароль неверный",reply_markup=keyboard1)
        
        sql="UPDATE users SET username=%s, password=%s , sessionID = %s  WHERE user_id = %s "
        val=(None,None,None,message.chat.id)
        cursor.execute(sql, val)
        db.commit()

########################### END #######################################

########################### POSTING #######################################

def templateID(message):
    sql= "SELECT id FROM posts where user_id=%s ORDER BY id DESC limit 1"
    cursor.execute(sql,(message.chat.id,))
    tmpID= cursor.fetchone()
    return tmpID

@bot.message_handler(commands=['post'])
def post(message):
    sql="SELECT sessionID FROM users WHERE user_id = %s LIMIT 1"
    val=message.chat.id
    cursor.execute(sql,(message.chat.id,))
    sessionId= cursor.fetchone() # выгружаем токен из БД по id пользователя, который всегда доступен в telegram. 
    print(sessionId)
    if sessionId[0] is None:
        bot.send_message(message.chat.id, f'Вы не авторизированы', reply_markup=keyboard1)
        return 0
    sql= "INSERT INTO posts (user_id,sessionID) VALUES(%s,%s)"
    cursor.execute(sql,(message.chat.id,sessionId[0],))
    db.commit()
    sql= "SELECT id FROM posts WHERE user_id=%s "
    cursor.execute(sql,(message.chat.id,))
    tmpID= cursor.fetchall()
    
   # user_post={'id': int(tmpID[0]), 'user_id' : message.chat.id, 'sessionID' : sessionId[0], 'timetopost' : None, 'path' : None, 'description' : None, 'exec' : None}
    bot.send_message(message.from_user.id, f'Выбери действие: ', reply_markup=keyboard2)



def handle_docs_document(message): # Загрузка фотографии, на сервер прилетает фотография, мы ее сохраняем, её название и путь мы записываем в posts в path - оттуда будем позже парсить для публикации. 
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    tmpID= templateID(message)
    photo=str(int(tmpID[0]))+'.jpg'
    downloaded_file = bot.download_file(file_info.file_path)
    with open(photo, 'wb') as new_file:
            new_file.write( downloaded_file)
    im = Image.open(photo)
    ratio = im.width  / im.height 
    print(im.width)
    print(im.height)
    print(ratio)
    if (ratio>0.8 and im.width > 600 and im.height > 750):
        sql="UPDATE posts SET path = %s WHERE id = %s "
        val=(photo, int(tmpID[0]) )
        cursor.execute(sql, val)
        db.commit()
        bot.reply_to(message, f'Фото добавлено', reply_markup=keyboard2)

    else:
        bot.send_message(message.chat.id, f'Фотография не соответствует требованиям', reply_markup=keyboard2)

def desc(message):
    user_desc= message.text
    print(user_desc)
    tmpID= templateID(message)
    sql="UPDATE posts SET description = %s WHERE id = %s "
    val=(user_desc, int(tmpID[0]) )
    cursor.execute(sql, val)
    db.commit()
    bot.send_message(message.chat.id, f'Описание добавлено', reply_markup=keyboard2)
    
def get_time(message):
    try:
        import re
        user_time= message.text
        if (all([c.isdigit() or c == '/' or c== ':' or c== ' ' for c in user_time])== True):

            date = re.split('; | |:|/|\n', user_time)
            user_datedb=date[2]+'-'+date[1]+'-'+date[0]+' '+date[3]+':'+ date[4]
            tmpID= templateID(message)
            sql="UPDATE posts SET timetopost = %s WHERE id = %s "
            val=(user_datedb, int(tmpID[0]))
            cursor.execute(sql, val)
            db.commit()
            bot.send_message(message.chat.id, f'Время установлено', reply_markup=keyboard2)
        else: 
            bot.send_message(message.chat.id, f'Введите в формате указанном выше', reply_markup=keyboard2) 
    except Exception as IndexError:
        bot.send_message(message.chat.id, f'Не указано время/дата', reply_markup=keyboard2) 


def posting(message):
    try:
        tmpID= templateID(message)
        sql= "SELECT timetopost, path FROM posts WHERE id=%s"
        cursor.execute(sql,(int(tmpID[0]),))
        time_to_post= cursor.fetchone()
        cron_request='/home/aleksandr/instagrambot/bin/python /home/aleksandr/instagrambot/photo_post.py' + ' ' +  str(int(tmpID[0]))
        cron = CronTab('aleksandr') 
    
        #job = cron.new(command='echo Hi >> /home/aleksandr/OUT ')
        job = cron.new(command=cron_request)
        job.minute.on(time_to_post[0].minute)
        job.hour.on(time_to_post[0].hour)
        job.day.on(time_to_post[0].day)
        job.month.on(time_to_post[0].month)
        sql = "UPDATE posts SET exec=%s where id=%s"
        val= (cron_request, int(tmpID[0]))
        cursor.execute(sql, val)
        db.commit()
        cron.write() # Крон служит для записи на отложенное время, доступно только на Linux. В целях экономии памяти сервера и разгрузки процессора. 
        bot.send_message(message.chat.id, f'Пост будет опубликован', reply_markup=keyboard1)
    except Exception as AttributeError:
        bot.send_message(message.chat.id, f'Вы не указали время', reply_markup=keyboard2) 

########################### END #######################################
    


@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'contact'])
def error(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        pass
    print(type(message.chat.id))
    bot.send_message(message.chat.id, 'Воспользуйтесь предложенными кнопками. '
                                      'Если кнопки исчезли, введите команду /start')


########################### EDIT POST BLOCK #######################################
def edit_time(message,result):
    try:
        import re
        user_time= message.text
        print(user_time)
        if (all([c.isdigit() or c == '/' or c== ':' or c== ' ' for c in user_time])== True):
            date = re.split('; | |:|/|\n', user_time)
            user_datedb=date[2]+'-'+date[1]+'-'+date[0]+' '+date[3]+':'+ date[4]
            sql="UPDATE posts SET timetopost = %s WHERE id = %s "
            val=(user_datedb, result)
            cursor.execute(sql, val)
            db.commit() ####### НИЖЕ УДАЛЕНИЕ СТАРОГО КРОНА ######
            sql="SELECT exec,timetopost from posts where id=%s LIMIT 1"
            cursor.execute(sql,(result,))
            cronre = cursor.fetchone()
            cron = CronTab('aleksandr') 
            cron.remove_all(command = str(cronre[0]))
            cron.write()

            ######## НИЖЕ ЗАПИСЬ НОВОГО КРОНА ######
            job = cron.new(command=str(cronre[0]))
            job.minute.on(cronre[1].minute)
            job.hour.on(cronre[1].hour)
            job.day.on(cronre[1].day)
            job.month.on(cronre[1].month)

            cron.write()

            bot.send_message(message.chat.id, f'Время установлено')

        else: 
            bot.send_message(message.chat.id, f'Введите в формате указанном выше') 
    except Exception as IndexError:
        bot.send_message(message.chat.id, f'Не указано время/дата') 

def edit_desc(message, result):
    user_desc= message.text
    print(user_desc)
    tmpID= templateID(message)
    sql="UPDATE posts SET description = %s WHERE id = %s "
    val=(user_desc, result)
    cursor.execute(sql, val)
    db.commit()
    bot.send_message(message.chat.id, f'Описание добавлено')

def edit_photo(message,result):
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    photo=str(result)+'.jpg'
    downloaded_file = bot.download_file(file_info.file_path)
    with open(photo, 'wb') as new_file:
            new_file.write( downloaded_file)
    im = Image.open(photo)
    ratio = im.width  / im.height 
    print(im.width)
    print(im.height)
    print(ratio)
    if (ratio>0.8 and im.width > 600 and im.height > 750):
        bot.reply_to(message, f'Фото добавлено')

    else:
        bot.send_message(message.chat.id, f'Фотография не соответствует требованиям')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        global cmcd, cmmi
        cmcd = call.message.chat.id
        cmmi = call.message.message_id
        print(call.message.chat.id, call.data)
        import re
        result=[]
        if (result == []):
            result = re.findall(r"id:\.?([ \d.]+)", call.message.caption, re.IGNORECASE | re.MULTILINE)
        print(call.message.caption)
        print(result)
        if call.data == 'delete_post':
            bot.edit_message_caption('Пост удален:', call.message.chat.id, call.message.message_id)
            import re
            result = re.findall(r"id:\.?([ \d.]+)", call.message.caption, re.IGNORECASE | re.MULTILINE)
            #sql= "DELETE FROM posts WHERE id = %s"
            #cursor.execute(sql,(int(result[0]),))
            #db.commit()

            sql="SELECT exec from posts where id=%s LIMIT 1"
            cursor.execute(sql,(int(result[0]),))
            cronre = cursor.fetchone()
            cron = CronTab('aleksandr') 

            cron.remove_all(command = str(cronre[0]))
            cron.write()
        if call.data == "edit_post":
            bot.edit_message_caption(call.message.caption + "\n Выберите действие", call.message.chat.id, call.message.message_id, reply_markup= edit_user_post())
        if call.data == "edit_time":
            bot.send_message(call.message.chat.id,"Пример: 20/12/2021 12:00")
            bot.register_next_step_handler(call.message,edit_time,result[0])
        if call.data == "edit_desc":
            bot.send_message(call.message.chat.id,"Введите текст")
            bot.register_next_step_handler(call.message,edit_desc,result[0])
        if call.data == "edit_photo":
            bot.send_message(call.message.chat.id,"Ваша фотография должна:\n •Размер изображения в Instagram — 600 x 750 (минимальное разрешение)\n •Быть с разрешением стороном минимум 4:5 либо же квадратным")
            bot.register_next_step_handler(call.message,edit_photo,result[0])

            print("")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(e)
        pass
########################### END #######################################

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
            #Bot()
            
        except Exception as e:
            print(f'i sleep   {e}')
            time.sleep(5)