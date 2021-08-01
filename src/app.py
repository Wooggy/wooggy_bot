import os
from string import ascii_lowercase
from random import choice

import telebot
from telebot import types
from flask import Flask, request

from key_unpacker import get_from_env
from hotels import hotels

# app init

API_TOKEN = get_from_env('API_TOKEN')
secret = ''.join([choice(ascii_lowercase) for _ in range(10)])
url = f"<your url>/{secret}"

bot = telebot.TeleBot(API_TOKEN, threaded=False)
bot.remove_webhook()
bot.set_webhook(url=url)

app = Flask(__name__)


@app.route(f'/{secret}', methods=["POST"])
def webhook() -> tuple:

    """Set webhook with Flask app"""

    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# app logic

users = {}


class User:

    """User class"""

    def __init__(self, message: types.Message) -> None:
        self.message = message

    def __str__(self) -> str:
        return f'{self.message.chat.id}: {self.message.chat.first_name} {self.message.chat.last_name}'


def sticker_pusher(message: types.Message, file_name: str) -> int:

    """Send sticker to chat"""

    st_path = os.path.join(os.path.abspath('../stickers'), file_name)
    with open(st_path, 'rb') as st:
        msg = bot.send_sticker(message.chat.id, st)
    return msg.id


@bot.message_handler(content_types=['text'])
def user_connection(message: types.Message) -> None:

    user = User(message)
    users.update({message.chat.id: user})
    message = user.message

    if message.text == '/start':
        start_command(message)
    elif message.text == '/help':
        help_command(message)
    elif message.text == '/lowprice':
        low_price_command(message)
    elif message.text == '/highprice':
        high_price_command(message)
    elif message.text == '/bestdeal':
        best_deal_command(message)
    else:
        bot.send_message(message.chat.id, 'Use the /help command')


@bot.message_handler()
def start_command(message: types.Message) -> None:

    """Send start command"""

    sticker_pusher(message, 'hello.webp')
    bot.send_message(message.chat.id, f'Hello {message.chat.first_name}!\n\n'
                                      f'Choose a command:\n'
                                      f'/lowprice 🔑 Top cheapest hotels in the city\n'
                                      f'/highprice 💎 Top most expensive hotels in the city\n'
                                      f'/bestdeal 🎯 Detailed selection')


@bot.message_handler()
def help_command(message: types.Message) -> None:

    """Send information about commands"""

    bot.send_message(message.chat.id, f'/lowprice 🔑 Top cheapest hotels in the city\n'
                                      f'/highprice 💎 Top most expensive hotels in the city\n'
                                      f'/bestdeal 🎯 Detailed selection')


@bot.message_handler()
def low_price_command(message: types.Message) -> None:

    """
    Start searching for cheap deals.

    Out: data = {'command': 'lowprice', 'step': 'select_city'}
    """

    data = {'command': 'lowprice'}
    data.update({'step': 'select_city'})
    sticker_pusher(message, 'lowprice.webp')
    msg = bot.send_message(message.chat.id, 'Looking for cheaper options...🔎\nEnter city:')
    bot.register_next_step_handler(msg, waiting, data)


@bot.message_handler()
def high_price_command(message: types.Message) -> None:

    """
    Start searching for expensive deals.

    Out: data = {'command': 'highprice', 'step': 'select_city'}
    """

    data = {'command': 'highprice'}
    data.update({'step': 'select_city'})
    sticker_pusher(message, 'highprice.webp')
    msg = bot.send_message(message.chat.id, 'Looking for more expensive options...🔎\nEnter city:')
    bot.register_next_step_handler(msg, waiting, data)


@bot.message_handler()
def best_deal_command(message: types.Message) -> None:

    """
    Start detailed selection.

    Out: data = {'command': 'bestdeal', 'step': 'select_city'}
    """

    data = {'command': 'bestdeal'}
    data.update({'step': 'select_city'})
    sticker_pusher(message, 'bestdeal.webp')
    msg = bot.send_message(message.chat.id, 'Looking for the best options...🔎\nEnter city:')
    bot.register_next_step_handler(msg, waiting, data)


def waiting(message: types.Message, data: dict) -> None:

    """
    Send waiting sticker.

    Input: data = {"step": <str>}
    Out: data = {"waiting_msg_id": <int>}
    """

    msg = sticker_pusher(message, 'waiting.tgs')
    data.update({"waiting_msg_id": msg})
    if data['step'] == 'select_city':
        select_city_step(message, data)
    elif data['step'] == 'result':
        result_step(message, data)


def string_compressor(text: str, byte: int) -> str:

    """String compressor"""

    while len(text.encode('utf-8')) >= byte:
        text = text[:-1]
    return text


