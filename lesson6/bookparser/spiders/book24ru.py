# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from bookparser.items import BookparserItem


class Book24ruSpider(scrapy.Spider):
    name = 'book24ru'
    allowed_domains = ['book24.ru']
    start_urls = ['https://book24.ru/search'
                  '/?q=%D0%94%D0%B5%D1%82%D1%81%D0%BA%D0%B8%D0%B5+%D1%81%D0%BA%D0%B0%D0%B7%D0%BA%D0%B8']

    def parse(self, response:HtmlResponse):
        next_page = response.css('a.catalog-pagination__item._text.js-pagination-catalog-item::attr(href)').extract_first()
        book_links = response.css('div.catalog-products__list.js-catalog-products a.book__image-link.js-item-element.ddl_product_link::attr(href)').extract()
        for link in book_links:
            yield response.follow(link, callback=self.book_parse)

        yield response.follow(next_page, callback=self.parse)


    def book_parse(self, response:HtmlResponse):
        link = response.url
        name = response.css('h1::text').extract_first()
        author = response.xpath('//div[@class="item-tab__chars-item"]//a[@class="item-tab__chars-link"]/text()').extract_first()
        price = response.css('div.item-actions__price-old::text').extract_first()
        sale_price = response.css('div.item-actions__prices div.item-actions__price b::text').extract_first()
        rating = response.css('div.rating span.rating__rate-value::text').extract_first()
        # print(link, name, author, price, sale_price, rating)
        yield BookparserItem(name=name, author=author, price=price, sale_price=sale_price, rating=rating)
