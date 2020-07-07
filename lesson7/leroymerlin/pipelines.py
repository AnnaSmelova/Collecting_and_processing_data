# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import os
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
from urllib.parse import urlparse


class DataBasePipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.leroymerlin_scrapy

    def write_to_db(self, item, collection_name):
        collection = self.mongo_base[collection_name]
        try:
            collection.insert_one(item)
        except Exception as e:
            print(e, item)
            pass

    def process_item(self, item, spider):
        product = {
            'name': item['name'],
            'photos': item['photos'],
            'params': self.extract_params(item),
            'link': item['link'],
            'price': item['price']
        }

        self.write_to_db(product, 'leroymerlin')
        return item

    def extract_params(self, item):
        params = {}
        for param in item['params']:
            p = param.split('>')[2].split('<')[0]
            v = param.split('>')[4].split('<')[0].replace('\n','').strip()
            params[p] = v
        return params


class LeroymerlinImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for img in item['photos']:
                try:
                    yield scrapy.Request(img, meta=item)
                except Exception as e:
                    print(e)

    def file_path(self, request, response=None, info=None, ):
        item = request.meta
        return 'img/'+ item['link'].split('/')[-2] + '/' + os.path.basename(urlparse(request.url).path)

    def item_completed(self, results, item, info):
        if results:
            item['photos'] = [itm[1] for itm in results if itm[0]]
        return item
