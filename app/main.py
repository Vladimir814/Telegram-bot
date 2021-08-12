from flask import Flask, request, jsonify
import requests
import json
import re


from flask_sslify import SSLify
from config import TOKEN, COINMARKETCAP_API_KEY


app = Flask(__name__)
sslify = SSLify(app)

URL = f'https://api.telegram.org/bot{TOKEN}/'


def send_message(chat_id, text='bot greets you'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=answer)


def get_currency_name(text):
    '''
    Парсим название криптовалюты из входящщего сообщения пользователя
    '''

    template = r'/\w+\-?\w+'
    name = re.findall(template, text)
    if len(name) > 0:
        return name[0][1:].lower()
    return 'name'


def get_currency_price(currency_name):
    '''
    Определяем стоимость указанной криптовалюты
    '''
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {'slug': f'{currency_name}', 'convert': 'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': f'{COINMARKETCAP_API_KEY}'}

    session = requests.Session()
    session.headers.update(headers)
    
    respons = session.get(url, params=parameters)
    d = json.loads(respons.text)['data']
    currency_id = list(d)[0]
    currency_price = json.loads(respons.text)['data'][f'{currency_id}']['quote']['USD']['price']
    return currency_price


def get_all_currencys_name():
    '''
    Получаем список всех криптовалют указанных на сайте
    '''
    all_currencys = []
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': f'{COINMARKETCAP_API_KEY}'}

    session = requests.Session()
    session.headers.update(headers)
    respons = session.get(url)
    result = json.loads(respons.text)['data']
    for currency in result:
        name = currency['slug']
        if name not in all_currencys:
            all_currencys.append(name)
    return all_currencys


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        currencys = get_all_currencys_name()
        result = request.get_json()
        chat_id = result['message']['chat']['id']
        message_text = result['message']['text']
        name = get_all_currencys_name(message_text)
        if name == 'help':
            send_message(chat_id, text='Чтобы узнать курс интересующей Вас\nкриптовалюты, введите её название в\nформате /bitcoin или /bitcoin-cash\n,если название состоит более чем из\nодного слова')
        elif name == 'info':
            message_text(chat_id, text='Этот бот показывает стоимость\nкриптовалюты ,в долларах США, на сайте\ncoinmarketcap.com в данный момент времени')
        elif name in currencys:
            price = get_currency_price(name)
            send_message(chat_id, text='{:.2f} USD'.format(price))
        else:
            send_message(chat_id, text='wrong currency name')
        return jsonify(result)
    return '<h1>Hello bot</h1>'


if __name__ == '__main__':
    app.run()
    