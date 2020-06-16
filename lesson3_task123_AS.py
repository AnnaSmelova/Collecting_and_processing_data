__author__ = 'Anna Smelova'
# Урок 3. Системы управления базами данных MongoDB и SQLite в Python

# Задание 1
# Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
# записывающую собранные вакансии в созданную БД


import requests
import re
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from pprint import pprint


MAIN_LINK = 'https://hh.ru'
HEADERS = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/83.0.4103.61 Safari/537.36'}


# Функция для обработки заработной платы
# ssalary - строка с заработной платой (пример: '120 000-180 000 руб.')
def parse_salary(ssalary):
    if not ssalary:
        return [None, None, None]
    salary = ssalary.replace(' ', '')
    asalary = salary.split(' ')
    curr = asalary[-1]

    salary_from = None
    salary_to = None

    regex_num = re.compile('\d+')
    salary_nums = regex_num.findall(salary)

    pattern_from = r'от.+[\d]+.+'
    pattern_to = r'до.+[\d]+.+'
    pattern_both = r'[\d]+.[\d]+.+'

    if re.match(pattern_from, salary):
        salary_from = salary_nums[0]
    elif re.match(pattern_to, salary):
        salary_to = salary_nums[0]
    elif re.match(pattern_both, salary):
        salary_from = salary_nums[0]
        salary_to = salary_nums[1]
    return [salary_from, salary_to, curr]


# Функция для получения базовой ссылки на вакансию (пример: https://hh.ru/vacancy/37422856)
# Эта ссылка уникальна для каждой вакансии
def get_base_url_from_url(url):
    base_url = url.split('?')[0]
    return base_url


# Функция записывающая собранные вакансии в бд
# collection - коллекция из бд
# user_query - вакансия, которую ищем
# user_limits - количество страниц для анализа
def collect_hh_vacancies(collection, user_query, user_limits):
    page = 0
    vacancies = []

    params = {'L_is_autosearch': 'false',
              'clusters': 'true',
              'enable_snippets': 'true',
              'text': user_query,
              'showClusters': 'true',
              'page': page}

    while True:
        # остановка, если проанализировали необходимое количество
        if 0 <= user_limits < params['page'] + 1:
            break

        response = requests.get(MAIN_LINK + '/search/vacancy/', params=params, headers=HEADERS)

        soup = bs(response.text, 'lxml')
        vacancy_block = soup.find('div', {'class': 'vacancy-serp'})  # нашли блок с вакансиями
        vacancy_list = vacancy_block.findChildren(recursive=False)

        for vacancy in vacancy_list:
            vacancy_data = {}

            # наименование вакансии и ссылка на саму вакансию
            vacancy_link_a = vacancy.find('a', {'class': 'bloko-link HH-LinkModifier'})
            try:
                vacancy_name = vacancy_link_a.getText()
                vacancy_link = str(vacancy_link_a['href'])
            except TypeError:
                continue
            except AttributeError:
                continue

            # сайт, откуда собрана вакансия
            vacancy_source = MAIN_LINK

            # работодатель
            vacancy_employer_a = vacancy.find('a', {'class': 'bloko-link bloko-link_secondary'})
            try:
                vacancy_employer = vacancy_employer_a.getText()
            except AttributeError:
                vacancy_employer = None

            # расположение
            vacancy_location_span = vacancy.find('span', {'class': 'vacancy-serp-item__meta-info'})
            try:
                vacancy_location = vacancy_location_span.getText()
            except AttributeError:
                vacancy_location = None

            # предлагаемая зарплата
            vacancy_salary_div = vacancy.find('div', {'class': 'vacancy-serp-item__sidebar'})
            try:
                vacancy_salary_span = vacancy_salary_div.findChildren(recursive=False)
                if vacancy_salary_span:
                    try:
                        vacancy_salary = vacancy_salary_span[0].getText()
                    except AttributeError:
                        vacancy_salary = None
                else:
                    vacancy_salary = None
            except AttributeError:
                vacancy_salary = None

            vacancy_salary_array = parse_salary(vacancy_salary)
            if vacancy_salary_array[0]:
                vacancy_salary_from = float(vacancy_salary_array[0])
            else:
                vacancy_salary_from = None
            if vacancy_salary_array[1]:
                vacancy_salary_to = float(vacancy_salary_array[1])
            else:
                vacancy_salary_to = None
            vacancy_salary_curr = vacancy_salary_array[2]

            vacancy_data['name'] = vacancy_name
            vacancy_data['url'] = vacancy_link
            vacancy_data['source'] = vacancy_source
            vacancy_data['location'] = vacancy_location
            vacancy_data['employer'] = vacancy_employer
            vacancy_data['min_salary'] = vacancy_salary_from
            vacancy_data['max_salary'] = vacancy_salary_to
            vacancy_data['currency'] = vacancy_salary_curr
            vacancy_data['base_url'] = get_base_url_from_url(vacancy_link)

            vacancies.append(vacancy_data)

        # Продолжаем, если на странице есть кнопка "Далее"
        next_button = soup.find('a', {'class': 'bloko-button HH-Pager-Controls-Next HH-Pager-Control'})
        if next_button:
            params['page'] += 1
        else:
            break
    if vacancies:
        collection.insert_many(vacancies)
    return f'Количество собранных вакансий: {len(vacancies)}'


