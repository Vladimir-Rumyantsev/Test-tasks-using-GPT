import telebot
from telebot import types
import os
import datetime
import time
import random
from openai import OpenAI

bot = telebot.TeleBot('TOKEN')

main_menu = ('Добро пожаловать в главное меню! Здесь Вы сможете выбрать наиболее подходящий для себя режим работы, '
             'исходя из Ваших целей и задач по генерации тестов по биологии.\nКаждый доступный режим представлен в '
             'виде кнопки для Вашего удобства.\n\nВ режиме 1 - Вы взаимодействуете с базой данных заданий\n'
             'В режиме 2 - Вы можете отправить собственную небольшую статью и бот постарается создать по ней задания\n'
             'В режиме 3 - Вы взаимодействуете с ботом в стандартном режиме\n\nТак же, в любой момент работы бота '
             'Вы можете отправить txt-файл со статьёй, которая после изучения разработчиками будет использоваться '
             'для улучшения знаний бота в Вашей сфере.')

start_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_button.add(types.KeyboardButton('/start'))

main_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_button.add(
    types.KeyboardButton('Режим 1'),
    types.KeyboardButton('Режим 2'),
    types.KeyboardButton('Режим 3'),
    types.KeyboardButton('Связаться с поддержкой')
)

in_main_menu_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
in_main_menu_button.add(
    types.KeyboardButton('В главное меню')
)

