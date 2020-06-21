__author__ = 'Anna Smelova'
# Написать программу, которая собирает входящие письма из своего или тестового почтового ящика
# и сложить данные о письмах в базу данных
# * от кого,
# * дата отправки,
# * тема письма,
# * текст письма полный
#
# Логин тестового ящика: study.ai_172@mail.ru
# Пароль тестового ящика: NextPassword172

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient
from pprint import pprint
import time


def get_data_from_letter(driver):
    email = {}
    email['from'] = driver.find_element_by_xpath("//span[@class='letter-contact']").get_attribute("title")
    time.sleep(5)
    email['date'] = driver.find_element_by_xpath("//div[@class='letter__date']").text
    email['theme'] = driver.find_element_by_xpath("//div/h2[@class='thread__subject thread__subject_pony-mode']").text
    email['text'] = driver.find_elements_by_xpath("//div[@class='letter-body__body-content']")[0].text
    #pprint(email)
    return email


emails = []
user_limit = 30  # ограничим количество просматриваемых писем, чтобы не ждать долго

chrome_options = Options()
chrome_options.add_argument('start-maximized')
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://mail.ru/")

assert "Mail" in driver.title

# логин
elem = driver.find_element_by_id('mailbox:login')
elem.send_keys('study.ai_172@mail.ru')
elem.send_keys(Keys.RETURN)
# пароль
elem = WebDriverWait(driver,5).until(
    EC.element_to_be_clickable((By.ID, 'mailbox:password'))
)
elem.send_keys('NextPassword172')
elem.send_keys(Keys.RETURN)
time.sleep(5)
# открываем первое письмо
link = driver.find_element_by_xpath("//a[@class='llc js-tooltip-direction_letter-bottom js-letter-list-item "
                                    "llc_pony-mode llc_normal']").get_attribute("href")
driver.get(link)
time.sleep(1)
email = get_data_from_letter(driver)
emails.append(email)

next_button = driver.find_element_by_xpath("//span[@class='button2 button2_has-ico button2_arrow-down button2_pure "
                                           "button2_short button2_compact button2_ico-text-top button2_hover-support "
                                           "js-shortcut']")
cnt = 1
while not next_button.get_attribute("disabled") and cnt < user_limit:
    cnt += 1
    next_button.click()
    email = get_data_from_letter(driver)
    emails.append(email)
    next_button = driver.find_element_by_xpath("//span[@class='button2 button2_has-ico button2_arrow-down button2_pure "
                                               "button2_short button2_compact button2_ico-text-top button2_hover-support "
                                               "js-shortcut']")


driver.close()

print(f'Собрана информация о {len(emails)} письмах.')

client = MongoClient('localhost', 27017)
db = client['letters']  # бд
letters = db.letters  # коллекция
letters.delete_many({})
letters.insert_many(emails)

# Проверка
for l in letters.find():
    print(l)
