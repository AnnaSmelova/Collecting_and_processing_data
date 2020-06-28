# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from leroymerlin.items import LeroymerlinItem
from scrapy.loader import ItemLoader


class LeroymerlinruSpider(scrapy.Spider):
    name = 'leroymerlinru'
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, search):
        self.start_urls = [f'https://leroymerlin.ru/search/?q={search}']

    def parse(self, response):
        next_page = response.css('a.paginator-button.next-paginator-button::attr(href)').extract_first()

        item_links = response.xpath('//div[@class="ui-product-card__info"]//a[@class="black-link product-name-inner"]')
        for link in item_links:
            yield response.follow(link, callback=self.parse_item)

        yield response.follow(next_page, callback=self.parse)

    def parse_item(self, response:HtmlResponse):
        loader = ItemLoader(item=LeroymerlinItem(), response=response)

        loader.add_xpath('photos', '//img[@alt="product image"]/@src')
        loader.add_xpath('name', '//h1[@itemprop="name"]/text()')
        loader.add_xpath('params', '//div[@class="def-list__group"]')
        loader.add_value('link', response.url)
        loader.add_xpath('price', '//span[@slot="price"]/text()')
        yield loader.load_item()
