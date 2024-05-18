import telebot
from telebot import types
import os
import datetime
import time
# import random
# from openai import OpenAI
# import requests
# import json


bot = telebot.TeleBot('6842595275:AAE6Iw_VjiEidw-geLaoMnDdV5I5S8FudWI')

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
    types.KeyboardButton('Отчистить историю диалога')
)

topics_from_database = os.listdir('database')
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
        # client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        # completion = client.chat.completions.create(
        #     model="IlyaGusev/saiga_mistral_7b_gguf",
        #     messages=messages,
        #     temperature=temperature,
        # )
        # response = completion.choices[0].message.content

        response = f'Mistral\n{str(self.messages[-1])}'

        self.messages.append({"role": "assistant", "content": response})
        return response


def telegram_bot():
    @bot.message_handler(content_types=['text', 'document'])
    def send_text(message):
        def exception():
            user_id_str = "{:010d}".format(message.chat.id)
            path = os.path.join("users", user_id_str[0], user_id_str[1], user_id_str[2], user_id_str[3],
                                user_id_str[4], user_id_str[5], user_id_str[6], user_id_str[7], user_id_str[8],
                                user_id_str[9])

            if os.path.exists(path):
                os.rmdir(path)

            ex_user = User(message.chat.id, message.text)
            ex_user.mode = 0
            ex_user.write()

            bot.send_message(
                message.chat.id,
                'К сожалению, во время работы бота произошла неожиданная ошибка.\n'
                'Мы её устранили, но пришлось отчистить историю Вашего диалога с ботом.',
            )
            bot.send_message(message.chat.id, main_menu, reply_markup=main_button)

        global ex_errors
        ex_errors = 0

        try:
            user = User(message.chat.id, message.text)
        except Exception as ex:
            ex = f'Exception 244\nid: {message.chat.id}\nmessage: {message.text}\nex: {ex}'
            exception()
            raise Exception(ex)

        try:
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
                    if message.text.lower() == 'в главное меню':
                        bot.send_message(message.chat.id, main_menu, reply_markup=main_button)
                        user.mode = 0
                        user.phase = 0
                        user.messages = []

                    elif message.text.lower() == 'отчистить историю диалога':
                        bot.send_message(
                            message.chat.id,
                            'История отчищена',
                            reply_markup=in_main_menu_button
                        )
                        user.messages = []

                    else:
                        response = user.mistral()
                        bot.send_message(message.chat.id, response,
                                         reply_markup=in_main_menu_and_history_cleanup_button)

                case 2:

                    match user.phase:
                        case 0:
                            if message.content_type == 'text' and message.text.lower() != 'в главное меню':
                                user.book = message.text
                                bot.send_message(
                                    message.chat.id,
                                    'Супер! Спросите меня о чём-нибудь по этому тексту.',
                                    reply_markup=in_main_menu_button
                                )

                                user.mode = 2
                                user.phase = 1
                                user.messages = []

                            elif message.content_type == 'document':
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
                                bot.send_message(message.chat.id, main_menu, reply_markup=main_button)
                                user.mode = 0
                                user.phase = 0
                                user.messages = []

                        case 1:
                            if message.text.lower() == 'в главное меню':
                                bot.send_message(message.chat.id, main_menu, reply_markup=main_button)
                                user.mode = 0
                                user.phase = 0
                                user.messages = []
                                user.book = 'None'

                            elif message.text.lower() == 'отчистить историю диалога':
                                bot.send_message(
                                    message.chat.id,
                                    'История отчищена',
                                    reply_markup=in_main_menu_button
                                )
                                user.messages = []

                            else:
                                response = user.mistral()
                                bot.send_message(message.chat.id, response,
                                                 reply_markup=in_main_menu_and_history_cleanup_button)

                case 3:
                    if message.text.lower() == 'в главное меню':
                        bot.send_message(message.chat.id, main_menu,
                                         reply_markup=main_button)
                        user.mode = 0
                        user.phase = 0
                        user.messages = []

                    elif message.text.lower() == 'отчистить историю диалога':
                        bot.send_message(
                            message.chat.id,
                            'История отчищена',
                            reply_markup=in_main_menu_button
                        )
                        user.messages = []

                    else:
                        response = user.mistral()
                        bot.send_message(message.chat.id, response,
                                         reply_markup=in_main_menu_and_history_cleanup_button)

            user.write()

        except Exception as ex:
            ex = (f'Exception 245\nid: {str(user.identifier)}\nmessages: {str(user.messages)}'
                  f'\nmode: {str(user.mode)}\nphase: {str(user.phase)}\nex: {ex}')
            exception()
            raise Exception(ex)

    bot.polling()


if __name__ == '__main__':
    main()
