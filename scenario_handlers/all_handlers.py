""" Хэндлеры для ручного стиля прохождения сценариев. НЕ С ПОМОЩЬЮ telegram.ext.ConversationHandler.
 Для продвижения по шагам хэндлер должен возвращать True. Тогда функция управлением сценарием utils.continue_scenario()
 перезапишет шаг стейта в соответствии со сценарием и продолжит остальные действия. Если хэндлер возвращает False -
 выполнение сценария прекращается. Шаг в стейте остается прежним. Для выхода пользователя из сценария используется
 функция state_clean(), стирающая стейт с данным сценарием из бд.
 """

from emoji import emojize
import settings


def state_clean(db,update, user_scenario):
    """ Общая функция стирания стейта при отмене сценария пользователем. Чтобы фильтр стейтов на входе функции общения
    'comunication' не закидывал юзера обратно в незаконченный сценарий. """
    db.form_state.delete_one({'user_id': update.effective_user.id, 'scenario': user_scenario})
    return False




#--------------------- Хэндлеры для сценария "переведи тэги" -------------------

def translate_tags(db,update, user_scenario):
    """ Получает ответ пользователя и выводит результат """
    user = db.users.find_one({'user_id': update.effective_user.id})
    text = update.message.text
    if 'photo' in user:
        answer = ''
        for con in user['photo']:
            answer += ': '.join(con) + '\n'
        answer += emojize(settings.NAME_EMOJI['лицо прячется'])
        if text.lower() in ['да', 'продолжить', 'прододжай', 'ok', 'давай', 'неважно',]:
            update.message.reply_text(answer)
        elif text.lower() in ['нет', 'не надо', 'не нужно', 'отмена', 'no',]:
            update.message.reply_text("Так действительно достовернее")
        elif text.lower in ['выйти из сценария', 'закончить', 'назад',]:
            state_clean(db,update, user_scenario)
        else:
            update.message.reply_text("Не понял, да, или нет?")
        return True

def translate_tags_finish(db,update, user_scenario):
    """ Вызывается при повторном вызове(если стейт уже есть). Возвращает False, останавливая сценарий. """
    user = db.users.find_one({'user_id': update.effective_user.id})
    if 'photo' in user:
        answer = ''
        for con in user['photo']:
            answer += ': '.join(con) + '\n'
        answer += emojize(settings.NAME_EMOJI['лицо прячется'])
        update.message.reply_text(answer)
        return False
# --------------------------- Конец сценария ------------------------

