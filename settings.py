""" Модуль настройки вопросов и сценариев для них. В переменной INTENTS прописываются быстрые ответы на разные сообщения
 пользователя. В сценариях SCENARIOS прописываются различные операции, в зависимости от желаемого функционала бота.
 К каждому сценарию пишутся отдельно хэндлеры в папке scenario_handlers. Можно пропускать их через встроеный в
 тедеграм алгоритм сценариев: telegram.ext.ConversationHandler как в примере с scenario_handlers.feedback. Или без
 лишнего кода управлять прохождением сценариев напрямую через свои хендлеры. В таком случае последнему шагу
 присваивается имя 'finish' и вызываемый хэндлер должен возвращать False, чтоды приостановить процесс перезаписи шага
 в стейте юзера. Хэндлеры для ручного контроля живут в scenario_handlers.all_handlers.py """


from emoji import emojize


NAME_EMOJI = {'нимб': ':smiling_face_with_halo:',
              'расплывающееся лицо': ':melting_face:',
              'глаза спирали': ':face_with_spiral_eyes:',
              'смеющееся лицо': ':beaming_face_with_smiling_eyes:',
              'сердце': ':heart_on_fire:',
              'лицо прячется': ':face_with_peeking_eye:',
              'пришелец': ':alien:'}



INTENTS = [
        {
                'name': 'приветствие',
                'tokens': ('привет', 'здравствуйте', 'hi', 'hello', 'доброе утро', 'добрый день',
                           'добрый вечер'),
                'scenario': None,
                'answer': 'Приветствую вас, {name_user}! Можете прислать мне любое фото и увидите что я об этом думаю..)'
        },
        {
                'name': 'как дела',
                'tokens': ('как дела',),
                'scenario': None,
                'answer': f'Пока не родила! {emojize(":beaming_face_with_smiling_eyes:", language="alias")}!'
        },
        {
                'name': 'спасибо',
                'tokens': ('спасибо', 'благодарою', 'спс',),
                'scenario': None,
                'answer': f'Было бы за что {emojize(NAME_EMOJI["пришелец"])}'
        },
        {
                'name': 'досвидания',
                'tokens': ('пока', ),
                'scenario': None,
                'answer': 'досвидания'
        },
        {
                'name': 'переведи теги',
                'tokens': ('переведи теги',),
                'scenario': 'translate_tags',
                'answer': None
        }
]
DEFAULT_ANSWER = 'Вы сказали {text}. Можно отправить мне изображение чтобы я его проанализировал. {smile}'

SCENARIOS = {
        'переведи теги': {
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
                                        'next_step': False}
                        }
        },
        'Оставить отзыв': {
                'first_step': 1,
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


