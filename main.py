import telebot
from telebot import types
import os
import datetime
import time
import random
from openai import OpenAI


bot = telebot.TeleBot('TOKEN')

main_menu = 'Главное меню.\nПожалуйста, выберите режим работы бота.'

start_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_button.add(types.KeyboardButton('/start'))

main_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_button.add(
    types.KeyboardButton('Режим 1'),
    types.KeyboardButton('Режим 2'),
    types.KeyboardButton('Режим 3')
)

in_main_menu_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
in_main_menu_button.add(
    types.KeyboardButton('В главное меню')
)

in_main_menu_and_history_cleanup_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
in_main_menu_and_history_cleanup_button.add(
    types.KeyboardButton('В главное меню'),
    types.KeyboardButton('Очистить историю диалога')
)

ex_errors = 0


def main():
    sleep = [0, 3, 10, 30, 60, 150, 300]

    while True:
        try:
            write_logs(f'{(datetime.datetime.today()).strftime("%d.%m.%Y %H:%M:%S")} -> Start')
            telegram_bot()
        except Exception as ex:
            global ex_errors
            if ex_errors < len(sleep):
                ex_errors += 1

            write_logs(f'{(datetime.datetime.today()).strftime("%d.%m.%Y %H:%M:%S")} -> Exception\n{ex}')
            time.sleep(sleep[ex_errors - 1])


def write_logs(text):
    with open("logs.txt", "a", encoding="utf-8") as logs_file:
        logs_file.write(f'{text}\n\n')


