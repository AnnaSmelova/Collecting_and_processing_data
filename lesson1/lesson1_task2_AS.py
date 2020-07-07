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
# APIkey = 'e4e2a9d0bcf445f287a200623200406'

import requests
import json
import os

APIkey = 'e4e2a9d0bcf445f287a200623200406'

header = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/83.0.4103.61 Safari/537.36'}

main_link = 'https://api.worldweatheronline.com/premium/v1/weather.ashx'

# Запросим погоду в Москве на завтра
city = 'Moscow'
params = {'key': APIkey,
          'q': city,  # локация
          'date': 'tomorrow',  # смотрим прогноз на завтра
          'num_of_days': 1,  # количество дней предсказания
          'format': 'json'}

Moscow_Response = requests.get(main_link, params=params, headers=header)

print(f'Код ответа сервера: {Moscow_Response.status_code}')

j_data = Moscow_Response.json()

print(f'Средняя температура завтра днем в {j_data["data"]["request"][0]["query"]} : '
      f'{j_data["data"]["weather"][0]["avgtempC"]}')

current_dir = os.getcwd()
path_to_write = os.path.join(current_dir, f'l1t2_response.json')
with open(path_to_write, 'w') as j_file:
    j_file.write(json.dumps(j_data))
