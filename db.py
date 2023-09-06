""" Модуль с коллекциями для БД: mongodb. Настройки для подключения задаюся в config.py"""

from pymongo import MongoClient
import config


# Подключение локальной БД Mongo
db = MongoClient(config.MONGO_LINK)[config.MONGO_DB]


# -------------- Информация о пользователе -----------
def get_or_create_user(db, effective_user, message):
    """ Информация о пользователе. Коллекция хранится в db.users """

    user = db.users.find_one({'user_id': effective_user.id})
    if not user:
        user = {
            'user_id': effective_user.id,
            'first_name': effective_user.first_name,
            'last_name': effective_user.last_name,
            'username': effective_user.username,
            'chat_id': message.chat.id,
            'subscription': False}
        db.users.insert_one(user)
        return user
    else: return user
# -----------------------------------------------------



# -------------- Создание и поиск стейтов пользователя для сценариев ---------------------
def form_state_start(db, update):
    """ Состояние анкеты. Фиксирует выполнение шагов по сценарию.
    Вызывается в первый раз и ищет/создает объект с уникальными user_id и scenario.
    scenario забирается с нажатой кнопки или отправленного текста. (update.message.text).
    после инициации объекта доступ к нему осуществляется через функцию form_state_find(db, update, scenario)"""

    scenario = update.message.text
    state = db.form_step.find_one({'user_id': update.effective_user.id, 'scenario': scenario})
    if not state:
        state = {
            'user_id': update.effective_user.id,
            'scenario': scenario,
            'step': 1,
            'context': []}
        db.form_step.insert_one(state)
        return state
    return state

def form_state_find(db, update, scenario):
    """ Состояние анкеты. Фиксирует выполнение шагов по сценарию. scenario: задается вручную """
    state = db.form_step.find_one({'user_id': update.effective_user.id, 'scenario': scenario})
    return state
# ----------------------------------------------------------------------------------------



# --------- Создание и поиск коллекции для сценария 'Оставить отзыв' ---------------------
def get_or_create_feedback_anketa(db, effective_user):
    """ Создать или считать данные из анкеты: db.feedback.
     Анкета заполняется в соответсвии со сценарием settings.SCENARIOS['Заполнить анкету'] """

    user_feedback = db.feedback.find_one({'user_id': effective_user.id})
    if not user_feedback:
        user_feedback = {
            'user_id': effective_user.id,
            'full_name': None,
            'rating': None,
            'comment': None,}
        db.feedback.insert_one(user_feedback)
        return user_feedback
    return user_feedback
# -------------------------------------------------------------------------------------------





# ---------------- подписка ---------------------
def toggle_subscription(db, user):
    """ Меняет состояние подписки на противоположное. """
    if user['subscription'] is False:
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'subscription': True}})
    else:
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'subscription': False}})

def all_subscription(db):
    """ Возвращает пользователей с положительной подпиской. """
    users_subscribes = db.users.find({'subscription': True})
    return users_subscribes
# ----------------------------------------------