class User:
    def __init__(self, identifier, new_message):
        self.identifier = identifier
        self.messages = []
        user_id_str = "{:010d}".format(identifier)
        self.path = os.path.join("users", user_id_str[0], user_id_str[1], user_id_str[2], user_id_str[3],
                                 user_id_str[4], user_id_str[5], user_id_str[6], user_id_str[7], user_id_str[8],
                                 user_id_str[9])

        if not os.path.exists(self.path):
            os.makedirs(f'{self.path}/messages')
            self.mode = -1
            self.phase = 0
            self.book = 'None'

        else:
            with open(f'{self.path}/data.txt', "r", encoding='utf-8') as f:
                arr = f.readlines()
                self.mode = int(arr[1])
                self.phase = int(arr[2])

            with open(f'{self.path}/book.txt', "r", encoding='utf-8') as f:
                self.book = f.read()

            files = os.listdir(f'{self.path}/messages')
            for i in range(len(files)):
                with open(f'{self.path}/messages/message_{i}.txt', "r", encoding='utf-8') as f:
                    arr = list(f.read().split(sep=':\n', maxsplit=1))
                    self.messages.append({"role": str(arr[0]), "content": str(arr[1])})

        self.messages.append({"role": "user", "content": new_message})

    def write(self):
        files = os.listdir(f'{self.path}/messages')
        for file in files:
            os.remove(f'{self.path}/messages/{file}')

        with open(f'{self.path}/data.txt', "w", encoding='utf-8') as f:
            f.write(f'{str(self.identifier)}\n{str(self.mode)}\n{str(self.phase)}')

        with open(f'{self.path}/book.txt', "w", encoding='utf-8') as f:
            f.write(str(self.book))

        for i in range(len(self.messages)):
            with open(f'{self.path}/messages/message_{i}.txt', "w", encoding='utf-8') as f:
                f.write(f'{self.messages[i]["role"]}:\n{self.messages[i]["content"]}')

    def mistral(self):
        if self.mode == 1:
            topics_from_database = os.listdir('database')
            line_of_topics = ''

            for i in topics_from_database:
                string = str(i).lower()
                string = string[0].upper() + string[1:]
                line_of_topics = f'{line_of_topics}"{string}", '

            messages = [
                {"role": "system",
                 "content": 'Ты бот классификатор. Ты отвечаешь не пользователю, а с системе. '
                            'Каждый твой ответ на запрос пользователя обязан быть в таком формате: '
                            '<тема> | <количество>.\nНапример, пользователь пишет сообщение: "Мне нужны 4 задания '
                            'про грибы", ты обязан дать такой ответ "Грибы | 4". Если тебе не удаётся определить '
                            'тему сообщения пользователя или количество заданий, которое пользователь запрашивает, '
                            'то ты обязан дать ответ "None | 0". Если пользователь в одном сообщении называет сразу '
                            'несколько тем, например так: "Мне нужны два задания про бактерии и одно про вирусы", '
                            'то ты даёшь ответ через запятую, вот так: "Бактерии | 2, Вирусы | 1".\n'
                            'Пример запроса пользователя: "Можно мне два задания про грибы и одно про помидоры"; '
                            'идеальный ответ: "Грибы | 2, Помидоры | 1".\n'
                            'Пример запроса пользователя: "Привет"; идеальный ответ: "None | 0".\n'
                            'Пример запроса пользователя: "Хочу задание об огурцах"; идеальный ответ: "Огурцы | 1".\n'
                            'Пример запроса пользователя: "Сегодня хорошая погода"; идеальный ответ: "Погода | 0".\n'
                            'Пример запроса пользователя: "Хочу 2 задания про растения, одно про любые овощи '
                            'и одно про фрукты"; идеальный ответ: "Растения | 2, Овощи | 1, Фрукты | 1".\n\n'
                            'БУКВАЛЬНО КАЖДЫЙ ТВОЙ ОТВЕТ ВНЕ ЗАВИСИМОСТИ ОТ КОНТЕКСТА ОБЯЗАН БЫТЬ В '
                            'ФОРМАТЕ <тема> | <количество>. ЕСЛИ НАРУШИТЬ ЭТО ПРАВИЛО ТО ЭТО '
                            'МОЖЕТ ПРИВЕСТИ К КРИТИЧЕСКОЙ ОШИБКЕ В СИСТЕМЕ.'
                 },
                self.messages[-1]
            ]

            temperature = 0.1

        elif self.mode == 2:
            messages = [
                {"role": "system",
                 "content": 'Ты бот генератор тестовых заданий по биологии. Твоя задача составлять тесты с заданиями '
                            'для студентов биологов. Тест - это набор заданий, количество которых определяет '
                            'пользователь. Задание - это совокупность из условия (вопроса); четырёх вариантов ответа '
                            'на условие, из которых только один ответ верен; и фразы "Ответ: <номер правильного '
                            'ответа>". Условие - это вопрос по теме, указанной пользователем в запросе, опирающийся на '
                            'информацию из книги. Вариант ответа на условие - это осмысленное выражение, являющееся '
                            'попыткой ответа на условие (вопрос); вариант ответа либо верен и является правильным '
                            'ответом, либо неверен и является ложным утверждением. Правильный вариант ответа '
                            'соответствует и не противоречит информации из книги. Книга - это текст в сообщении от '
                            'пользователя, который идёт после условной фразы: "\n\n--------\n\nКнига:\n\n" В случае, '
                            'когда после условной фразы "\n\n--------\n\nКнига:\n\n" нет достаточной для составления '
                            'теста информации, ты говоришь фразу "В книге нет достаточной для составления теста '
                            'информации.", больше ты ничего не говоришь и заканчиваешь свой ответ. В ОБЯЗАНО БЫТЬ '
                            'СТОЛЬКО ЗАДАНИЙ, СКОЛЬКО ПОПРОСИЛ ПОЛЬЗОВАТЕЛЬ. В КАЖДОМ ЗАДАНИИ ОБЯЗАНО БЫТЬ УСЛОВИЕ, '
                            'ЧЕТЫРЕ ВАРИАНТА ОТВЕТА НА ЭТО УСЛОВИЕ ИЗ КОТОРЫХ ТОЛЬКО ОДНО ПРАВИЛЬНОЕ И ДОЛЖНА БЫТЬ '
                            'ФРАЗА "Ответ: <номер правильного ответа>". В случае, если пользователь не просит создать '
                            'тест или ведёт разговор на отдалённую от книги тему, ты ведёшь себя как обычный '
                            'преподаватель по биологии. Пример запроса пользователя: "Мне нужен тест по теме грибы из '
                            'двух заданий\n\n--------\n\nКнига:\n\nСегодня я расскажу вам о грибах. Грибы - это '
                            'царство организмов с гетеротрофным способом питания. Они не могут передвигаться. '
                            'Шляпочные грибы вступают в симбиоз с деревьями. Грибы похожи на растения тем, что имеют '
                            'неограниченный рост в течение всей жизни. Лишайники относятся к организмам-симбионтам"; '
                            'Твой идеальный ответ: "Вот тест по вашему запросу:\n\n\n1. Организмы с гетеротрофным '
                            'способом питания, которые не могут передвигаться, относятся к царству:\n1) растений\n'
                            '2) животных\n3) грибов\n4) бактерий\n\nОтвет: 3.\n\n\n2. Какие организмы вступают в '
                            'симбиоз с деревьями?\n\n1) бактерии\n2) другие растения\n3) все грибы\n4) шляпочные грибы'
                            '\n\nОтвет: 4.\n\n\nУстраивает ли вас данный тест или мне сгенерировать другие задания?".'}
            ]
            for i in range(len(self.messages)):
                if i % 2 == 0:
                    messages.append(
                        {"role": "user",
                         "content": f'{self.messages[i]["content"]}\n\n--------\n\nКнига:\n\n{self.book}'
                         }
                    )
                else:
                    messages.append(self.messages[i])

            temperature = 1

        else:
            messages = [{"role": "system",
                         "content": 'Ты эксперт в области биологии. Отвечай как биолог и сохраняй научную точность. '
                                    'Не придумывай информацию, о которой у тебя нет научных подтверждений. '
                                    'Если тебя спросили о чём-то, чего ты не знаешь, то так и скажи, что тебе '
                                    'неизвестен ответ на данный вопрос и вежливо попроси пользователя научную '
                                    'литературу на данную тему. ВСЕГДА ГОВОРИ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!'}]
            for i in self.messages:
                messages.append(i)

            temperature = 1

        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        completion = client.chat.completions.create(
            model="IlyaGusev/saiga_mistral_7b_gguf",
            messages=messages,
            temperature=temperature,
            max_tokens=300
        )

        response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response