def select_city_step(message: types.Message, data: dict) -> None:

    """
    Create neighborhood callback buttons.

    Input: data = {"command": <str>, "waiting_msg_id": <int>}
    Out: callback_data = "<command data> <destination id> <neighborhood name>"
    """

    neighborhoods = hotels.select_city(message.text)
    if neighborhoods:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for btn_name, destination_id in neighborhoods.items():
            callback_string = string_compressor(f'{data["command"][0]} {destination_id} {btn_name}', 64)
            markup.add(
                types.InlineKeyboardButton(text=btn_name, callback_data=callback_string))
        bot.send_message(message.chat.id, text=f'Select neighborhood: ', reply_markup=markup)
        bot.delete_message(message.chat.id, data["waiting_msg_id"])
    else:
        bot.delete_message(message.chat.id, data["waiting_msg_id"])
        bot.send_message(message.chat.id, 'Invalid input')
        if data["command"] == 'lowprice':
            low_price_command(message)
        elif data["command"] == 'highprice':
            high_price_command(message)
        elif data["command"] == 'bestdeal':
            best_deal_command(message)


@bot.callback_query_handler(func=lambda call: True)
def select_city_step_callback(call: types.CallbackQuery) -> None:

    """
    Callback from neighborhood buttons.

    Input: callback_data = "<command data> <destination id> <neighborhood name>"
    Out: data = {"command": <str>, "result": <dict>}
    """

    full_name_command = {'l': 'lowprice', 'h': 'highprice', 'b': 'bestdeal'}
    call_data = call.data.split()
    neighborhood_name = ' '.join(call_data[2:])
    data = {"result": {"destinationId": call_data[1]}}
    data.update({"command": full_name_command[call_data[0]]})

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text=f'Selected neighborhood: {neighborhood_name}')

    if data["command"] in ['lowprice', 'highprice']:
        if data["command"] == 'highprice':
            data["result"].update({"sortOrder": "PRICE_HIGHEST_FIRST"})
        day_qty_step(call.message, data)
    elif data["command"] == 'bestdeal':
        price_range_step(call.message, data)


def error_message(message: types.Message) -> None:

    """Send message about syntax error"""

    bot.send_message(message.chat.id, f'Syntax error: ❗{message.text}❗\nDefault parameters used')


def price_range_step(message: types.Message, data: dict) -> None:

    """
    Data collection for hotels API.

    Out: data = {"result":
                            "priceMax": <int>,
                            "priceMin": <int>}
    """

    msg = bot.send_message(message.chat.id, 'Enter price range\nExample: 257 2000')
    bot.register_next_step_handler(msg, landmark_step, data)


def landmark_step(message: types.Message, data: dict) -> None:

    """
    Data collection for hotels API.

    Input: data = {"result":
                            "priceMax": <int>,
                            "priceMin": <int>}
    Out: data = {"landmarkIds": <str>}
    """

    price_range = message.text.split()
    if all([i.isdigit() for i in price_range]):
        data["result"].update({"priceMax": int(max(price_range))})
        data["result"].update({"priceMin": int(min(price_range))})
    else:
        error_message(message)
    msg = bot.send_message(message.chat.id, 'Enter the max distance from the center\nExample: 5')
    bot.register_next_step_handler(msg, day_qty_step, data)


def day_qty_step(message: types.Message, data: dict) -> None:

    """
    Data collection for hotels API.

    Input: data = {"result": "landmarkIds": <str>}
                    or "result": "sortOrder": "PRICE_HIGHEST_FIRST"
                    or None
    Out: data = {"result": "days": <int>}
    """

    if data["command"] == 'bestdeal':
        if message.text.isdigit():
            data["result"].update({"landmarkIds": f'{message.text} miles'})
        else:
            error_message(message)

    msg = bot.send_message(message.chat.id, 'How many days are you planning to rent?\nExample: 7')
    bot.register_next_step_handler(msg, hotels_qty_step, data)


def hotels_qty_step(message: types.Message, data: dict) -> None:

    """
    Data collection for hotels API.

    Input: data = {"result": "days": <int>}
    Out: data = {'step': 'result'}
    """

    data.update({'step': 'result'})
    n = message.text
    if n.isdigit():
        if int(n) > 28:
            n = 28
    else:
        n = 1
        error_message(message)
    data["result"].update({"days": int(n)})
    msg = bot.send_message(message.chat.id, 'How many hotels to show?\nExample: 10')
    bot.register_next_step_handler(msg, waiting, data)


def result_step(message: types.Message, data: dict) -> None:

    """
    Show the end result.

    Input: data = {"result": "pageSize": <int>, "waiting_msg_id": <int>}
    """

    if message.text.isdigit():
        if int(message.text) > 25:
            data["result"].update({"pageSize": '25'})
        else:
            data["result"].update({"pageSize": message.text})
    else:
        error_message(message)

    out = hotels.result(data["result"])
    bot.delete_message(message.chat.id, data["waiting_msg_id"])
    if not out:
        bot.send_message(message.chat.id, 'Oops... There are no results for your requests...')
        sticker_pusher(message, 'no_results.webp')
    for hotel in out:
        bot.send_message(message.chat.id, hotel['info'])
        bot.send_location(message.chat.id, latitude=hotel['location']['lat'], longitude=hotel['location']['lon'])
    help_command(message)
