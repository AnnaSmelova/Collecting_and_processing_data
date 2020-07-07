# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
from bookparser.items import BookparserItem

class LabirintruSpider(scrapy.Spider):
    name = 'labirintru'
    allowed_domains = ['labirint.ru']
    start_urls = ['https://www.labirint.ru/search'
                  '/%D0%94%D0%B5%D1%82%D1%81%D0%BA%D0%B8%D0%B5%20%D1%81%D0%BA%D0%B0%D0%B7%D0%BA%D0%B8'
                  '/?stype=0']

    def parse(self, response:HtmlResponse):
        next_page = response.css('a.pagination-next__text::attr(href)').extract_first()
        book_links = response.css('div.products-row a.product-title-link::attr(href)').extract()
        for link in book_links:
            yield response.follow(link, callback=self.book_parse)

        yield response.follow(next_page, callback=self.parse)


    def book_parse(self, response:HtmlResponse):
        link = response.url
        name = response.css('h1::text').extract_first()
        author = response.css('div.authors a.analytics-click-js::text').extract_first()
        price = response.css('div.buying span.buying-priceold-val-number::text').extract_first()
        sale_price = response.css('div.buying span.buying-pricenew-val-number::text').extract_first()
        rating = response.xpath('//div[@id="rate"]/text()').extract_first()
        # print(link, name, author, price, sale_price, rating)
        yield BookparserItem(name=name,author=author,price=price,sale_price=sale_price,rating=rating)
