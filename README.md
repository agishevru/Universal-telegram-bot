Universal Telegram Bot
===================


Universal Telegram Bot - простой чат бот для Telegram с возможностью отправки изображений пользователю.
Бот умеет обрабатывать изображения с помощью сервисов clarifai. Если ему отправить изображение, он отпрвит его описание
на русском языке и список распознанных концепций на английском языке. Предложит перевести, и вернет перевод.
Так же бот поддерживает добавление любых сценариев. Работает через базу данных MongoDB. Логирует все события в консоль
и файл лога.


Описание Бота:
==============

Основное приложение. `tg_bot.py`
--------------------------------
---

Основное приложение распологается в файле tg_bot.py. В нем создаются главные классы библиотеки telegram-bot:

```python
def main(): # запуск главных функций бота
    mybot = Updater(token)
    dt = mybot.dispatcher
```

И базовые хэндлеры для реакции на события и команды:
```
dt.add_handler(feedback_conversation_handler)
dt.add_handler(CommandHandler('start', greet_user, pass_user_data=True)) # хэндлер комманд. привязывает "строку" к созданной функции
dt.add_handler(CommandHandler('pic', send_pic, pass_user_data=True))
dt.add_handler(RegexHandler('^(Получить изображение)$', send_pic, pass_user_data=True)) # хэндлер комманд с регулярными выражниями. для кнопок
dt.add_handler(MessageHandler(Filters.contact, get_contact, pass_user_data=True)) # хэндлер текста. считывает отправленный контакт
dt.add_handler(MessageHandler(Filters.location, get_location, pass_user_data=True))
dt.add_handler(RegexHandler('^(Подписаться)$', subscribe))  # запускает функцию подписки
dt.add_handler(RegexHandler('^(Отписаться)$', unsubscribe))  # запускает функцию отписки

```

Распределительные хэндлеры `handlers.py.`
--------------------------

---
Базовые хэндлеры вызывают функции-хэндлеры, обрабатывающие события более предметно. Они распологаются в модуле
`handlers.py.`

1. Например, хэндлер старта бота, создающий коллекцию в БД с профайлом пользователя и отправляющий приветственное сообщение:

```python
def greet_user(bot, update, user_data)
```

2. Хэндлер, реагирующий на сообщения от пользователя. Запускает в свою очередь функцию с ветвистой логикой
общения в модуле utils.communication:

```python
def talk_to_me(bot, update, user_data):
    """ Получает текст и запускает функцию общения """
    user = get_or_create_user(db, update.effective_user, update.message)
    log.info(f'Получено: {update.message.chat.username} - {update.message.chat.id} - {update.message.text}')
    communication(bot, update, user_data, user) # логика общения
```

3. Хэндлер, привязанный к кнопке "Получить изображение" - отправляет пользователю случайное фото из выбранной папки:
`images_list = glob('images/themes/*.jp*g'):`

```python
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

```

4. Хэндлер, принимающий фото от пользователя. Запускает функцию обработки изображения через алгоритмы
clarifai.com. В результате пользователю возвращается описание изображения на русском языке
и распознанные на нем темы на английском языке. Бот спрашивает, нужно ли перевести, и переводит если ответ
положительный. Фото сохраняются в директорию /downloads.

```python
def check_user_photo(bot, update, user_data)
```

5. Хэндлеры подписки и отписки. Подписавшимся функция `send_updates` отправляет сообщение. Интервал задается 
в модуле `tg_bot.py`, функцией `subscription = mybot.job_queue.run_repeating(send_updates, interval=5)`

```python
def subscribe(bot, update)
def unsubscribe(bot, update)
@mq.queuedmessage # очередь, с лимитами от телеграм
def send_updates(bot, job):
    """ Отправляет всем пользователям с подпиской сообщение. Тайминги выставляются в tg_bot.main.subscription"""
    for user in all_subscription(db):
        bot.sendMessage(chat_id=user['chat_id'], text=f'Cпамчик {emojize(settings.NAME_EMOJI["сердце"])}')
```
Эти распределительные хэндлеры вызывают логические блоки, обеспечивающие выполнение обозначенных
задач. Эти функции распологаются в модуле `utils.py`. 


Логические функции для выполнения задач. `utils.py`
---------------------------------------
---
1. Функция, принимающая изображение и прогоняюшая его через алгоритмы `clarifai.com`, прописанные в модуле 
`clarifai/general_image_recognition.py`. Чтобы они работали, необходимо зарегистрироваться на сайте clarifai.com, и
и получить индивидуальный ключ доступа к api, называемый `PAT`. Его нужно будет прописать в `config.py`:
`PAT_CLARIFAI = ''`. Возвращает описание фото