client = MongoClient('localhost', 27017)
db = client['vacancy_hh']  # бд
vacancy = db.vacancy_hh  # коллекция

user_query = str(input('Укажите запрос: '))
user_limits = int(input('Укажите количество страниц для анализа(-1, если все): '))

vacancy.delete_many({})  # чистим коллекцию перед тем, как заполнить; функция для обновления базы ниже в п.3

result = collect_hh_vacancies(vacancy, user_query, user_limits)
print(result)
print()


# Задание 2
# Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введенной суммы


user_salary = float(input('Укажите заработную плату: '))


# функция выводит на экран вакансии с заработной платой больше введенной суммы
# salary - указанная сумма(float)
# vacancy - коллекция с вакансиями
def filter_vacancy_by_salary(salary, vacancy):
    cnt = 0
    for vac in vacancy.find({
        '$or': [
            {'max_salary': {'$gt': salary}}, {'min_salary': {'$gt': salary}}
        ]
    }):
        cnt += 1
        pprint(vac)
        print()
    return f'Найдено {cnt} вакансий с заработной платой выше {salary}'


result = filter_vacancy_by_salary(user_salary, vacancy)
print(result)
print()


# Задание 3*
# Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта

# Функция добавляет в коллекцию вакансии, которых нет в коллекции, а также обновляет,
# если в вакансии что-то поменялось
# collection - коллекция из бд
# user_query - вакансия, которую ищем
def update_hh_vacancies(collection, user_query):
    cnt = collection.estimated_document_count()
    page = 0
    params = {'L_is_autosearch': 'false',
              'clusters': 'true',
              'enable_snippets': 'true',
              'text': user_query,
              'showClusters': 'true',
              'page': page}

    while True:
        response = requests.get(MAIN_LINK + '/search/vacancy/', params=params, headers=HEADERS)

        soup = bs(response.text, 'lxml')
        vacancy_block = soup.find('div', {'class': 'vacancy-serp'})  # нашли блок с вакансиями
        vacancy_list = vacancy_block.findChildren(recursive=False)

        for vacancy in vacancy_list:
            # наименование вакансии и ссылка на саму вакансию
            vacancy_link_a = vacancy.find('a', {'class': 'bloko-link HH-LinkModifier'})
            try:
                vacancy_name = vacancy_link_a.getText()
                vacancy_link = str(vacancy_link_a['href'])
            except TypeError:
                continue
            except AttributeError:
                continue

            # сайт, откуда собрана вакансия
            vacancy_source = MAIN_LINK

            # работодатель
            vacancy_employer_a = vacancy.find('a', {'class': 'bloko-link bloko-link_secondary'})
            try:
                vacancy_employer = vacancy_employer_a.getText()
            except AttributeError:
                vacancy_employer = None

            # расположение
            vacancy_location_span = vacancy.find('span', {'class': 'vacancy-serp-item__meta-info'})
            try:
                vacancy_location = vacancy_location_span.getText()
            except AttributeError:
                vacancy_location = None

            # предлагаемая зарплата
            vacancy_salary_div = vacancy.find('div', {'class': 'vacancy-serp-item__sidebar'})
            try:
                vacancy_salary_span = vacancy_salary_div.findChildren(recursive=False)
                if vacancy_salary_span:
                    try:
                        vacancy_salary = vacancy_salary_span[0].getText()
                    except AttributeError:
                        vacancy_salary = None
                else:
                    vacancy_salary = None
            except AttributeError:
                vacancy_salary = None

            vacancy_salary_array = parse_salary(vacancy_salary)
            if vacancy_salary_array[0]:
                vacancy_salary_from = float(vacancy_salary_array[0])
            else:
                vacancy_salary_from = None
            if vacancy_salary_array[1]:
                vacancy_salary_to = float(vacancy_salary_array[1])
            else:
                vacancy_salary_to = None
            vacancy_salary_curr = vacancy_salary_array[2]

            collection.find_one_and_update(
                {'name': vacancy_name, 'base_url': get_base_url_from_url(vacancy_link)},
                {'$set': {
                    'url': vacancy_link,
                    'source': vacancy_source,
                    'location': vacancy_location,
                    'employer': vacancy_employer,
                    'min_salary': vacancy_salary_from,
                    'max_salary': vacancy_salary_to,
                    'currency': vacancy_salary_curr
                }},
                upsert=True
            )

        # Продолжаем, если на странице есть кнопка "Далее"
        next_button = soup.find('a', {'class': 'bloko-button HH-Pager-Controls-Next HH-Pager-Control'})
        if next_button:
            params['page'] += 1
        else:
            break
    added_cnt = collection.estimated_document_count() - cnt
    return f'В коллекцию добавлено {added_cnt} новых вакансий'


print(f'По запросу {user_query} в коллекции {vacancy.estimated_document_count()} вакансий.')
print('Добавление новых вакансий с сайта...')
result = update_hh_vacancies(vacancy, user_query)
print(result)
print(f'По запросу {user_query} в коллекции {vacancy.estimated_document_count()} вакансий.')
