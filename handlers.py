""" Функционал хэндлеров бота"""
import logging
import os
from datetime import datetime
from glob import glob
from random import choice

from emoji import emojize
from telegram.ext import messagequeue as mq

import settings
from utils import image_analyze, get_keyboard, communication
from db import db, get_or_create_user, toggle_subscription, all_subscription


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()

file_handler = logging.FileHandler('tg_bot.log', encoding='utf-8')
log.addHandler(file_handler)  # Привязка к созданному логеру 'Log'


def greet_user(bot, update, user_data):
    """ Функция старта. Активируется при команде /start. Создает в БД: db.users профайл юзера. Отправляет сообщение
     с функционалом бота."""
    user = get_or_create_user(db, update.effective_user, update.message)
    # user_data = {}
    log.info(f'вызвана  функция  - greet_user с параметрами: {bot}, {update}')
    name_user = update.effective_user.first_name
    log.info(f'подключился пользователь {update.effective_user.username}:'
             f' {update.effective_user.first_name, update.effective_user.last_name}')
    # avatar_user = utils.get_user_avatar(user_data)  - если прикручивать индивидуальный смайлик
    update.message.reply_text(reply_markup=get_keyboard(),
                              text=f'Приветствую вас, {name_user}! {emojize(settings.NAME_EMOJI["нимб"])}\n'
                                   f"Я могу сделать описание фотографии, если вы мне её отправите")

def get_contact(bot, update, user_data):
    """ Считывает отправленный пользователем контакт и заносит номер телефона в профайл пользователя в db.users"""
    user = get_or_create_user(db, update.effective_user, update.message)
    user_contact = update.message.contact
    db.users.update_one(
        {'_id': user['_id']},
        {'$set': {'phone': user_contact['phone_number']}}
    )
    # user_data['contact']=user_contact
    log.info(f'пользователь {update.message.chat.username} отправил свой контакт {update.message.contact}')


def get_location(bot, update, user_data):
    """ Считывает отправленную пользователем локацию и заносит в профайл пользователя в db.users"""
    user = get_or_create_user(db, update.effective_user, update.message)
    user_location = update.message.location
    db.users.update_one(
        {'_id': user['_id']},
        {'$set': {'location': str(user_location)}}
    )
    # user_data['location']=user_location
    log.info(f'пользователь {update.message.chat.username} отправил свою локацию {update.message.location}')


def talk_to_me(bot, update, user_data):
    """ Получает текст и запускает функцию общения """
    user = get_or_create_user(db, update.effective_user, update.message)
    # avatar_user = utils.get_user_avatar(user_data)  - если прикручивать индивидуальный смайлик
    log.info(f'Получено: {update.message.chat.username} - {update.message.chat.id} - {update.message.text}')
    communication(bot, update, user_data, user) # логика общения



def send_pic(bot, update, user_data):
    """ Отправляет рандомное изображение из указанной папки в переменной images_list"""
    user = get_or_create_user(db, update.effective_user, update.message)
    log.info(f'{update.message.chat.username} вызвал функцию /pic')
    images_list = glob('images/themes/*.jp*g')
    if images_list:
        some_img = choice(images_list)
        bot.send_photo(chat_id=update.message.chat.id, photo=open(some_img, 'rb'), reply_markup=get_keyboard(),)
        log.info(f'отправленно изображение : {some_img}')
    else:
        update.message.reply_text('Изображения пока подготовлены')


def check_user_photo(bot, update, user_data):
    """ Сохраняет полученное от пользователя фото в папку downloads. Запускает логику анализа фото """
    user = get_or_create_user(db, update.effective_user, update.message)
    update.message.reply_text('обрабатываю фото. В первый раз может занять пару минут')
    # блок загрузки и сохранения изображения
    os.makedirs('downloads', exist_ok=True)
    photo_file = bot.getFile(update.message.photo[-1].file_id)
    filename = os.path.join('downloads', '{}.jpg'.format(datetime.now().strftime('%d_%m_%y_%H_%M')))   # (photo_file.file_id
    photo_file.download(filename)
    log.info(f'получено изображение от {update.effective_user.username}, - {filename}')

    image_analyze(filename, update, user_data, user) # запуск логики ответов пользователю при распозновании изображений



def subscribe(bot, update):
    """ Оформляет подписку пользователя. Ставит True в параметре subscription у профайла пользователя в db.users """
    user = get_or_create_user(db, update.effective_user, update.message)
    if user['subscription'] is False:
        toggle_subscription(db, user)
        update.message.reply_text('Вы подписались')
    else:
        update.message.reply_text('Вы уже подписаны. Для отписки введите /unsubscribe')

def unsubscribe(bot, update):
    """ Отписывает пользователя. Ставит False в параметре subscription у профайла пользователя в db.users """
    user = get_or_create_user(db, update.effective_user, update.message)
    if user['subscription'] is True:
        toggle_subscription(db, user)
        update.message.reply_text('Вы отписались')
    else:
        update.message.reply_text('Вы не были подписаны. Для подписки введите /subscribe')

@mq.queuedmessage # очередь, с лимитами от телеграм
def send_updates(bot, job):
    """ Отправляет всем пользователям с подпиской сообщение. Тайминги выставляются в tg_bot.main.subscription"""
    for user in all_subscription(db):
        bot.sendMessage(chat_id=user['chat_id'], text=f'Cпамчик {emojize(settings.NAME_EMOJI["сердце"])}')



def set_alfrm(bot, update, args, job_queue):    # отложенная задача, задаваемая пользователем
    try:
        seconds = abs(int(args[0]))
        job_queue.run_once(alarm, seconds, context=update.message.chat_id)
    except (IndexError, ValueError):
        update.message.reply_text('Введите число секунд после команды /alarm')

@mq.queuedmessage
def alarm(bot, job):         # действие, для отложенной задачи пользователя
    bot.send_message(chat_id=job.context, text='Сработал будильнмк')