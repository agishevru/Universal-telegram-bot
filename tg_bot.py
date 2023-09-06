""" Простой телеграм бот для общения с функцией выполнения сценариев и распознаванием изображений."""

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from telegram.ext import messagequeue as mq

from config import token
from handlers import *
from scenario_handlers.feedback import feedback_conversation_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger()

file_handler = logging.FileHandler('tg_bot.log', encoding='utf-8')
log.addHandler(file_handler)  # Привязка к созданному логеру 'Log'
# file_handler.setLevel(logging.DEBUG)



def main(): # запуск главных функций бота
    mybot = Updater(token)

    mybot.bot._msg_queue = mq.MessageQueue()
    mybot.bot._is_messages_queued_default = True     # сообщения по умолчанию должны ставиться в очередь

    log.info('Бот запускается')
    dt = mybot.dispatcher

    subscription = mybot.job_queue.run_repeating(send_updates, interval=5)    # отложенная задача / рассылка

    dt.add_handler(feedback_conversation_handler)
    dt.add_handler(CommandHandler('start', greet_user, pass_user_data=True)) # хэндлер комманд. привязывает "строку" к созданной функции
    dt.add_handler(CommandHandler('pic', send_pic, pass_user_data=True))
    dt.add_handler(RegexHandler('^(Получить изображение)$', send_pic, pass_user_data=True)) # хэндлер комманд с регулярными выражниями. для кнопок
    dt.add_handler(MessageHandler(Filters.contact, get_contact, pass_user_data=True)) # хэндлер текста. считывает отправленный контакт
    dt.add_handler(MessageHandler(Filters.location, get_location, pass_user_data=True))
    dt.add_handler(RegexHandler('^(Подписаться)$', subscribe))  # запускает функцию подписки
    dt.add_handler(RegexHandler('^(Отписаться)$', unsubscribe))  # запускает функцию отписки


    dt.add_handler(CommandHandler('subscribe', subscribe))
    dt.add_handler(CommandHandler('unsubscribe', unsubscribe))
    # dt.add.handler(CommandHandler('alarm', set_alfrm, pass_args=True, pass_job_queue=True))     # задаваемая пользователем отложенная задача. pass_args(разбивка на аргументы: /alarm n

    dt.add_handler(MessageHandler(Filters.photo, check_user_photo, pass_user_data=True))
    dt.add_handler(MessageHandler(Filters.text, talk_to_me, pass_user_data=True))   # хэндлер текста. считывает текст

    mybot.start_polling() # слушает сервер
    mybot.idle()




if __name__ == '__main__':
    main()