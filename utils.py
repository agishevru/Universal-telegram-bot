""" Дополнительные функции бота"""
import logging
import os
import time
from random import choice

from emoji import emojize
from telegram import ReplyKeyboardMarkup, KeyboardButton

from scenario_handlers import all_handlers
from db import db, form_state_start, form_state_find
import settings
from clarifai.general_image_recognition import image_to_text_translate_rus, image_to_tags, translate_ensglish_to_russian

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()
file_handler = logging.FileHandler('tg_bot.log', encoding='utf-8')
log.addHandler(file_handler)  # Привязка к созданному логеру 'Log'


def get_keyboard():
    """ Клавиатура, привязанная к панели ввода """
    contact_button = KeyboardButton('отправить свой контакт', request_contact=True)
    location_button = KeyboardButton('отправить свою локацию', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([['Оставить отзыв', 'Подписаться', 'Отписаться'],['Получить изображение']], resize_keyboard=True)
    return my_keyboard

def communication(bot, update, user_data, user):
    """ Функция общения. Проверяет сообщение от пользователя на интенты, описанные в модуле settings.INTENTS и возвращает
     прописанные там ответы. Или запускает сценарий если он есть в интенте. """
    user_id = update.effective_user.id
    name_user = update.effective_user.first_name
    text_user = update.message.text

    # проверка на незавершенные стейты пользователя
    user_states = db.form_step.find({'user_id': user_id})
    if user_states:
        for form in user_states:
            if form['step'] != 'finish':
                user_scenario = form['scenario']
                return continue_scenario(db, update, user_scenario)

    # сценарии юзера закрыты, поиск интентов
    for intent in settings.INTENTS:
        if any(token in text_user.lower() for token in intent['tokens']):  # run intent
            if intent['answer']:
                text = intent['answer'].format(name_user=name_user)
                update.message.reply_text(text=text, reply_markup=get_keyboard())   # НАШЛИ ЗАЯВЛЕННЫЙ ИНТЕНТ, отвечаем
                log.info(f'ответ : {text}')
            else:   # если ответ отсутствует, запускается сценарий
                start_scenario(db, update)
            break
    else:
        text = settings.DEFAULT_ANSWER.format(text=text_user, smile=emojize(settings.NAME_EMOJI['глаза спирали']))
        update.message.reply_text(text=text, reply_markup=get_keyboard())
        log.info(text)

def start_scenario(db, update):
    """ Запускается при включении сценария. Работает только с первым и финишным шагом. Остальные пробрасываются через
    фильтр в начале функции общения - 'communication()'. Создает или находит в БД: 'db.form_step' стейт пользователя
    с полученным из сообщения сценарием. Отправляет пользователю ответ из первого шага сценария 'settings.SCENARIOS'.
    Если пользователь на финишном шаге сценария, передает управление в continue_scenario. Которая действует сообразно
    прописанным в сценарии опциям."""
    log.info(f'пользователь {update.effective_user.username} запустил сценарий {update.message.text}')
    user_state = form_state_start(db, update)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_next_step = settings.SCENARIOS[user_scenario]['steps'][user_step]['next_step']
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)
    if user_answer is not False:
        update.message.reply_text(user_answer, reply_markup=user_keyboard)
    if user_step == 'finish': return continue_scenario(db, update, user_scenario)


def continue_scenario(db, update, user_scenario):
    """ Запускается при наличии незавершенного стейта пользователя через фильтр в начале функции общения communication()
    . Создает или находит в БД: 'db.form_step' стейт пользователя с полученным из сообщения сценарием. Запускает хэндлер
    из сценария, создающий, если нужно необходимую таблицу с данными, или выполняющий прочий функционал. Далее если
    хэндлер возвращает True, перезаписывает шаг в стейте пользователя. И отправляет ответ из этого шага по сценарию
    'settings.SCENARIOS'. Если пользователь на финишном шаге сценария, хэндлер должен вернуть False и выполнение
    прекратится без перезаписи шага."""

    # -------------------- запись с хэндлера в бд -------------
    user_state = form_state_find(db, update, user_scenario)
    user_handler = settings.SCENARIOS[user_scenario]['steps'][user_state['step']]['handler']
    if user_handler is not False:
        user_handler = getattr(all_handlers, user_handler) # хэндлер должен записывать необходимые данные в соотв.табл.
        if user_handler(db, update, user_scenario) is False: return

    # ------------------ обновление шага сценария --------------
    user_next_step = settings.SCENARIOS[user_state['scenario']]['steps'][user_state['step']]['next_step']
    db.form_step.update_one({'user_id': user_state['user_id'], 'scenario': user_state['scenario']}, {'$set': {'step': user_next_step}})

    # ------------------ рабочие данные ----------------------
    user_state = form_state_find(db, update, user_scenario)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard is not False: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)

    # ---------------------- ответ -------------------------
    update.message.reply_text(user_answer, reply_markup=user_keyboard)



def get_user_avatar(user_data):
    """ Рандомные смайлики-аватары для пользователей. просто доп. опция. По умолчанию не используется"""
    if 'smile' in user_data:
        return user_data['smile']
    else:
        user_data['smile'] = emojize(choice(settings.USER_EMOJI), language="alias");
        return user_data['smile']


def image_analyze(filename, update, user_data, user):
    """ Логика ответов пользователю при распозновании изображений. Отправка описания уже на русском языке"""

    # Блок генерации описания изображения, перевода на русский яз. и отправки сообщения польз-ю.
    try:
        mes = image_to_text_translate_rus(os.path.abspath(filename))
        log.info(f'На файле распознано: {mes}')
        update.message.reply_text(f'Теперь я знаю как выглядит {mes}')
        update.message.reply_text(f'{emojize(settings.NAME_EMOJI["смеющееся лицо"])}')
        time1 = time.time()

        # Блок анализа !концептов! изображения, и отправки польз-ю.
        concepts_photo = image_to_tags(filename)

        row_concept_photo = ''
        for con in concepts_photo:
            row_concept_photo += ' : '.join(con) + '\n'
        time2 = time.time()
        if time2 - time1 < 5:
            time.sleep(5)
        update.message.reply_text(f'Кстати, вот что я распознал на этой фотке: \n'
                                  f'\n "Тэг" : Шанс что он на фото \n'
                                  f'{row_concept_photo.center(50)}\n'
                                  f'{emojize(settings.NAME_EMOJI["глаза спирали"])}')


        # Блок перевода концептов на русский. Отправка осуществляется после утвердительного ответа.
        update.message.reply_text(
            f'Для перевода введите команду "переведи теги" {emojize(settings.NAME_EMOJI["нимб"])}')
        tags_eng = ''
        for n, tag in enumerate(concepts_photo):
            tags_eng += tag[0] + ',' if n < len(concepts_photo) - 1 else tag[0]
        rus = translate_ensglish_to_russian(tags_eng)
        tags_rus = rus.split(',')
        for n, t_r in enumerate(tags_rus):
            concepts_photo[n][0] = t_r

        # Запись русскоязычных концептов в user_data
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'photo': concepts_photo}}
        )
    except Exception:
        update.message.reply_text('Подключение прервалось. Давайте попробуем еще раз.')







