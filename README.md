Universal Telegram Bot
===================


Universal Telegram Bot - простой чат бот для Telegram с возможностью отправки изображений пользователю. Это базовая версия,
для кастомизации под любой функционал. Бот поддерживает добавление любых сценариев и содержит готовую логику общения.
Так же умеет обрабатывать изображения с помощью сервисов <http://clarifai.com/>. Если ему отправить изображение, он отпрвит его описание
на русском языке и список распознанных концепций на английском языке. Предложит перевести, и вернет перевод.
 Работает через базу данных MongoDB. Логирует все события в консоль
и файл лога.

Бот реализован на `Python 3.8`

Описание Бота:
==============

Основное приложение: `tg_bot.py`
--------------------------------
---

Основное приложение распологается в файле `tg_bot.py`. В нем создаются главные классы библиотеки telegram-bot:

```python
def main(): # запуск главных функций бота
    mybot = Updater(token)  #
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

1. Например, хэндлер старта бота, создающий таблицу (коллекцию) в БД с профайлом пользователя и отправляющий приветственное сообщение:

```python
def greet_user(bot, update, user_data):
..
```

2. Хэндлер, реагирующий на сообщения от пользователя. Запускает в свою очередь функцию с ветвистой логикой
общения в модуле `utils.communication`:

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
<http://clarifai.com>. В результате пользователю возвращается описание изображения на русском языке
и распознанные на нем темы на английском языке. Бот спрашивает, нужно ли перевести, и переводит если ответ
положительный. Фото сохраняются в директорию `/downloads`.

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
задач. Функции распологаются в модуле `utils.py`. 


Блок логических функций для выполнения задач. `utils.py`
---------------------------------------
---
1. Функция, принимающая изображение и прогоняюшая его через алгоритмы <http://clarifai.com>, прописанные в модуле 
`clarifai/general_image_recognition.py`. Чтобы они работали, необходимо зарегистрироваться на сайте <http://clarifai.com>,
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

- `def start_scenario` - 
Запускается при включении сценария. Работает только с первым и финишным шагом. Остальные пробрасываются через
    фильтр в начале функции общения - 'communication()'. Создает или находит в БД: 'db.form_step' стейт пользователя
    с полученным из сообщения сценарием. Отправляет пользователю ответ из первого шага сценария 'settings.SCENARIOS'.
    Если пользователь на финишном шаге сценария, передает управление в continue_scenario. Которая действует сообразно
    прописанным в сценарии опциям.
```python
def start_scenario(db, update):
    log.info(f'пользователь {update.effective_user.username} запустил сценарий {update.message.text}')
    user_state = form_state_start(db, update)
    user_scenario = user_state['scenario']
    user_step = user_state['step']
...
```

- `def continue_scenario(db, update, user_scenario)` - Запускается при наличии незавершенного стейта пользователя через фильтр в начале функции общения communication()
    . Создает или находит в БД, в коллекции стейтов пользователя: `db.form_step` стейт пользователя с полученным из сообщения ***сценарием***. Запускает хэндлер
    из сценария, создающий, если нужно необходимую таблицу с данными, или выполняющий прочий функционал. Далее если
    хэндлер возвращает True, перезаписывает шаг в стейте пользователя. И отправляет ответ из этого шага по сценарию
    'settings.SCENARIOS'. Если пользователь на финишном шаге сценария, хэндлер должен вернуть False и выполнение
    прекратится без перезаписи шага

```python
def continue_scenario(db, update, user_scenario):
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
Логика общения настраивается в модуле со словесным бэкграундом: `settings.py` и модуле с хэндлерами к нему: `scenario_handlers.выбранный_модуль`. 
В словестном модуле `settings.py` прописываются интенты `settings.INTENTS`: быстрые вопросы - ответы, а так же возможные
сценарии `settings.SCENARIOS` для бота.

## Блок `INTENTS = [{..`:
   - `name:` В переменной указывается название темы, просто для удобной идентефикации. Ни на что не влияет.
   - `tokens:` В переменной перечисляются слова - триггеры, на которые среагирует функция `communication()`.
   - `answer:` В переменной - возваращаемый ответ.
   - `scenario:` Если же интент должен запускать сценарий, например, оставить отзыв, то указывается название, которое должно соответствовать
   названию в самом блоке сценариев `SCENARIOS = [{..`. Запуск сценария происходит если `answer:` отсутствует.