in_main_menu_and_last_book_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
in_main_menu_and_last_book_button.add(
    types.KeyboardButton('В главное меню'),
    types.KeyboardButton('Использовать прошлую книгу')
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

    def mistral(self) -> list[str]:
        if self.mode == 1:
            return self.mistral_mode_1()

        elif self.mode == 2:
            return self.mistral_mode_2()

        else:
            return self.mistral_mode_3()

    def mistral_mode_1(self) -> list[str]:
        topics_from_database = os.listdir('database')

        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        completion = client.chat.completions.create(
            model="IlyaGusev/saiga_mistral_7b_gguf",
            messages=[
                {"role": "system",
                 "content": 'Ты бот классификатор. Ты отвечаешь не пользователю, а с системе. '
                            'Каждый твой ответ на запрос пользователя обязан быть в таком формате: '
                            '<тема> | <количество>.\nНапример, пользователь пишет сообщение: "Мне нужны 4 задания '
                            'про грибы", ты обязан дать такой ответ "Грибы | 4". Если тебе не удаётся определить '
                            'тему сообщения пользователя или количество заданий, которое пользователь запрашивает, '
                            'то ты обязан дать ответ "None | 0". Если пользователь в одном сообщении называет '
                            'сразу несколько тем, например так: "Мне нужны два задания про бактерии и одно про '
                            'вирусы", то ты даёшь ответ через запятую, вот так: "Бактерии | 2, Вирусы | 1".\n'
                            'Пример запроса пользователя: "Можно мне два задания про грибы и одно про помидоры"; '
                            'идеальный ответ: "Грибы | 2, Помидоры | 1".\n'
                            'Пример запроса пользователя: "Привет"; идеальный ответ: "None | 0".\n'
                            'Пример запроса пользователя: "Хочу задание об огурцах"; '
                            'идеальный ответ: "Огурцы | 1".\n'
                            'Пример запроса пользователя: "Сегодня хорошая погода"; '
                            'идеальный ответ: "Погода | 0".\n'
                            'Пример запроса пользователя: "Хочу 2 задания про растения, одно про любые овощи '
                            'и одно про фрукты"; идеальный ответ: "Растения | 2, Овощи | 1, Фрукты | 1".\n\n'
                            'БУКВАЛЬНО КАЖДЫЙ ТВОЙ ОТВЕТ ВНЕ ЗАВИСИМОСТИ ОТ КОНТЕКСТА ОБЯЗАН БЫТЬ В '
                            'ФОРМАТЕ <тема> | <количество>. ЕСЛИ НАРУШИТЬ ЭТО ПРАВИЛО ТО ЭТО '
                            'МОЖЕТ ПРИВЕСТИ К КРИТИЧЕСКОЙ ОШИБКЕ В СИСТЕМЕ.'
                 },
                self.messages[-1]
            ],
            temperature=0.1,
            max_tokens=150
        )

        response = list(completion.choices[0].message.content.split(', '))

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
            response = 'Вы запросили слишком много заданий!\nПожалуйста, не просите больше десяти заданий за раз.'
            self.messages.append({"role": "assistant", "content": response})
            return [response]

        else:
            response_messages = []

            for i in dict_of_topics:
                if i.lower() == 'none':
                    response = (
                        f'Я не смог распознать, по какой теме Вы запрашиваете задание.\n'
                        f'Если Вы запрашиваете конкретную тему; '
                        f'то, пожалуйста, переформулируйте Ваш запрос.\n'
                        f'Если Вы говорите общие фразы по типу "Привет", '
                        f'то я не способен их обрабатывать в "Режиме 1".'
                    )
                    self.messages.append({"role": "assistant", "content": response})
                    return [response]

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
                        with open(f"database/{i}/{contents[j]}", "r", encoding='utf-8') as f:
                            line = (f'{line}{f.read()}\n\n-------------------'
                                    f'-----------------------------------------\n\n')

                    response_messages.append(line[:-62])

                else:
                    topic = i[0].upper() + i[1:]
                    response_messages.append(f'Темы "{topic}" нет в базе данных.')

            for i in response_messages:
                self.messages.append({"role": "assistant", "content": i})

            return response_messages

    def mistral_mode_2(self) -> list[str]:
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
                        'соответствует и не противоречит информации из книги. Книга - это текст, который указан '
                        'ниже. В случае, когда в книге нет достаточной для составления '
                        'теста информации, ты говоришь фразу "В книге нет достаточной для составления теста '
                        'информации.", больше ты ничего не говоришь и заканчиваешь свой ответ. В ТЕСТЕ ОБЯЗАНО '
                        'БЫТЬ СТОЛЬКО ЗАДАНИЙ, СКОЛЬКО ПОПРОСИЛ ПОЛЬЗОВАТЕЛЬ. В КАЖДОМ ЗАДАНИИ ОБЯЗАНО БЫТЬ УСЛОВИЕ, '
                        'ЧЕТЫРЕ ВАРИАНТА ОТВЕТА НА ЭТО УСЛОВИЕ ИЗ КОТОРЫХ ТОЛЬКО ОДНО ПРАВИЛЬНОЕ И ДОЛЖНА БЫТЬ '
                        'ФРАЗА "Ответ: <номер правильного ответа>". В случае, если пользователь не просит создать '
                        'тест или ведёт разговор на отдалённую от книги тему, ты ведёшь себя как обычный '
                        'преподаватель по биологии.\n\n'


                        'Пример книги: "Сегодня я расскажу вам о грибах. Грибы - это '
                        'царство организмов с гетеротрофным способом питания. Они не могут передвигаться. '
                        'Шляпочные грибы вступают в симбиоз с деревьями. Грибы похожи на растения тем, что имеют '
                        'неограниченный рост в течение всей жизни. Лишайники относятся к организмам-симбионтам.".\n'

                        'Пример запроса пользователя: "Мне нужен тест по теме грибы из двух заданий".\n'

                        'Твой идеальный ответ: "Вот тест по вашему запросу:\n\n\n1. Организмы с гетеротрофным '
                        'способом питания, которые не могут передвигаться, относятся к царству:\n1) растений\n'
                        '2) животных\n3) грибов\n4) бактерий\n\nОтвет: 3.\n\n\n2. Какие организмы вступают в '
                        'симбиоз с деревьями?\n\n1) бактерии\n2) другие растения\n3) все грибы\n4) шляпочные грибы'
                        '\n\nОтвет: 4.\n\n\nУстраивает ли вас данный тест или мне сгенерировать другие задания?".\n\n'


                        'Пример книги: "Вчера была ясная погода".\n'
                        'Пример запроса пользователя: "Мне нужны 3 задания".\n'
                        'Твой идеальный ответ: "В книге нет достаточной для составления теста информации.".\n\n'

                        'Пример книги: "Привет".\n'
                        'Пример запроса пользователя: "Можно 3 задания?".\n'
                        'Твой идеальный ответ: "В книге нет достаточной для составления теста информации.".\n\n'


                        'Пример книги: "Виды облаков и их значение:\n1. Кучевые облака: Показывают ясную погоду.\n'
                        '2. Кучево-дождевые облака: Предвестники сильных дождей.\n'
                        '3. Перистые облака: Сигнал приближающегося тёплого фронта и дождя.\n'
                        '4. Слоистые облака: Могут принести морось, но редко сильный дождь.\n'
                        '5. Лентикулярные облака: Свидетельство сложных атмосферных движений, '
                        'не связанных с погодой.\n6. Облака Кельвина — Гельмгольца: '
                        'Редкие, но интересные облака, указывающие на нестабильность воздушных масс.".\n'

                        'Пример запроса пользователя: "Мне нужны 3 заданий из книги".\n'

                        'Твой идеальный ответ: "Какие облака указывают на ясную погоду?\n'
                        '1) Кучевые облака\n2) Кучево-дождевые облака\n3) Перистые облака\n'
                        '4) Слоистые облака\n5) Лентикулярные облака\n6) Облака Кельвина — Гельмгольца\n'
                        'Ответ: 1.\n\nКакие облака могут принести морось, но редко сильный дождь?\n'
                        '1) Кучевые облака\n2) Кучево-дождевые облака\n3) Перистые облака\n'
                        '4) Слоистые облака\n5) Лентикулярные облака\n6) Облака Кельвина — Гельмгольца\n'
                        'Ответ: 4.\n\nКакие облака указывают на нестабильность воздушных масс?\n'
                        '1) Кучевые облака\n2) Кучево-дождевые облака\n3) Перистые облака\n'
                        '4) Слоистые облака\n5) Лентикулярные облака\n6) Облака Кельвина — Гельмгольца\n'
                        'Ответ: 6.".\n\n'


                        'Пример книги: "В настоящее время существует очень много наук, изучающих животных. '
                        'Например: этология – наука о поведении животных; энтомология – о насекомых; ихтиология – '
                        'о рыбах; орнитология – о птицах и т. д.  Зоология имеет области пересечения со многими '
                        'биологическими науками. Так, существуют, например, экология животных и генетика животных. '
                        'Зоологию и географию объединяет зоогеография – наука о закономерностях распространения и '
                        'распределения животных на Земле. Строением тела и отдельных органов растений, животных и '
                        'человека занимается наука морфология, а их функциями – наука физиология. Морфология и '
                        'физиология животных тесно связаны с зоологией."\n'

                        'Пример запроса пользователя: "сделай 1 тестовое задание про науки о животных".\n'

                        'Твой идеальный ответ: "Какая из перечисленных наук исследует поведение животных?\n'
                        '1) этология\n2) экология животных\n3) морфология\n4) ихтиология\nОтвет: 1."\n\n'


                        'Пример книги: "В настоящее время существует очень много наук, изучающих животных. '
                        'Например: этология – наука о поведении животных; энтомология – о насекомых; ихтиология – '
                        'о рыбах; орнитология – о птицах и т. д.  Зоология имеет области пересечения со многими '
                        'биологическими науками. Так, существуют, например, экология животных и генетика животных. '
                        'Зоологию и географию объединяет зоогеография – наука о закономерностях распространения и '
                        'распределения животных на Земле. Строением тела и отдельных органов растений, животных и '
                        'человека занимается наука морфология, а их функциями – наука физиология. Морфология и '
                        'физиология животных тесно связаны с зоологией."\n'

                        'Пример запроса пользователя: "сгенерируй 2 задания по тексту".\n'

                        'Твой идеальный ответ: "1. Какая из следующих наук изучает функции организмов животных?\n'
                        '1) энтомология\n2) физиология\n3) морфология\n4) ихтиология\nОтвет: 2.\n\n2. Какая из '
                        'следующих наук изучает распространение и распределение животных на Земле?\n'
                        '1) энтомология\n2) зоогеография\n3) орнитология\n4) физиология\nОтвет: 2."\n\n'
                        
                        f'КНИГА, ПО КОТОРОЙ ТЫ ОБЯЗАН СОСТАВЛЯТЬ ЗАДАНИЯ В ЭТОМ ДИАЛОГЕ:\n\n{self.book}'
             }
        ]
        for i in self.messages:
            messages.append(i)

        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        completion = client.chat.completions.create(
            model="IlyaGusev/saiga_mistral_7b_gguf",
            messages=messages,
            temperature=0.8,
            max_tokens=300
        )

        response = str(completion.choices[0].message.content)
        self.messages.append({"role": "assistant", "content": response})
        return [response]

    def mistral_mode_3(self) -> list[str]:
        messages = [{
            "role": "system",
            "content": 'Ты эксперт в области биологии. Отвечай как биолог и сохраняй научную точность. '
                       'Если тебя спросили о чём-то, чего ты не знаешь, то так и скажи, что тебе '
                       'неизвестен ответ на данный вопрос и вежливо попроси пользователя отправить научную '
                       'литературу на данную тему в виде txt-файла. ВСЕГДА ГОВОРИ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!'
        }]
        for i in self.messages:
            messages.append(i)

        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        completion = client.chat.completions.create(
            model="IlyaGusev/saiga_mistral_7b_gguf",
            messages=messages,
            temperature=1,
            max_tokens=200
        )

        response = str(completion.choices[0].message.content)
        self.messages.append({"role": "assistant", "content": response})
        return [response]


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

            elif ((message.content_type == 'text') and (user.mode in [1, 2, 3]) and
                  (message.text.lower() == 'очистить историю диалога')):
                bot.send_message(
                    message.chat.id,
                    'История очищена',
                    reply_markup=in_main_menu_button
                )
                user.messages = []

            elif ((user.mode != 2) or (user.phase != 0)) and (message.content_type == 'document'):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                book = str(downloaded_file.decode('utf-8'))

                bot.send_message(
                    message.chat.id,
                    'Спасибо большое, я обязательно ознакомлюсь с данным документом.\n'
                    'Такие статьи помогают мне становиться умнее.'
                )

                if not os.path.exists(f'booksFromUsers'):
                    os.makedirs(f'booksFromUsers')

                with open(str(f'booksFromUsers/{user.identifier}_'
                              f'{(datetime.datetime.today()).strftime("%d.%m.%Y_%H.%M.%S")}.txt'),
                          "w", encoding='utf-8') as f:
                    f.write(book)

            else:
                match user.mode:
                    case -1:
                        bot.send_message(
                            message.chat.id,
                            "Добро пожаловать в telegram-бот, разработанный в помощь преподавателям биологии "
                            "для генерации тестовых заданий для студентов. Бот предлагает три режима работы, "
                            "каждый из которых имеет уникальные особенности, адаптированные к различным "
                            "потребностям преподавателей.\n\nРежим 1:\nТесты из базы данных\nЭтот режим позволяет "
                            "извлекать тестовые задания из обширной базы данных. Пользователям предоставляется "
                            "доступ к широкому спектру вопросов, охватывающих многие аспекты учебной программы по "
                            "биологии.\n\nРежим 2:\nГенерирование тестов из предоставленного текста\nВ этом режиме "
                            "преподаватели могут загружать учебные материалы, такие как книги или статьи, в бота. "
                            "На основании полученных данных, бот создает тесты, согласно предоставленной информации\n\n"
                            "Режим 3:\nСвободная AI\nЭтот режим предоставляет преподавателям возможность свободно "
                            "взаимодействовать с ботом, как с обычным помощником на основе AI."
                        )
                        bot.send_message(message.chat.id, main_menu, reply_markup=main_button)

                        user.mode = 0
                        user.phase = 0
                        user.messages = []

                    case 0:
                        if message.text.lower() == 'режим 1':

                            topics_from_database = os.listdir('database')
                            line = ''
                            for i in topics_from_database:
                                line = f'{line}• {i[0].upper() + i[1:]}\n'

                            bot.send_message(
                                message.chat.id,
                                'Вы зашли в Режим 1.\nВ данном режиме я работаю по своей базе данных. '
                                'Введите запрос в свободном формате, в котором запрашиваете задания по определённой '
                                'теме, например так: "Выдай 3 задания про грибы".\n\n'
                                f'Темы, которые есть в моей базе данных:\n\n{line}',
                                reply_markup=in_main_menu_button
                            )
                            user.mode = 1
                            user.phase = 0
                            user.messages = []

                        elif message.text.lower() == 'режим 2':
                            if user.book.lower() == 'none':
                                bot.send_message(
                                    message.chat.id,
                                    'Вы зашли в Режим 2.\nВ данном режиме Вы можете прислать мне свою информацию; '
                                    'опираясь на неё, я буду генерировать задания для Ваших тестов.\nПришлите сейчас '
                                    'мне txt-файл или текстовое сообщение, с которым мне предстоит работать.',
                                    reply_markup=in_main_menu_button
                                )
                            else:
                                bot.send_message(
                                    message.chat.id,
                                    'Вы зашли в Режим 2.\nВ данном режиме Вы можете прислать мне свою информацию; '
                                    'опираясь на неё, я буду генерировать задания для Ваших тестов.\nПришлите сейчас '
                                    'мне txt-файл или текстовое сообщение, с которым мне предстоит работать, '
                                    'или воспользуйтесь кнопкой "Использовать прошлую книгу", чтобы я работал по Вашей '
                                    'прошлой информации.',
                                    reply_markup=in_main_menu_and_last_book_button
                                )

                            user.mode = 2
                            user.phase = 0
                            user.messages = []

                        elif message.text.lower() == 'режим 3':
                            bot.send_message(
                                message.chat.id,
                                'Вы зашли в Режим 3.\nВ данном режиме я веду свободный стиль общения. '
                                'Просто введите Ваш запрос.',
                                reply_markup=in_main_menu_button
                            )
                            user.mode = 3
                            user.phase = 0
                            user.messages = []

                        elif message.text.lower() == 'связаться с поддержкой':
                            bot.send_message(
                                message.chat.id,
                                'Контакты поддержки:\n'
                                'https://t.me/VladimirRumyantsev\n'
                                'https://t.me/LyutyChyort\n'
                                'https://t.me/kystikikolychie\n'
                                'https://t.me/Lisiy_Svet\n'
                                'https://t.me/MrDevilI\n'
                                'Чтобы поддержать разработчиков финансово, напишите одному из контактов',
                                reply_markup=main_button
                            )
                            user.mode = 0
                            user.phase = 0
                            user.messages = []

                        else:
                            bot.send_message(
                                message.chat.id,
                                'Пожалуйста, выберите режим работы бота.',
                                reply_markup=main_button
                            )
                            user.mode = 0
                            user.phase = 0
                            user.messages = []

                    case 1:
                        response = user.mistral()
                        for i in response:
                            bot.send_message(message.chat.id, i,
                                             reply_markup=in_main_menu_and_history_cleanup_button)

                    case 2:
                        if (user.phase == 0) and (message.content_type == 'text'):
                            if message.text.lower() != 'использовать прошлую книгу':
                                user.book = message.text

                            bot.send_message(
                                message.chat.id,
                                'Супер!\nТеперь задайте мне запрос в похожей форме: '
                                '"Выдай мне N заданий, с X вариантами ответа, по теме Y".',
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
                                'Супер! Документ успешно получен!\nТеперь задайте мне запрос в похожей форме: '
                                '"Выдай мне N заданий, с X вариантами ответа, по теме Y".',
                                reply_markup=in_main_menu_button
                            )

                            user.mode = 2
                            user.phase = 1
                            user.messages = []

                        else:
                            bot.send_message(message.chat.id, 'Ваш запрос в очереди. Подождите, пожалуйста!')
                            response = user.mistral()
                            for i in response:
                                bot.send_message(message.chat.id, i,
                                                 reply_markup=in_main_menu_and_history_cleanup_button)

                    case 3:
                        response = user.mistral()
                        for i in response:
                            bot.send_message(message.chat.id, i,
                                             reply_markup=in_main_menu_and_history_cleanup_button)

            user.write()

        except Exception as ex:
            bot.send_message(
                message.chat.id,
                'К сожалению, произошла неожиданная ошибка.\n'
                'Пожалуйста, попробуйте ввести Ваш запрос повторно, '
                'если ошибка по какой-либо причине будет повторяться - выйдите в главное меню, Вашу проблему изучат '
                'мои разработчики.',
            )

            raise Exception(f'Exception code: 280\nID: {message.chat.id}\nMode: {str(user.mode)}\n'
                            f'Phase: {str(user.phase)}\nMessages: {str(user.messages)}\nException: {ex}')

    bot.polling()


if __name__ == '__main__':
    main()