```python
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
        update.message.reply_text(f'Кстати, вот что я распознал на этом фото: \n'
                                  f'"Тэг" : Шанс что он на фото\n'
                                  f'{row_concept_photo.center(50)}\n'
                                  f'{emojize(settings.NAME_EMOJI["глаза спирали"])}')
...
```
2. Клавиатура с основными кнопками. По умолчанию, прикрепляется к ответам бота, кроме сценариев.
```python
def get_keyboard():
    """ Клавиатура, привязанная к панели ввода """
    contact_button = KeyboardButton('отправить свой контакт', request_contact=True)
    location_button = KeyboardButton('отправить свою локацию', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([['Оставить отзыв', 'Подписаться', 'Отписаться'],['Получить изображение']], resize_keyboard=True)
    return my_keyboard
```
3. Функция общения с пользователем. Работает в связке с модулем `settings.py`, где указываются интенты и сценарии.
Принцип работы:  
- получает сообщение от пользователя.
- ищет его в таблице стейтов, чтобы понять, в сценарии он или нет. 
- Если нет, сравнивает сообщение с прописанными интентами в `settings.INTENTS`. Если находит - возвращает ответ из
интента. Если интент есть, но в нем не прописан ответ, запускает указанный в нем сценарий.
- Если интент не находит, возвращает `DEFAULT_ANSWER` сообщение.

```python
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
```

4. За выполнение сценария отвечают функции:

```python
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
...


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
...
```

Логика общения. `settings.py`
--------------
---
Логика общения настраивается в модуле `settings.py`. В нем прописываются вопросы - ответы, а так же возможные
сценарии для бота. 
- В переменной INTENTS прописываются быстрые ответы на разные сообщения
пользователя. 
- В сценариях SCENARIOS прописываются различные операции, в зависимости от желаемого функционала бота.
К каждому сценарию пишутся отдельно хэндлеры в модуле `scenario_handlers.all_handlers.py`. Можно пропускать их через 
встроеный в телеграм алгоритм сценариев: `telegram.ext.ConversationHandler` как в примере с 'Оставить отзыв' ->
`scenario_handlers.feedback`. Или без лишнего кода управлять прохождением сценариев напрямую через свои хендлеры. В таком случае последнему шагу
присваивается имя 'finish' а вызываемый хэндлер должен возвращать False, чтобы приостановить процесс перезаписи шага
в стейте юзера. Хэндлеры для ручного контроля живут в `scenario_handlers.all_handlers.py`.




Установка
---------
1. Создайте виртуальное окружение и активируйте его. Потом в виртуальном окружении выполните:

```shell
    pip install -r requiremtents.txt
```
2. Положите картинки в папку images. Файлы должны быть в формате .jpg / .jpeg

Настройка
---------
1. Создайте файл config.py и добавьте туда следующие настройки:

```python
    API_KEY = 'ваш ключ api, который вы полуичили у BotFather'
    MONGO_LINK = 'mongodb://localhost:27017/'
    MONGO_DB = 'tg_bot'
    # если нужно распознование изображений:
    PAT_CLARIFAI = 'ваш ключ api сгенированный на сервисе clarifai'
```
2. Настройте логику ответов в файле settings.py - придумайте интенты и ответы на на них, там же прописываются сценарии:

```python
INTENTS = [
    {
        'name': 'приветствие',
        'tokens': ('привет', 'здравствуйте', 'hi', 'hello', 'доброе утро', 'добрый день', 'добрый вечер'),
        'scenario': None,
        'answer': 'Приветствую вас, {name_user}!'
    }

SCENARIOS = {
        'Оставить отзыв': {
            'steps': {
                1: {
                    'text': 'Пожалуйста введите имя и фамилию. Чтобы выйти - нажмите "Отмена"',
                    'failure_text': None,
                    'keyboard': [['Отмена']],
                    'handler': 'full_name',
                    'next_step': 2},
                2: {
                    'text': 'Оцените бота',
                    'failure_text': None,
                    'keyboard': [['1','2','3','4','5'],['Отмена']],
                    'handler': 'rating',
                    'next_step': 3},
                3: {
                    'text': 'Введите комментарий',
                    'failure_text': None,
                    'keyboard': [['Отмена']],
                    'image': None,
                    'handler': 'comment',
                    'next_step': 'finish'},
                'finish': {
                    'text': False,
                    'failure_text': False,
                    'keyboard': False,
                    'handler': False,
                    'next_step': False}
                }
        }
}
```
Запуск
------
В активированном виртуальном окружении запустите:

```shell
    bot.py