```python
INTENTS = [
        {
                'name': 'приветствие',
                'tokens': ('привет', 'здравствуйте', 'hi', 'hello', 'доброе утро', 'добрый день',
                           'добрый вечер'),
                'scenario': None,
                'answer': 'Приветствую вас, {name_user}! Можете прислать мне любое фото и увидите что я об этом думаю..)'
        }
```

## Блок `SCENARIOS = [{..`:


В `SCENARIOS` прописываются различные сценарии с последовательными операцими, в зависимости от желаемого функционала бота. К каждому сценарию пишутся
отдельно хэндлеры в дирректории `/scenario_handlers.выбранный модуль`. Вот описание структуры сценария:

```python
SCENARIOS = {
    'Оставить отзыв': {
        'first_step': 1,
        'steps': {
                1: {
                        'text': 'Пожалуйста введите имя и фамилию. Чтобы выйти - нажмите "Отмена"',
                        'failure_text': None,
                        'keyboard': [['Отмена']],
                        'handler': 'full_name',
                        'next_step': 2},..
```
- `'steps':` - Cодержит словари с ключом `номер шага`, и стандартными опциями в нем. 
- `'text':` - Cодержит сообщение пользователю, с нужным запросом для следующего шага.
- `'keyboard':` - Cодержит название кнопки для клавиатуры, которая при нажатии будет восприниматься как сообщение от пользователя.
- `'handler':` - Название хэндлера, который запускается в начале этого шага. Он проверяет релевантность полученных данных 
из сообщения пользователя, и если нужно, создает бд для фиксации этих данных. Далее если все успешно, он должен вернуть
True. Тогда обработчик сценария продолжит работу, перезапишет шаг в стейте, и отправит пользователю сообщение, указанное
в `'text':`, для начала следующего шага.
- `'next_step':` - используется при перезаписи шага. Из этого параметра берется номер. Если следующий шаг является 
последним, указывается значение `'finish'`. А следующий шаг должен иметь такое же название -`'finish'`. Когда обработчик 
сценария на финишном этапе запишет это состояние в стейт пользователя, то данный стейт будет проходить сквозь фильтры в 
функции `comunication()`. И сценарий больше не будет активироваться сам. Только при вводе пользователем соответствующего 
токена для запуска сценария. В таком случае у финишного шага стоит указать хэндлер, который будет выводить уже имеющиеся 
данные пользователя / стирать законченный стейт для перезапуска сценария.




Так же для каждого сценария с помощью функции 
`form_state_start(db, update)` модуля `db.py` создается стейт в коллекции `db.form_step` с актуальной информацией о прохождении конкретного сценария конкретным пользователем.
```python
def form_state_start(db, update):
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
```
На каждом шаге выполнения сценария значение `'step':` меняется на следующий шаг, и таким образом обработчики сценариев
узнают из какого шага в сценарии брать инструкцию. Эти механизмы прописаны уже автоматически в двух разных подходах работы со
сценариями. Один через встроенный в телеграмм `telegram.ext.ConversationHandler`. Другой - с самостоятельным контролем
шагов, уже встроенный в функцию `communication`. Далее - более подробное описание каждого подхода.


### 1. Сценарии через `telegram.ext.ConversationHandler`
Этот подход здесь реализован на примере со сценарием `'Оставить отзыв'`, к которому привязан целый модуль 
`scenario_handlers/feedback.py`, где прохождение сценария задается через
`ConversationHandler(entry_points='',entry_points='', fallbacks='')`: 
    
