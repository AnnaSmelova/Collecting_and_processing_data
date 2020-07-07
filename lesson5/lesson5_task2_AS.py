__author__ = 'Anna Smelova'
# Написать программу, которая собирает «Хиты продаж» с сайта техники mvideo и складывает данные в БД.
# Магазины можно выбрать свои. Главный критерий выбора: динамически загружаемые товары

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import json
import time

goods = []

chrome_options = Options()
chrome_options.add_argument('start-maximized')
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.mvideo.ru/")

assert "М.Видео" in driver.title

time.sleep(15)
blocks = driver.find_elements_by_xpath("//div[@class='gallery-title-wrapper']")
for block in blocks:
    if block.text == 'Хиты продаж':
        next_button = block.find_element_by_xpath("..//..//..//a[contains(@class,'next-btn sel-hits-button-next')]")
        b_class = next_button.get_attribute('class')
        while b_class != 'next-btn sel-hits-button-next disabled':
            next_button.click()
            time.sleep(5)
            next_button = block.find_element_by_xpath("..//..//..//a[contains(@class,'next-btn sel-hits-button-next')]")
            b_class = next_button.get_attribute('class')
        elems = block.find_elements_by_xpath("..//..//..//li[@class='gallery-list-item height-ready']")
        cnt = 0
        for el in elems:
            cnt += 1
            data = el.find_element_by_xpath(".//a").get_attribute("data-product-info")
            # не хватило времени придумать, как обработать ошибку с дюймами, которые прикидываются двойными кавычками
            try:
                data_dict = json.loads(data)
            except:
                continue
            goods.append(data_dict)
        print(f'Собрана информация о {cnt} товарах.')

driver.close()

client = MongoClient('localhost', 27017)
db = client['goods']  # бд
items = db.goods  # коллекция
items.delete_many({})
items.insert_many(goods)

# Проверка
for i in items.find():
    print(i)
