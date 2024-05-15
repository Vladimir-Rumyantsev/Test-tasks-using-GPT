import telebot
from openai import OpenAI
import os
import random


bot = telebot.TeleBot('6842595275:AAE6Iw_VjiEidw-geLaoMnDdV5I5S8FudWI')
topics_from_database = os.listdir('database')


def AI_biologist(text):
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    completion = client.chat.completions.create(
        model="IlyaGusev/saiga_mistral_7b_gguf",
        messages=[
            {"role": "system",
             "content": 'Ты эксперт в области биологии. Отвечай как биолог и сохраняй научную точность.'
                        ' Не придумывай информацию, о которой у тебя нет научных подтверждений. '
                        'Если тебя спросили о чём-то, чего ты не знаешь, то так и скажи, что тебе '
                        'неизвестен ответ на данный вопрос и вежливо попроси пользователя научную '
                        'литературу на данную тему. ВСЕГДА ГОВОРИ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!'},
            {"role": "user", "content": text}
        ],
        temperature=1,
    )
    return completion.choices[0].message.content


def telegram_bot():
    @bot.message_handler(content_types=['text'])
    def send_text(message):
        try:
            if message.text.lower() == '/start':
                bot.send_message(message.chat.id, 'Стартовое сообщение!\n\nСейчас в базе данных есть такие темы:\n'
                                                  f'{topics_from_database}')

            else:

                client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

                completion = client.chat.completions.create(
                    model="IlyaGusev/saiga_mistral_7b_gguf",
                    messages=[
                        {"role": "system",
                         "content": 'Ты бот классификатор. Ты отвечаешь не пользователю, а с системе. '
                                    'Каждый твой ответ на запрос пользователя обязан быть в таком формате: '
                                    '<тема> | <количество>. Например, пользователь пишет сообщение '
                                    '"Мне нужны 4 задания про грибы", ты обязан дать такой ответ "Грибы | 4". '
                                    'Если тебе не удаётся определить тему сообщения пользователя или количество '
                                    'заданий, которое пользователь запрашивает, то ты обязан дать ответ "None | None". '
                                    'БУКВАЛЬНО КАЖДЫЙ ТВОЙ ОТВЕТ ВНЕ ЗАВИСИМОСТИ ОТ КОНТЕКСТА ОБЯЗАН БЫТЬ В ФОРМАТЕ '
                                    '<тема> | <количество>. ЕСЛИ НАРУШИТЬ ЭТО ПРАВИЛО ТО ЭТО МОЖЕТ ПРИВЕСТИ К '
                                    'КРИТИЧЕСКОЙ ОШИБКЕ В СИСТЕМЕ.'
                                    # 'Темы которые сейчас существуют в системе: грибы, '
                                    # 'кристаллохимия, разработка, жирафы. Если сообщение пользователя не подходит ни '
                                    # 'под одну из этих тем, то ответь "None | None"'
                         },
                        {"role": "user", "content": message.text}
                    ],
                    temperature=0.1,
                )

                response = list(completion.choices[0].message.content.split(' | '))

                if len(response) != 2:
                    bot.send_message(message.chat.id, AI_biologist(message.text))
                    raise Exception(f'Exception code 64\n\n{response}')

                response[0] = str(response[0]).lower()

                if response[0] not in topics_from_database:
                    bot.send_message(message.chat.id, AI_biologist(message.text))

                else:
                    try:
                        response[1] = int(response[1])
                    except:
                        bot.send_message(message.chat.id, 'Произошла ошибка. Пожалуйста, повторите ваш запрос!')
                        raise Exception(f'Exception code 72\n\n{response}')

                    contents = os.listdir(f'database/{response[0]}')
                    n = response[1]

                    if n > 10:
                        bot.send_message(message.chat.id, 'Вы запросили слишком много заданий!\n'
                                                          'Пожалуйста, не просите больше десяти заданий за раз.')

                    else:
                        len_contents = len(contents)

                        if n > len_contents:
                            n = len_contents

                        random_numbers = []

                        for i in range(n):
                            random_number = random.randint(0, len_contents - 1)

                            while random_number in random_numbers:
                                random_number = random.randint(0, len_contents - 1)

                            random_numbers.append(random_number)

                        line = ''

                        for i in random_numbers:
                            with open(f"database/{response[0]}/task_{i}.txt", "r", encoding='utf-8') as f:
                                line = (f'{line}Задание {f.read()}\n\n-------------------------------------------------'
                                        f'-----------\n\n')

                        bot.send_message(message.chat.id, line[:-62])

        except Exception as ex:
            bot.send_message(message.chat.id, f'Except...\n\n{ex}')

    bot.polling()


telegram_bot()
