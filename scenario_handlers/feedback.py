""" Хэндлеры для кнопки заполнить анкету. Шаги прописываются в anketa_conversation_handler в этом модуле:
{entry_points=точка входа, states=шаги, fallbacks=сообщение для нерелевантного ввода}.
Для каждого шага создается хэндлер. Хэндлеры по общему принципу обращаются в settings.SCENARIOS для получения
инструкций. Механизм тестовый, возможна логика использования сценариев без ConversationHandler от telegram.bot,
 если прописать эти хэндлеры отдельно.
"""
import logging
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import ConversationHandler, RegexHandler, MessageHandler, Filters

import settings
from db import db, get_or_create_feedback_anketa, form_state_start, form_state_find
from utils import get_keyboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()

file_handler = logging.FileHandler('tg_bot.log', encoding='utf-8')
log.addHandler(file_handler)  # Привязка к созданному логеру 'Log'


################################################################################
# <-- feedback_conversation_handler -->

def feedback_anketa_start(bot, update, user_data):
    """ Старт сценария. Выявляет шаг пользователя и возвращает необходимый хэндлер.
    Ищет в таблице стейтов(db.form_step) пользователя(user_id) со сценарием(scenario) и возвращает/создает его стейт """

    log.info(f'пользователь {update.effective_user.username} запустил сценарий "Оставить отзыв"')
    # ------------------ рабочие данные ----------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user)
    user_state = form_state_start(db, update)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_next_step = settings.SCENARIOS[user_scenario]['steps'][user_step]['next_step']

    # ------------------ выход если отзыв оставлен ----------------------
    if user_next_step is False:
        text = '<b>Имя:</b> <i>{full_name}</i>\n' \
               '<b>Рейтинг приложения: </b> <i>{rating}</i>\n' \
               '<b>Комментарий: </b> <i>{comment}</i>'.format(**anketa_user)
        update.message.reply_text(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    # ------------------ ответ если отзыва нет ----------------------
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user_handler = settings.SCENARIOS[user_scenario]['steps'][user_step]['handler']

    update.message.reply_text(user_answer, reply_markup=user_keyboard)
    return user_handler

def full_name_handler(bot, update, user_data):
    """ Записывает ФИО в db.anketa. Отп. клавиатуру для след. шага и след запрос. """

    # ----------------------- выход если отмена ----------------
    scenario = 'Оставить отзыв'
    user_state = form_state_find(db, update, scenario)
    text = update.message.text
    if text == 'Отмена':
        db.form_step.delete_one({'user_id': user_state['user_id'], 'scenario': scenario})
        return ConversationHandler.END
    if len(text.split(' ')) !=2:
        update.message.reply_text('Пожалуйста введите имя и фамилию корректно')
        return 'full_name'

    # ------------------ обновление шага сценария --------------
    user_next_step = settings.SCENARIOS[user_state['scenario']]['steps'][user_state['step']]['next_step']
    db.form_step.update_one({'user_id': user_state['user_id'], 'scenario': user_state['scenario']}, {'$set': {'step': user_next_step}})
    # ------------------ рабочие данные ----------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user)
    text = update.message.text
    user_state = form_state_find(db, update, scenario)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard is not False: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user_handler = settings.SCENARIOS[user_scenario]['steps'][user_step]['handler']

    # ------------------ запись в форму ----------------------
    db.feedback.update_one({'_id': anketa_user['_id']},
                         {'$set': {'full_name': text}})
    update.message.reply_text(user_answer, reply_markup=user_keyboard)
    return user_handler

def rating_handler(bot, update, user_data):
    """ Записывает рейтинг в db.anketa. """

    # ----------------------- выход если отмена ----------------
    scenario = 'Оставить отзыв'
    user_state = form_state_find(db, update, scenario)
    text = update.message.text
    if text == 'Отмена':
        db.form_step.delete_one({'user_id': user_state['user_id'], 'scenario': scenario})
        return ConversationHandler.END

    # ------------------ обновление шага сценария --------------
    user_next_step = settings.SCENARIOS[user_state['scenario']]['steps'][user_state['step']]['next_step']
    db.form_step.update_one({'user_id': user_state['user_id'], 'scenario': user_state['scenario']}, {'$set': {'step': user_next_step}})

    # ------------------ рабочие данные ----------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user)
    text = update.message.text
    user_state = form_state_find(db, update, scenario)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard is not False: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user_handler = settings.SCENARIOS[user_scenario]['steps'][user_step]['handler']

    # ------------------ запись в форму ----------------------
    db.feedback.update_one({'_id': anketa_user['_id']},
                         {'$set': {'rating': text}})
    update.message.reply_text(user_answer, reply_markup=user_keyboard)
    return user_handler

def comment_handler(bot, update, user_data):
    """ Записывает комментарий в db.anketa и отпр. польз. его результаты"""

    # ----------------------- выход если отмена ----------------
    scenario = 'Оставить отзыв'
    user_state = form_state_find(db, update, scenario)
    text = update.message.text
    if text == 'Отмена':
        db.form_step.delete_one({'user_id': user_state['user_id'], 'scenario': scenario})
        return ConversationHandler.END

    # ------------------ обновление шага сценария --------------
    user_next_step = settings.SCENARIOS[user_state['scenario']]['steps'][user_state['step']]['next_step']
    db.form_step.update_one({'user_id': user_state['user_id'], 'scenario': user_state['scenario']}, {'$set': {'step': user_next_step}})

    # ------------------ рабочие данные ----------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user)
    text = update.message.text
    user_state = form_state_find(db, update, scenario)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
    user_answer = settings.SCENARIOS[user_scenario]['steps'][user_step]['text']
    user_keyboard = settings.SCENARIOS[user_scenario]['steps'][user_step]['keyboard']
    if user_keyboard is not False: user_keyboard = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True, one_time_keyboard=True)
    user_handler = settings.SCENARIOS[user_scenario]['steps'][user_step]['handler']

    # ------------------ запись в форму ----------------------
    db.feedback.update_one({'_id': anketa_user['_id']},
                         {'$set': {'comment': update.message.text}})

    # ------------------ ответное сообщение ------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user)
    text = '<b>Имя:</b> <i>{full_name}</i>\n' \
           '<b>Рейтинг приложения: </b> <i>{rating}</i>\n' \
           '<b>Комментарий: </b> <i>{comment}</i>'.format(**anketa_user)
    update.message.reply_text(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)

    # ----------------- завершение  -----------------
    return ConversationHandler.END



def dontknow(bot, update, user_data):
    """ Отаправляет сообщение в случае некорректного ввода. """
    update.message.reply_text('Не релевантый ввод')


# сам хэндлер сценариев ConversationHandler, с прописанными шагами
feedback_conversation_handler = ConversationHandler(
    entry_points=[RegexHandler('^(Оставить отзыв)$', feedback_anketa_start, pass_user_data=True)],
    states={'full_name': [MessageHandler(Filters.text, full_name_handler, pass_user_data=True)],
            'rating': [RegexHandler('^(1|2|3|4|5|Отмена)$', rating_handler, pass_user_data=True)],
            'comment': [MessageHandler(Filters.text, comment_handler, pass_user_data=True)], },
    fallbacks=[MessageHandler(Filters.text | Filters.photo | Filters.video | Filters.document,
                              dontknow, pass_user_data=True)])
# --> End scenario feedback_conversation_handler <--
######################################################################