```python
feedback_conversation_handler = ConversationHandler(
    entry_points=[RegexHandler('^(Оставить отзыв)$', feedback_anketa_start, pass_user_data=True)],
    entry_points={'full_name': [MessageHandler(Filters.text, full_name_handler, pass_user_data=True)],
                     'rating': [RegexHandler('^(1|2|3|4|5|Отмена)$', rating_handler, pass_user_data=True)],
                    'comment': [MessageHandler(Filters.text, comment_handler, pass_user_data=True)], },
       fallbacks=[MessageHandler(Filters.text | Filters.photo | Filters.video | Filters.document,
                              dontknow, pass_user_data=True)])
```
   А сам `ConversationHandler(entry_points='',entry_points='', fallbacks='')` уже запускает функции,
   отвечающие за исполнение необходимых шагов, и находящиеся в этом же модуле:
```python
def feedback_anketa_start(bot, update, user_data):
    """ Старт сценария. Выявляет шаг пользователя и возвращает необходимый хэндлер."""
    ..
def full_name_handler(bot, update, user_data):
    """ Записывает ФИО в db.anketa. Отп. клавиатуру для след. шага и след запрос. """
    ..
def rating_handler(bot, update, user_data):
    """ Записывает рейтинг в db.anketa. """
    ..
def comment_handler(bot, update, user_data):
    """ Записывает комментарий в db.anketa и отпр. польз. его результаты"""
    ..
def dontknow(bot, update, user_data):
    """ Отаправляет сообщение в случае некорректного ввода. """
```
В целях обеспечения стандартизации работы со сценариями эти функции обращаются в общий блок сценариев `settings.SCENARIOS`
 за получением инструкций по актуальному шагу. Этот принцип можно исключить, тем самым упростив код самостоятельно, и 
оставив контроль за переходом на след шаг только в хэндлерах, без обращения к `settings.SCENARIOS`.

В первой функции-хэндлере важной является функция создания стейта пользователя `get_or_create_feedback_anketa`.
Таким образом мы фиксируем в бд., что пользователь начал такой-то сценарий, и сейчас на таком-то шаге. Так же следом 
функция `form_state_start` создает необходимую для конкретного сценария таблицу(коллекция) в бд, куда пользователь и 
будет заносить свои данные.
```python
def feedback_anketa_start(bot, update, user_data): # запускается первой, при старте сценария
    # ------------------ рабочие данные ----------------------
    anketa_user = get_or_create_feedback_anketa(db, update.effective_user) # создаем стейт состояния сценария
    user_state = form_state_start(db, update)   # создаем таблицу для данных пользоватея в сценарии
```
В следующих функциях-хэндлерах появляется блок перезаписи шага, после проверки на актуальность полученного сообщения от 
пользователя. И заполнения таблицы ответом пользователя. В конце возвращается ответ из сценария.
```python
def full_name_handler(bot, update, user_data):
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
    ..
    # ------------------ запись в форму ----------------------
    db.feedback.update_one({'_id': anketa_user['_id']},
                         {'$set': {'full_name': text}})
    # -------------------- ответ ----------------------
    update.message.reply_text(user_answer, reply_markup=user_keyboard)
    return user_handler
```

Для более детального изучения см. модуль `scenario_handlers/feedback.py`, где код подробно документирован.

## 1. Сценарии через свои собственные хэндлеры, упрощенный подход.

Второй принцип позволяет без лишнего кода управлять прохождением сценариев напрямую через свои хендлеры.
Вход в сценарий осуществляется по ключевому слову в интенте. Важно, чтобы оно было в единственном варианте, и соответсвовало
названию сценария, тк по нему создастся стейт с таким названием. А от него функции - обработчики сценариев, будут 
выходить на этот сценарий:
```python
INTENTS = [
        {
        'name': 'переведи теги',
        'tokens': ('переведи теги',),   # ключевое слово
        'scenario': 'translate_tags',
        'answer': None}..
SCENARIOS = {
        'переведи теги': {  # название сценария
                        'first_step': 1,
                        'steps': {
                                1: {
                                    'text': 'Но есть одна проблема: я очень плохо перевожу. Продолжить?',
                                    'failure_text': None,
                                    'handler': 'translate_tags',
                                    'keyboard': False,
                                    'next_step': 'finish'},
                                'finish': {
                                    'text': False,
                                    'failure_text': False,
                                    'handler': 'translate_tags_finish',
                                    'keyboard': False,
                                    'next_step': False}}}}
```
Работа со сценариями в этом случае осуществляется с помощью двух функций - обработчиков сценариев:
### Начало сценария: `def start_scenario()`
```python
def start_scenario(db, update):
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
```
Запускается при включении сценария. Работает только с первым и финишным шагом. Остальные пробрасываются через
фильтр в начале функции общения - `communication()`. Создает или находит в БД таблицу (коллекцию) `db.form_step`
стейта пользователя с полученным из сообщения сценарием. Отправляет пользователю ответ из первого шага сценария `settings.SCENARIOS`.
Если пользователь на финишном шаге сценария, передает управление в `continue_scenario()`. Которая действует сообразно
прописанным в сценарии опциям.

