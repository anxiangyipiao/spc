# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SpiderItem(scrapy.Item):

    _id = scrapy.Field()
    province = scrapy.Field()  # 省份
    city = scrapy.Field()  # 城市
    county = scrapy.Field()  # 县级
    title = scrapy.Field()  # 标题
    url = scrapy.Field()  # 详情页链接
    publish_time = scrapy.Field()  # 发布时间
    source = scrapy.Field()  # 来源
    entry_time = scrapy.Field()  # 抓取时间
    site_name = scrapy.Field()  # 网站名称
    # file_type = scrapy.Field()  # 详情页内容
    contents = scrapy.Field()  # 详情页内容
    type = scrapy.Field()
    standby_url = scrapy.Field()

 


