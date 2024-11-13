# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# import time
import logging
import time
from .tool import parse_html
from sp_action.utils import MySQLClient

logger = logging.getLogger(__name__)


class TransformerAddPipeline(object):


    def open_spider(self, spider):

        self.mysql_client = MySQLClient()

        # 失效关键字
        self.filter_titles = self.mysql_client.get_filter_title()
        
        # 重要关键字
        self.importance_titles = self.mysql_client.get_important_title()


    def filter_time(self, item):

        # 进行时间判断
        item['entry_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        entry_time2 = time.strftime("%Y-%m-%d", time.localtime()) + ' 17:00:00'
        entry_time3 = time.strftime("%Y-%m-%d", time.localtime()) + ' 17:40:00'
        
        if item['entry_time'] > entry_time2 and item['entry_time'] < entry_time3:
            print('服务器忙，后续重新抓取')
            return False
        
        return True

    # 判断详情页内容是否为空
    def filter_contents(self, item):

        if item['contents'] == None:
            logger.error('详情页内容可能获取失败，请检查', item['title'])
            return False
        return True


    def get_item_type(self, item):
         
        # 千里马、招标网单独入库，其它网站进行正文筛选
        if item['site_name'] != '千里马' and item['site_name'] != '招标网':
            item['type'] = parse_html(item['title'], item['contents'])
        else:
            item['type'] = '变压器'
        
        return item


    def process_item(self, item, spider):

        # 过滤时间 17:00-17:40
        if self.filter_time(item) == False:

            return item
        
        # 判断详情页内容是否为空，或者获取失败
        if self.filter_contents(item) == False:
            
            spider.content_download_error(dict(item, **{"title": item["title"]}))
            return item

        # 可用item,调用下载成功回调函数
        spider.content_download_success(dict(item, **{"title": item["title"]}))

        # 插入原始数据，全量数据
        self.mysql_client.insert_item_to_origin(item)
        
        # 获得item的类型
        item = self.get_item_type(item)
        # 对于需求的字段，进行数据入库
        if item['type']:
                        
            # 如果 item['title'] 不包含任何一个self.filter_titles，那么 any 函数会返回 False
            if any(keyword in item['title'] for keyword in self.filter_titles) == False:
                            
                self.mysql_client.insert_item_to_simple(item)
          
                return item

            # 如果 item['title'] 包含任何一个self.importance_titles，那么 any 函数会返回 True
            if any(keyword in item['title'] for keyword in self.importance_titles) == True:
                
                self.mysql_client.insert_item_to_simple(item)
                
                return item