### Продолжение сценария: `def continue_scenario()`
```python
def continue_scenario(db, update, user_scenario):
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
```
Запускается при наличии незавершенного стейта пользователя через фильтр в начале функции общения `communication()`
. Создает или находит в БД таблицу (коллекцию) `db.form_step` стейта пользователя с полученным из сообщения сценарием. Запускает хэндлер
указанный в сценарии, создающий, если нужно необходимую таблицу с данными, или выполняющий прочий функционал. Далее если
хэндлер возвращает `True`, перезаписывает шаг в стейте пользователя. И отправляет ответ из этого шага по сценарию
'settings.SCENARIOS'. Если пользователь на финишном шаге сценария, хэндлер должен вернуть `False` и выполнение
прекратится без перезаписи шага.


Общий процесс работы сценариев и хэндлеров к ним прописан выше, в начале раздела. Хэндлеры для ручного контроля 
находятся в `scenario_handlers.all_handlers.py`. Главное, что стоит отметить еще раз - хэндлеры контролируют переход на 
следующий шаг с помощью возвращаемого значения `return True / False`. Если `True` - обработчик сценария `continue_scenario()` 
продолжит работу: перезапишет шаг, и отправит сообщение `SCENARIOS['название_сценария_из_стейта']['steps'][шаг_из_стейта]['text']`
. Если же хэндлеру не понравился ввод пользователя и он хочет перезапросить ввод, он должен сам ответить пользователю и 
вернуть `False`, тогда пользователь останется на этом же шаге. А фильтр стейтов в функции `communication()` запустит 
снова `continue_scenario()`. 
## Во избежание вечной закольцованности и фактически поломки бота в глазах пользователя, нужно всегда пропиывать в хэндлерах возможность отмены сценария:

```python
# Любой хэндлер из сценария:
def some_handler(db,update, user_scenario):
    user = db.users.find_one({'user_id': update.effective_user.id})
    text = update.message.text
    if text.lower in ['выйти из сценария', 'закончить', 'назад',]: # проверяем не хочет ли польозователь выйти
        state_clean(db,update, user_scenario) # стираем стейт и возвращаем False
        return False

# Общая функция стирания стейта при отмене сценария пользователем. Чтобы фильтр стейтов на входе функции общения 
# 'comunication' не закидывал юзера обратно в незаконченный сценарий.
def state_clean(db,update, user_scenario):
    db.form_state.delete_one({'user_id': update.effective_user.id, 'scenario': user_scenario})
    return False
```



# Инструкции быстрой настройки и старта бота.
Установка
---------
1. Установите Python3.8. Создайте виртуальное окружение и активируйте его. Потом в виртуальном окружении выполните:

```shell
    pip install -r requiremtents.txt
```
2. Установите и разверните Базу данных MongoDB, руководствуясь официальными инструкциями к вашей ОС.


3. Положите картинки в папку images. Файлы должны быть в формате .jpg / .jpeg

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
###### Если нужны сервисы распознования изображений, зарегистрируйтесь на сайте <http://clarifai.com/>. И получите индивидуальный ключ доступа `PAT`.

2. Настройте логику ответов в файле settings.py - придумайте интенты и ответы на на них, там же прописываются сценарии.
Создайте необходимые хэндлеры, как описано выше. В Боте прописано и настроено два базовых сценария:
   - 'Оставить отзыв'
   - 'переведи теги'. 

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
python3.8 tg_bot.py
```
Если все успешно, бот начнет выводить в консоль логи о событиях.
