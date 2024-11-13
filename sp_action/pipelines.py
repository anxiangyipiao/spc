# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# import time
import logging
import time, os
from .tool import parse_html
from sp_action.utils import MySQLClient

logger = logging.getLogger(__name__)


class TransformerAddPipeline(object):
    # 构造方法（初始化对象时执行的方法）
    # 开启爬虫时: 连接MySQL
    def open_spider(self, spider):

        self.mysql_client = MySQLClient()


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

    def insert_original_info(self, item):
          
        pass

    def process_item(self, item, spider):


        # 过滤时间 17:00-17:40
        if self.filter_time(item) == False:

            return item
        

        # 判断详情页内容是否为空，或者获取失败
        if self.filter_contents(item) == False:
            
            spider.download_error(dict(item, **{"title": item["title"]}))
            return item


        # 可用item,调用下载成功回调函数
        spider.download_success(dict(item, **{"title": item["title"]}))

        # 插入原始数据
        self.mysql_client.insert_original_info(item)
        

        # 千里马、招标网单独入库，其它网站进行正文筛选
        if item['site_name'] != '千里马' and item['site_name'] != '招标网':
                item['type'] = parse_html(item['title'], item['contents'])
        else:
                item['type'] = '变压器'
        
        # 对于需求的字段，进行数据入库
        if item['type']:
                        # 从库中取无效关键字，进行入库前进行标题筛选无效关键字
                        contains_keyword = []
                        self.cursor.execute('SELECT contains_keyword FROM c_contains_keyword')
                        results = self.cursor.fetchall()
                        for row in results:
                            contains_keyword.append(row[0])
                        # print(contains_keyword)
                        # 对于标题  去除无效关键字
                        if any(keyword in item['title'] for keyword in contains_keyword) == False:
                            item['contents'] = ''
                            keys = list(item.keys())  # ['pcid', 'pid', 'cid', 'roles']
                            values = list(item.values())  # ['333', '222', '111', '制作方']
                            # 所有字段组成的字符串
                            key_str = ','.join(['`%s`' % k for k in keys])
                            # 值组成的字符串
                            values_str = ','.join(["%s"] * len(values))
                            c_item = dict(**item)
                            c_keys = list(c_item.keys())

                            if 'entry_time' in keys:
                                c_item.pop('entry_time')
                                c_keys.remove('entry_time')

                            c_values = list(c_item.values())
                            # update字符串
                            update_str = ','.join(["`{}`=%s".format(k) for k in c_keys])
                            # SQL
                            sql = 'insert into `{}`({}) values({}) on duplicate key update {}'.format(
                                table_name,
                                key_str,
                                values_str,
                                update_str
                            )
                            # print(c_values)
                            # 执行SQL
                            self.cursor.execute(sql, values + c_values)
                            self.db.commit()
                            print(f'----- 插入/更新成功: -----')
                            return item
                        else:
                            important_title = ['变压器', '主变', '油浸', '油变', '35KV', '中性点', '整流变', '配变', '厂用变', '变电站','66KV', '10KV', '220KV']
                            if any(keyword in item['title'] for keyword in important_title) == True:
                                item['contents'] = ''
                                keys = list(item.keys())  # ['pcid', 'pid', 'cid', 'roles']
                                values = list(item.values())  # ['333', '222', '111', '制作方']
                                # 所有字段组成的字符串
                                key_str = ','.join(['`%s`' % k for k in keys])
                                # 值组成的字符串
                                values_str = ','.join(["%s"] * len(values))
                                c_item = dict(**item)
                                c_keys = list(c_item.keys())

                                if 'entry_time' in keys:
                                    c_item.pop('entry_time')
                                    c_keys.remove('entry_time')

                                c_values = list(c_item.values())
                                # update字符串
                                update_str = ','.join(["`{}`=%s".format(k) for k in c_keys])
                                # SQL
                                sql = 'insert into `{}`({}) values({}) on duplicate key update {}'.format(
                                    table_name,
                                    key_str,
                                    values_str,
                                    update_str
                                )
                                # print(c_values)
                                # 执行SQL
                                self.cursor.execute(sql, values + c_values)
                                self.db.commit()
                                print(f'----- 插入/更新成功: -----')
                                return item