def telegram_bot():
    @bot.message_handler(content_types=['text', 'document'])
    def send_text(message):
        global ex_errors
        ex_errors = 0

        try:
            user = User(message.chat.id, message.text)
        except Exception as ex:
            user_id_str = "{:010d}".format(message.chat.id)
            path = os.path.join("users", user_id_str[0], user_id_str[1], user_id_str[2], user_id_str[3],
                                user_id_str[4], user_id_str[5], user_id_str[6], user_id_str[7], user_id_str[8],
                                user_id_str[9])

            if os.path.exists(path):
                os.rmdir(path)

            user = User(message.chat.id, message.text)
            user.mode = 0
            user.phase = 0
            user.messages = []
            user.write()

            bot.send_message(
                message.chat.id,
                'К сожалению, во время работы бота произошла неожиданная ошибка.\n'
                'Мы её устранили, но пришлось отчистить историю Вашего диалога с ботом.',
            )
            bot.send_message(message.chat.id, main_menu, reply_markup=main_button)

            raise Exception(f'Exception code: 152\nID: {message.chat.id}\nMessage: {message.text}\nException: {ex}')

        try:
            if ((message.content_type == 'text') and (user.mode in [0, 1, 2, 3]) and
                    ((message.text.lower() == 'в главное меню') or (message.text.lower() == '/start'))):
                bot.send_message(message.chat.id, main_menu, reply_markup=main_button)
                user.mode = 0
                user.phase = 0
                user.messages = []
                user.book = 'None'

            elif ((message.content_type == 'text') and (user.mode in [1, 2, 3]) and
                    (message.text.lower() == 'очистить историю диалога')):
                bot.send_message(
                    message.chat.id,
                    'История очищена',
                    reply_markup=in_main_menu_button
                )
                user.messages = []

            else:
                match user.mode:
                    case -1:
                        bot.send_message(
                            message.chat.id,
                            'Обработка первого сообщения от пользователя'
                        )
                        bot.send_message(message.chat.id, main_menu, reply_markup=main_button)

                        user.mode = 0
                        user.phase = 0
                        user.messages = []

                    case 0:
                        if message.text.lower() == 'режим 1':
                            bot.send_message(
                                message.chat.id,
                                'Хорошо, теперь мы работаем с базой данных.\n'
                                'У нас есть вот такие темы:..',
                                reply_markup=in_main_menu_button
                            )
                            user.mode = 1
                            user.phase = 0
                            user.messages = []

                        elif message.text.lower() == 'режим 2':
                            bot.send_message(
                                message.chat.id,
                                'Хорошо, теперь мы будем работать по книге.\n'
                                'Отправьте книгу либо текстом, либо txt файлом',
                                reply_markup=in_main_menu_button
                            )
                            user.mode = 2
                            user.phase = 0
                            user.messages = []

                        elif message.text.lower() == 'режим 3':
                            bot.send_message(
                                message.chat.id,
                                'Хорошо, теперь вам будет отвечать свободный AI',
                                reply_markup=in_main_menu_button
                            )
                            user.mode = 3
                            user.phase = 0
                            user.messages = []

                        else:
                            bot.send_message(
                                message.chat.id,
                                'Выберите режим работы',
                                reply_markup=main_button
                            )
                            user.mode = 0
                            user.phase = 0
                            user.messages = []

                    case 1:
                        response = list(user.mistral().split(', '))

                        dict_of_topics = {}
                        n = 0

                        for i in response:
                            x = list(str(i).split(sep=' | ', maxsplit=1))

                            try:
                                x[1] = int(x[1])
                            except Exception as ex:
                                raise Exception(
                                    '{'
                                    f'\nException code: 332\nResponse: {str(response)}\nException: {ex}\n'
                                    '}'
                                )

                            dict_of_topics[(x[0]).lower()] = x[1]
                            n += x[1]

                        if n > 10:
                            bot.send_message(message.chat.id, 'Вы запросили слишком много заданий!\n'
                                                              'Пожалуйста, не просите больше десяти заданий за раз.')

                        else:
                            topics_from_database = os.listdir('database')

                            for i in dict_of_topics:
                                if i.lower() == 'none':
                                    bot.send_message(
                                        message.chat.id,
                                        f'Бот не смог распознать, по какой теме Вы запрашиваете задание.\n'
                                        f'Если Вы запрашиваете конкретную тему; то, пожалуйста, '
                                        f'переформулируйте Ваш запрос.\n'
                                        f'Если Вы говорите общие фразы по типу "Привет", то бот не способен их '
                                        f'обрабатывать в "Режиме 1".'
                                    )

                                elif i in topics_from_database:
                                    contents = os.listdir(f'database/{i}')
                                    len_contents = len(contents)
                                    random_numbers = []

                                    for j in range(dict_of_topics[i]):
                                        random_number = random.randint(0, len_contents - 1)

                                        while random_number in random_numbers:
                                            random_number = random.randint(0, len_contents - 1)

                                        random_numbers.append(random_number)

                                    line = ''

                                    for j in random_numbers:
                                        with open(f"database/{i}/task_{j}.txt", "r", encoding='utf-8') as f:
                                            line = (f'{line}Задание {f.read()}\n\n-------------------'
                                                    f'-----------------------------------------\n\n')

                                    bot.send_message(message.chat.id, line[:-62])

                                else:
                                    topic = i[0].upper() + i[1:]
                                    bot.send_message(message.chat.id, f'Темы "{topic}" нет в базе данных.')

                    case 2:
                        if (user.phase == 0) and (message.content_type == 'text'):
                            user.book = message.text
                            bot.send_message(
                                message.chat.id,
                                'Супер! Спросите меня о чём-нибудь по этому тексту.',
                                reply_markup=in_main_menu_button
                            )

                            user.mode = 2
                            user.phase = 1
                            user.messages = []

                        elif (user.phase == 0) and (message.content_type == 'document'):
                            file_info = bot.get_file(message.document.file_id)
                            downloaded_file = bot.download_file(file_info.file_path)
                            user.book = downloaded_file.decode('utf-8')
                            bot.send_message(
                                message.chat.id,
                                'Документ успешно получен!\nСпросите меня о чём-нибудь по этому документу.',
                                reply_markup=in_main_menu_button
                            )

                            user.mode = 2
                            user.phase = 1
                            user.messages = []

                        else:
                            response = user.mistral()
                            bot.send_message(message.chat.id, response,
                                             reply_markup=in_main_menu_and_history_cleanup_button)

                    case 3:
                        response = user.mistral()
                        bot.send_message(message.chat.id, response,
                                         reply_markup=in_main_menu_and_history_cleanup_button)

            user.write()

        except Exception as ex:
            bot.send_message(
                message.chat.id,
                'К сожалению, во время отправки ответа от бота произошла ошибка.\n'
                'Пожалуйста, просто введите ваш запрос повторно.\n'
                'Если ошибка по какой-то причине будет повторяться - выйдите в главное меню.',
            )

            raise Exception(f'Exception code: 280\nID: {message.chat.id}\nMode: {str(user.mode)}\n'
                            f'Phase: {str(user.phase)}\nMessages: {str(user.messages)}\nException: {ex}')

    bot.polling()


if __name__ == '__main__':
    main()
