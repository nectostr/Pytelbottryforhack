# -*- coding: utf-8 -*-
import config
import telebot
import psycopg2
import pandas as pd
import requests as re
import json


bot = telebot.TeleBot(config.token)

# @bot.message_handler(content_types=["text"])
# def answer_on_message(message):
#     bot.send_message(message.chat.id, message.text[::-1])


str_C = ''
conver_level = 0
curr_course = None
ch_id = None
base_url = 'http://192.168.88.251:8081/rest/vmapi/'
my_courses = {}
my_skills = {}
# пара (имя,идишник)
curr_courses = [None,None]
missingKeywords = []
vacansies = []

def ask_course(message):
    s = "Начните вводить название курса.\nДвух-трех букв должно быть достаточно"
    bot.send_message(message.chat.id, s)
    global conver_level
    conver_level = 1

@bot.message_handler(commands=['help'])
def com_hand4(message):
    global ch_id
    ch_id = message.chat.id
    s = "Welcome to our app stranger!\n"
    s+= "First what should you do - add courses, wich you have been passed and add or edit skills wich you get from that courses. Then we will give you skills wich you need for some jobs and where you can get it\n"
    s+= "Also you can control program by sending\n"
    s+= "/help - to reread this guide\n"
    s+= "/reset - to reset session of app\n"
    s+= "/mycourses - to know wich courses you've been alvready add\n"
    s+= "/myskills - to know about wich of your skills we've been alvready known;\n"
    s+= "/recommend - to get prepared result"
    bot.send_message(message.chat.id, s)



@bot.message_handler(commands=['reset'])
def com_hand3(message):
    global conver_level,my_courses, ch_id
    ch_id = message.chat.id
    my_courses = {}

    s = 'Ресет выполнен\n'
    s += 'Начните вводить название курса.\nДвух-трех букв должно быть достаточно'
    markdown = s
    bot.send_message(message.chat.id, markdown,parse_mode="Markdown")
    conver_level = 1

@bot.message_handler(commands=['recommend'])
def com_hand2(message):
    try:
        global base_url, my_skills, missingKeywords, vacansies
        if my_skills != []:
            print(json.dumps(list(my_skills.keys())))
            r = re.post(base_url+'recommend',data = json.dumps(list(my_skills.keys())),headers= {'content-type': 'application/json'})
            print(r.text)
            r = r.json()
        # print(type(r))

        for i in range(len(r)):
            missingKeywords.append(r[i]['missingKeywords'])
            vacansies.append(r[i]['vacanciesExample'])

        # print(missingKeywords)
        global conver_level, ch_id
        ch_id = message.chat.id
        keyboard = telebot.types.InlineKeyboardMarkup()
        s = 'Пожалуйста, подождите пару секунд, выполняются вычисления...'
        bot.send_message(message.chat.id, s)
        for i in range(len(missingKeywords)):
            callback_button = telebot.types.InlineKeyboardButton(
                text=str('Направление '+str(i)),
                callback_data=('vacansНаправление'+str(i)))
            keyboard.add(callback_button)
        s = 'Мы подобрали для вас несколько основных направлений развития:'
        bot.send_message(message.chat.id, s, reply_markup=keyboard)
        # bot.send_message(message.chat.id, r.json())
        conver_level = 10
    except:
        s = 'Непредвиденная ошибка. Пожалуйста, начните заново'
        bot.send_message(message.chat.id, s)
        conver_level = 1

@bot.message_handler(commands=['myskills'])
def com_hand11(message):
    global conver_level, ch_id, my_skills
    ch_id = message.chat.id
    s = ''
    if len(my_skills) != 0:
        for i in my_skills.keys():
            s += i + '; '
        bot.send_message(message.chat.id, s)
    else:
        s = "Я еще не знаю ваших навыков"
        bot.send_message(message.chat.id, s)

@bot.message_handler(commands=['mycourses'])
def com_hand1(message):
    global conver_level, ch_id
    ch_id = message.chat.id
    s = ''
    if len(my_courses) != 0:
        for i in my_courses.values():
            s += i + '; '
        bot.send_message(message.chat.id, s)
    else:
        s = 'Я еще пока не знаю пройденных вами курсов'
        bot.send_message(message.chat.id, s)
    conver_level = 0

@bot.message_handler(func=lambda message: True, content_types=['text'])
def solve_text(message):
    global conver_level, ch_id
    ch_id = message.chat.id
    if conver_level == 0:
        ask_course(message)
        return
    elif conver_level == 1:
        add_course(message)
        return
    elif conver_level == 6:
        if message.text != 'stop':
            my_skills[message.text] = ""
            add_tag(message)
        else:
            bot.send_message(message.chat.id, 'Еще курс?')
            conver_level = 1
        return

def add_tag(message):
    print('добавляем ' + message.text)
    s = 'Скилл ' + message.text + ' добавлен. Что бы закончить напишите stop, или введите еще название полученного скилла'
    bot.send_message(message.chat.id, s)

