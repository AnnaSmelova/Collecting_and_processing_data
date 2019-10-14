__author__ = 'Anna Smelova'
# Урок 1. Основы клиент-серверного взаимодействия. Парсинг API
# Задание 2
#
# Изучить список открытых API.
# Найти среди них любое, требующее авторизацию (любого типа).
# Выполнить запросы к нему, пройдя авторизацию.
# Ответ сервера записать в файл.

# Выбрала API https://www.worldweatheronline.com/developer/
# Authentication Model: API Key (Provided when registering your application.)
# После регистрации получила trial api key
# APIkey = 'f5df54c3faae48e38b7212013191410'

import requests
import json
import os

APIkey = 'f5df54c3faae48e38b7212013191410'

header = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}

# Запросим погоду в Москве на завтра
url = f'https://api.worldweatheronline.com/premium/v1/weather.ashx?key={APIkey}&q=Moscow&num_of_days=1&tp=3&format=json'

Moscow_Response = requests.get(url, headers=header)

print(f'Код ответа сервера: {Moscow_Response.status_code}')

j_data = Moscow_Response.json()

current_dir = os.getcwd()
path_to_write = os.path.join(current_dir, f'l1t2_response.json')
with open(path_to_write, 'w') as j_file:
    j_file.write(json.dumps(j_data))
