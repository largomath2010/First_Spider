# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

class DuplicatesPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            Filter_Field=getattr(crawler.spider,'Filter_Field')
        )

    def __init__(self,Filter_Field):
        self.ids_seen = set()
        self.Filter_Field=Filter_Field

    def process_item(self, item, spider):
        if item[self.Filter_Field] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item[self.Filter_Field])
        else:
            self.ids_seen.add(item[self.Filter_Field])
            return item