def add_course(message):
    try:
        global str_C,curr_course, conver_level, curr_courses
        str_C = message.text
        conn = psycopg2.connect(
            database=config.database,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT title,course_id,platform FROM db_test.courses_key WHERE title like('"+str_C.lower()+"%')")
        curr_courses = cur.fetchall()
        cur.close()
        conn.close()
        if len(curr_courses) > 0:
            keyboard = telebot.types.InlineKeyboardMarkup()
            # print(len(curr_courses))
            s = ''
            for i in range(len(curr_courses)):
                # s += 'Ваш курс '+ str(curr_cur_name[i][0]) + '?\n'

                callback_button = telebot.types.InlineKeyboardButton(text=str((curr_courses[i][0] +' на платформе '+ curr_courses[i][2])), callback_data=(str(i)))

                keyboard.add(callback_button)
            callback_button = telebot.types.InlineKeyboardButton(text=str('Наберу курс заново'),
                                                                 callback_data=('niht.again'))
            keyboard.add(callback_button)
            bot.send_message(message.chat.id, "Выбирайте!", reply_markup=keyboard)

            conver_level = 1

        else:
            bot.reply_to(message, 'Увы, вашего курса еще нет\nВводим еще!')

            conver_level = 1
    except:
        s = 'Непредвиденная ошибка. Пожалуйста, начните заново'
        bot.send_message(message.chat.id, s)
        conver_level = 1

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        global my_courses,conver_level, curr_courses, my_skills,curr_course
        headers = {'content-type': 'application/json'}
        if curr_course is not None:
            r = re.post(base_url + 'coursetotags', data=json.dumps({'course_id': curr_course[1]}),
                        headers=headers)
            dat = r.json()
        if call.data == 'niht.lazy':
            bot.send_message(ch_id, 'Еще курс?')
            conver_level = 1
        elif call.data == 'ia.notlazy':
            keyboard3 = telebot.types.InlineKeyboardMarkup()
            for i in range(len(dat)):
                callback_button = telebot.types.InlineKeyboardButton(
                        text = str(dat[i]['keyword']),
                        callback_data = ('delete' + dat[i]['keyword']))
                keyboard3.add(callback_button)

            callback_button = telebot.types.InlineKeyboardButton(
                text=str('Добавить навык!'),
                callback_data=('update'))
            keyboard3.add(callback_button)
            callback_button = telebot.types.InlineKeyboardButton(
                text=str('Я передумал'),
                callback_data=('rethin'))
            keyboard3.add(callback_button)
            s = 'Нажмите на лишние скиллы'
            bot.send_message(ch_id, s,reply_markup=keyboard3)
            conver_level = 1
        elif (call.data) == 'rethin':
            s = 'Добавите еще курс'
            bot.send_message(ch_id, s)
            conver_level = 1
        elif (call.data)[:6] == 'delete':
            del my_skills[call.data[6:]]
            print('удаляем ' + call.data[6:])
        elif call.data == 'update':
            s = 'Введите новый тег для этого курса.'
            bot.send_message(ch_id, s)
            conver_level = 6
        elif (call.data)[:6] == 'vacans':
            s = (call.data)[6:-1] + ' ' + (call.data)[-1:] + """\n*Вам нехватает скиллов:*\n"""
            for i in range(len(missingKeywords[int(call.data[-1:])])):
                s += missingKeywords[int(call.data[-1:])][i]['keyword'] \
                     + '- используйте курсы:\n'
                for j in range(len(missingKeywords[int(call.data[-1:])][i]['courses'])):
                    s += missingKeywords[int(call.data[-1:])][i]['courses'][j]['name'] \
                        + ' ищите их в ' + missingKeywords[int(call.data[-1:])][i]['courses'][j]['link'] + '\n'
            s += '_Примеры вакансий этого направления:_ \n'
            for i in range(len(vacansies[int(call.data[-1:])])):
                s += vacansies[int(call.data[-1:])][i]['name'] \
                     + '- по ссылке:' + vacansies[int(call.data[-1:])][i]['link'] +'\n[text](URL)'
            bot.send_message(ch_id,s,parse_mode="Markdown")
        elif call.data != 'niht.again':
            curr_course = (curr_courses[int(call.data)][0], curr_courses[int(call.data)][1])
            my_courses[curr_course[1]] = curr_course[0]
            keyboard2 = telebot.types.InlineKeyboardMarkup()
            callback_button = telebot.types.InlineKeyboardButton(text=str('Нет, все верно'),
                                                                 callback_data=('niht.lazy'))
            keyboard2.add(callback_button)
            callback_button = telebot.types.InlineKeyboardButton(text=str('Да, я добавлю или удалю несколько'),
                                                                 callback_data=('ia.notlazy'))
            keyboard2.add(callback_button)
            s = 'Готово, ' + curr_courses[int(call.data)][0] + ' добавлен! Ваши скилы после этого курса:'
            r = re.post(base_url + 'coursetotags', data=json.dumps({'course_id': curr_course[1]}),
                        headers=headers)
            dat = r.json()
            for i in range(len(dat)):
                s +='\n' + dat[i]['keyword']
                my_skills[dat[i]['keyword']] = ""
            s += '\nРедактировать скиллы?'
            bot.send_message(ch_id,  s,reply_markup=keyboard2)

        else:
            bot.send_message(ch_id, 'Ну набирайте')
            conver_level = 1
    except:
        s = 'Непредвиденная ошибка. Пожалуйста, начните заново'
        bot.send_message(ch_id, s)
        conver_level = 1


if __name__ == '__main__':
     bot.polling(none_stop=True)

# TODO Разобраться с убиранием кнопок или/и запретом на повторное добавление вакансий
# TODO Что там с размерами? почему на половину нет ответов!?!?!7
# TODO  lowerc запросов
