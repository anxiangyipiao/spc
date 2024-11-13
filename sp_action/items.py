# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SpiderItem(scrapy.Item):

    table_name = 'c_transformer_info'
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

    # province = scrapy.Field()  # 城市
    # city = scrapy.Field()  # 城市
    # project_county = scrapy.Field()  # 区/县
    # file_type = scrapy.Field()  # 文件类型：招标公告、中标公告、中标候选人公告
    # project_name = scrapy.Field()  # 项目名称
    # project_id = scrapy.Field()  # 项目编号
    # section_name = scrapy.Field()  # 标段名称
    # section_id = scrapy.Field()  # 标段编号
    # project_type = scrapy.Field()  # 项目类型：建设工程，水利工程，交通工程等
    # published_date = scrapy.Field()  # 项目公布日期
    # project_link = scrapy.Field()  # 项目详情链接
    # pdf_link = scrapy.Field()  # 项目pdf链接
    # contents = scrapy.Field()  # 项目详情内容
    # published_date_new = scrapy.Field()  # 项目公布日期(备用)


