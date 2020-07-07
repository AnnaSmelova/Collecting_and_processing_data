# -*- coding: utf-8 -*-
import scrapy
import re
import json
from scrapy.http import HtmlResponse
from instagram.items import InstagramItem
from urllib.parse import urlencode
from copy import deepcopy


class InstagramcomSpider(scrapy.Spider):
    #атрибуты класса
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    insta_login = ''
    insta_pwd = ''
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'

    graphql_url = 'https://www.instagram.com/graphql/query/?'

    subscribers_hash = 'c76146de99bb02f6415203be841dd25a'
    subscriptions_hash = 'd04b0a864b4b54837c0d870b0e77e076'

    def __init__(self, users_list):
        self.parse_users = users_list      #Пользователь, у которого собираем посты. Можно указать список

    def parse(self, response: HtmlResponse):  #Первый запрос на стартовую страницу
        csrf_token = self.fetch_csrf_token(response.text)   #csrf token забираем из html
        yield scrapy.FormRequest(                   #заполняем форму для авторизации
            self.inst_login_link,
            method='POST',
            callback=self.user_parse,
            formdata={'username': self.insta_login, 'enc_password': self.insta_pwd},
            headers={'X-CSRFToken': csrf_token}
        )

    def user_parse(self, response: HtmlResponse):
        j_body = json.loads(response.text)
        if j_body['authenticated']:                 #Проверяем ответ после авторизации
            for user in self.parse_users:
                yield response.follow(                  #Переходим на желаемую страницу пользователя. Сделать цикл для кол-ва пользователей больше 2-ух
                    f'/{user}',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': user}
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)       #Получаем id пользователя
        variables={'id': user_id,                                    #Формируем словарь для передачи даных в запрос
                   'username': username,
                   'first': 12}                                      #12 постов. Можно больше (макс. 50)

        url_subscribers = f'{self.graphql_url}query_hash={self.subscribers_hash}&{urlencode(variables)}'
        yield response.follow(
            url_subscribers,
            callback=self.subscribers_parse,
            cb_kwargs={'user_id': user_id,
                       'username': username,
                       'variables': deepcopy(variables)
                       }
        )

        url_subscriptions = f'{self.graphql_url}query_hash={self.subscriptions_hash}&{urlencode(variables)}'
        yield response.follow(
            url_subscriptions,
            callback=self.subscriptions_parse,
            cb_kwargs={'user_id': user_id,
                       'username': username,
                       'variables': deepcopy(variables)
                       }

        )

    def subscribers_parse(self, response, user_id, username, variables):
        j_body = json.loads(response.text)
        page_info = j_body.get('data').get('user').get('edge_followed_by').get('page_info')
        if page_info['has_next_page']:
            variables['after'] = page_info['end_cursor']

            url_subscribers = f'{self.graphql_url}query_hash={self.subscribers_hash}&{urlencode(variables)}'

            yield response.follow(
                url_subscribers,
                callback=self.subscribers_parse,
                cb_kwargs={'user_id': user_id,
                           'username': username,
                           'variables': deepcopy(variables)}
            )

        subscribers = j_body.get('data').get('user').get('edge_followed_by').get('edges')
        for subscriber in subscribers:
            item = InstagramItem(
                source_id=user_id,
                source_name=username,
                user_id=subscriber['node']['id'],
                user_name=subscriber['node']['username'],
                user_fullname=subscriber['node']['full_name'],
                photo_url=subscriber['node']['profile_pic_url'],
                subs_type='subscriber'
            )

            yield item

    def subscriptions_parse(self, response, user_id, username, variables):
        j_body = json.loads(response.text)
        page_info = j_body.get('data').get('user').get('edge_follow').get('page_info')
        if page_info['has_next_page']:
            variables['after'] = page_info['end_cursor']

            url_subscriptions = f'{self.graphql_url}query_hash={self.subscriptions_hash}&{urlencode(variables)}'

            yield response.follow(
                url_subscriptions,
                callback=self.subscriptions_parse,
                cb_kwargs={'user_id': user_id,
                           'username': username,
                           'variables': deepcopy(variables)}
            )

        subscriptions = j_body.get('data').get('user').get('edge_follow').get('edges')
        for subscription in subscriptions:
            item = InstagramItem(
                source_id=user_id,
                source_name=username,
                user_id=subscription['node']['id'],
                user_name=subscription['node']['username'],
                user_fullname=subscription['node']['full_name'],
                photo_url=subscription['node']['profile_pic_url'],
                subs_type='subscription'
            )

            yield item

    #Получаем токен для авторизации
    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    #Получаем id желаемого пользователя
    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')
