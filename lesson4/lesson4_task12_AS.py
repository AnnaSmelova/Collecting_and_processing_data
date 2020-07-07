__author__ = 'Anna Smelova'
# 1)Написать приложение, которое собирает основные новости с сайтов news.mail.ru, lenta.ru, yandex.news
# Для парсинга использовать xpath. Структура данных должна содержать:
# название источника,
# наименование новости,
# ссылку на новость,
# дата публикации
#
# 2)Сложить все новости в БД

import requests
from pprint import pprint
from lxml import html
from datetime import datetime, timedelta
from pymongo import MongoClient


HEADERS = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/83.0.4103.61 Safari/537.36'}

# Функция преобразует дату с сайта moslenta.ru
# d - элемент типа <class 'lxml.etree._ElementUnicodeResult'>
# Примеры входных данных: 'Вчера в 18:14', 'Сегодня в 21:18', '26 мая в 00:01'
def parse_date_from_moslenta(d):
    sdate = d.__str__()
    if sdate.find('Сегодня') != -1:
        return datetime.today().strftime('%d/%m/%Y') + ' ' + sdate[-5:]
    elif sdate.find('Вчера') != -1:
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%d/%m/%Y') + ' ' + sdate[-5:]
    else:
        adate = sdate.split(' ')
        day = int(adate[0])
        month = adate[1]
        months = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
                  'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
        if month in months.keys():
            month = months[month]
        else:
            return sdate
        year = int(datetime.today().strftime("%Y"))
        time = adate[-1]

        result = datetime(year, month, day).strftime('%d/%m/%Y') + ' ' + time
        return result


# Функция собирает новости из блока "Главное" (топ-5 новостей)
# https://yandex.ru/news/
def get_news_from_yandex():
    base_link = 'https://yandex.ru/news/'
    response = requests.get(base_link, headers=HEADERS)
    dom = html.fromstring(response.text)
    blocks = dom.xpath("//div[@class='stories-set stories-set_main_yes stories-set_pos_0']")  # блок с топ-5 новостями
    news = []
    for block in blocks:
        names = block.xpath(".//div/h2/a/text()")
        links = block.xpath(".//div/h2/a/@href")
        sources_and_times = block.xpath(".//div[@class='story__date']/text()")
        i = 0
        while i < len(names):
            item = {}
            item['agg_source'] = base_link
            item['name'] = names[i]
            item['url'] = links[i].replace(r'/news/', base_link)
            item['source'] = sources_and_times[i][:-6]
            i_time = sources_and_times[i][-5:]
            i_date = datetime.today().strftime('%d/%m/%Y')
            item['date_time'] = str(i_date) + ' ' + str(i_time)
            news.append(item)
            i += 1

    # pprint(news)
    return news


# Функция собирает новости из блока "Картина дня" (топ-5 новостей)
# https://news.mail.ru/
def get_news_from_mail():
    base_link = 'https://news.mail.ru/'
    response = requests.get(base_link, headers=HEADERS)
    dom = html.fromstring(response.text)
    blocks = dom.xpath("//td[@class='daynews__main'] | //td[@class='daynews__items']")  # блок с топ-5 новостями
    news = []
    for block in blocks:
        names = block.xpath(".//a/span/span[1]/text()")
        links = block.xpath(".//a/@href")
        i = 0
        while i < len(names):
            item = {}
            # ссылка
            i_url = base_link + links[i]

            url_response = requests.get(i_url, headers=HEADERS)
            url_dom = html.fromstring(url_response.text)
            # дата публикации
            i_datetime = url_dom.xpath(".//span[@class='note__text breadcrumbs__text js-ago']/@datetime")
            d_t = datetime.strptime(str(i_datetime[0]), '%Y-%m-%dT%H:%M:%S%z').strftime('%d/%m/%Y %H:%M')
            # источник
            i_source = url_dom.xpath(".//a[@class='link color_gray breadcrumbs__link']//span[@class='link__text']/text()")

            item['agg_source'] = base_link
            item['name'] = names[i]
            item['url'] = i_url
            item['source'] = i_source[0]
            item['date_time'] = d_t

            news.append(item)
            i += 1

    # pprint(news)
    return news


# Функция собирает новости из блока "Главные новости"
# https://lenta.ru/
def get_news_from_lenta():
    base_link = 'https://lenta.ru/'
    response = requests.get(base_link, headers=HEADERS)
    dom = html.fromstring(response.text)
    blocks = dom.xpath("//div[contains(@class, 'b-yellow-box__wrap')]")  # блок с главныеми новостями
    news = []
    for block in blocks:
        names = block.xpath(".//div/a/text()")
        links = block.xpath(".//div/a/@href")
        i = 0
        while i < len(names):
            item = {}
            # ссылка и источник
            if links[i].find('https://') == -1:
                i_url = base_link + links[i]
                i_source = 'Lenta'
            else:
                i_url = links[i]
                i_source = 'Moslenta'

            # дата публикации
            url_response = requests.get(i_url, headers=HEADERS)
            url_dom = html.fromstring(url_response.text)

            if i_source == 'Lenta':
                i_datetime = url_dom.xpath(".//time[@class='g-date']/@datetime")
                d_t = datetime.strptime(str(i_datetime[0]), '%Y-%m-%dT%H:%M:%S%z').strftime('%d/%m/%Y %H:%M')
            else:
                i_datetime = url_dom.xpath(".//div[contains(@class, 'time')]/text()")
                d_t = parse_date_from_moslenta(i_datetime[0])

            item['agg_source'] = base_link
            item['name'] = names[i]
            item['url'] = i_url
            item['source'] = i_source
            item['date_time'] = d_t

            news.append(item)
            i += 1

    # pprint(news)
    return news


client = MongoClient('localhost', 27017)
db = client['news']  # бд
news = db.news  # коллекция
news.delete_many({})
news.insert_many(get_news_from_yandex())
news.insert_many(get_news_from_mail())
news.insert_many(get_news_from_lenta())

# Проверка
print('--------Lenta--------')
for n in news.find({'agg_source': 'https://lenta.ru/'}):
    pprint(n)
print(f"Всего новостей с Lenta: {news.count_documents({'agg_source': 'https://lenta.ru/'})}")
print()
print('--------Yandex--------')
for n in news.find({'agg_source': 'https://yandex.ru/news/'}):
    pprint(n)
print(f"Всего новостей с Yandex: {news.count_documents({'agg_source': 'https://yandex.ru/news/'})}")
print()
print('--------Mail--------')
for n in news.find({'agg_source': 'https://news.mail.ru/'}):
    pprint(n)
print(f"Всего новостей с Mail: {news.count_documents({'agg_source': 'https://news.mail.ru/'})}")
print()
