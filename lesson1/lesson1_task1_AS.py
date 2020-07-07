__author__ = 'Anna Smelova'
# Урок 1. Основы клиент-серверного взаимодействия. Парсинг API
# Задание 1
#
# Посмотреть документацию к API GitHub,
# разобраться как вывести список репозиториев для конкретного пользователя,
# сохранить JSON-вывод в файле *.json.


import requests
import json
import os


USER = 'annasmelova'  # Мой аккаунт с 5 репозиториями
# USER = 'wdi-sg'  # Пользователь, у которого >300 репозиториев для проверки постраничного обхода

main_link = f'https://api.github.com/users/{USER}/repos'

user_repos_list = []

page = 1  # Идем в цикле по страницам, выводим по 100 репозиториев на страницу
params = {'page': page,
          'per_page': 100}
while True:
    page_repos_list = []
    data = requests.get(main_link, params=params)
    j_data = data.json()
    for repo in j_data:
        page_repos_list.append(repo['name'])
    params['page'] += 1
    user_repos_list += page_repos_list
    # Останавливаем цикл, когда на текущей странице меньше 100 репозиториев
    if len(page_repos_list) < 100:
        break

print(f'Репозитории пользователя {USER}:')
for rep in user_repos_list:
    print(rep)
print(f'Количество репозиториев пользователя {USER} = {len(user_repos_list)}')

current_dir = os.getcwd()
path_to_write = os.path.join(current_dir, f'l1t1_{USER}_git_repos_list.json')
with open(path_to_write, 'w') as j_file:
    j_file.write(json.dumps(user_repos_list))
