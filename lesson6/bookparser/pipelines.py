# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient


class BookparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.book_scrapy

    def process_item(self, item, spider):
        if spider.name == 'labirintru':
            pass

        if spider.name == 'book24ru':
            pass

        collection = self.mongo_base[spider.name]
        collection.insert_one(item)

        return item
