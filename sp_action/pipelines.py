# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# import time
import pymysql
import time, os
from .tool import parse_html
from datetime import datetime, timedelta


class TransformerAddPipeline(object):
    # 构造方法（初始化对象时执行的方法）
    # 开启爬虫时: 连接MySQL
    def open_spider(self, spider):
        self.cursor = None

    # 关闭爬虫时: 关闭连接MySQL
    def close_spider(self, spider):
        try:
            self.cursor.close()
            self.db.close()
        except:
            pass

            # 处理数据

    def process_item(self, item, spider):
        table_name = item.table_name
        if self.cursor == None:
            try:
                self.db = pymysql.connect(
                    host=spider.config_ext.get('mysql', 'server'), port=int(spider.config_ext.get('mysql', 'port')),
                    user=spider.config_ext.get('mysql', 'username'),
                    password=spider.config_ext.get('mysql', 'password'),
                    database=spider.config_ext.get('mysql', 'db'), charset='utf8mb4'
                )
                self.cursor = self.db.cursor()
                print('数据库连接成功')
            except Exception  as e:
                print('数据库连接失败', e)

        # 进行时间判断
        item['entry_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        entry_time2 = time.strftime("%Y-%m-%d", time.localtime()) + ' 17:00:00'
        entry_time3 = time.strftime("%Y-%m-%d", time.localtime()) + ' 17:40:00'
        
        if item['entry_time'] > entry_time2 and item['entry_time'] < entry_time3:
            print('服务器忙，后续重新抓取')
        else:
            # 正常抓取
            item['title'] = item['title'].replace("\n", "")
            # 固定参数
            if item['contents'] == None or item['contents'] == 'None':
                print('详情页内容可能获取失败，请检查', item['title'])
                return item
            

            
            spider.download_success(dict(item, **{"title": item["title"]}))
            

            # 用时间  紧急处理redis问题
            if item['publish_time'] > '2024-11-10':
                
                # 二次过滤时间
                default_publish_day = str(datetime.now() + timedelta(days=-4))[:10]
                item['publish_time'] = item['publish_time'].replace('/', '-')
                if item['publish_time'] > default_publish_day:

                    # 解决特殊去重问题
                    if 'http' not in item['url']:
                        item['url'] = item['standby_url']

                    keys = list(item.keys())  # ['pcid', 'pid', 'cid', 'roles']
                    values = list(item.values())  # ['333', '222', '111', '制作方']
                    
                    # 所有字段组成的字符串
                    key_str = ','.join(['`%s`' % k for k in keys])
                    # 值组成的字符串
                    values_str = ','.join(["%s"] * len(values))
                    c_item = dict(**item)
                    c_keys = list(c_item.keys())

                    c_values = list(c_item.values())
                    # update字符串
                    update_str = ','.join(["`{}`=%s".format(k) for k in c_keys])

                    sql = 'insert into `{}`({}) values({}) on duplicate key update {}'.format(
                        'c_original_info',
                        key_str,
                        values_str,
                        update_str
                    )
                    # print(c_values)
                    # 执行SQL
                    self.cursor.execute(sql, values + c_values)
                    self.db.commit()
                    print(f'----- 插入原始数据成功: -----')

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





