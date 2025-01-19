# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArgenpropItem(scrapy.Item):
    link = scrapy.Field()
    price = scrapy.Field()
    expenses = scrapy.Field()
    location = scrapy.Field()
    address = scrapy.Field()
    rooms = scrapy.Field()
    m2 = scrapy.Field()
    years = scrapy.Field()
    image = scrapy.Field()
