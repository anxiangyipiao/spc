# -*- coding: utf-8 -*-
import json, time, scrapy
from datetime import datetime
import time
from datetime import datetime, timedelta
from sp_action.utils import RedisClient,local_config


class ZhaotoubiaoBaseSpider(scrapy.Spider):
    name = 'base_spider'
    start_urls = ["https"]
    province = ''
    city = ''
    # 上次采集时间
    last_published_timestamp = 0

    # 最后一次发布时间
    last_publish_time = None
    
    # 此网站采集时间偏移量，单位：天
    published_check_offset_day = 7
    
    # 所以采集的link
    count_download_link = 0

    # 采集成功的link
    count_download_success = 0
    
    # 一次运行总错误次数超出该值，认为网站不可爬
    max_error_num = 5

    env = local_config['env']
    
    # 翻页结束标志
    page_over = False

    check_rule = None

    filed_list = []

    custom_settings = {
        "ITEM_PIPELINES": {'sp_action.pipelines.TransformerAddPipeline': 300},
        'DOWNLOAD_DELAY': 0.3,
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOADER_MIDDLEWARES': {
        'sp_action.middlewares.RetryDownloaderMiddleware': 100,
        'sp_action.middlewares.SeleniumMiddleware': 200,
        }
    }


    def __init__(self):
        
        # redis配置
        self.MASTER = RedisClient().get_client()
    
    def initialize_spider_data(self):

         # 构建运行键
        self.event_key = self.env + ':' + 'run_status' + ':' + self.province + ':' + self.name
        
        #  获取上次运行时间
        if  self.MASTER.hget(self.event_key, 'last_publish_time') == None:
            self.last_publish_time = str(datetime.now() + timedelta(days=6))[:10]
            self.last_published_timestamp = self.date_to_timestamp(str(datetime.now() + timedelta(days=6))[:10])
        
        else:
            self.last_publish_time = self.MASTER.hget(self.event_key, 'last_publish_time')
            self.last_published_timestamp = self.date_to_timestamp(self.last_publish_time)


        self.MASTER.hmset(self.event_key, {
                'last_publish_time': self.last_publish_time,
                'published_check_offset_day': self.published_check_offset_day,
                'running_status': 'running',
                'count_download_link': 0,
                'last_run_time': time.strftime("%Y-%m-%d %H:%M:%S")
            })


        self.published_check_offset_day = self.MASTER.hget(self.event_key, 'published_check_offset_day')

    def date_to_timestamp(self, date_str):
        date_str = date_str.strip()
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        return int(dt.timestamp())
     
    def check_published_time(self, publish_time):
        
        # 提前结束
        if self.max_error_num < 0:
            return False
        
        # 转时间戳对比
        check_time = self.date_to_timestamp(publish_time)
        return check_time > (self.last_published_timestamp - int(self.published_check_offset_day) * 86400)
    
    def get_success_name(self,publish_time):
        
        month_now = publish_time[:7]
        return self.env + ':' + 'download_link' + ':' + self.province + ':' + self.name + ':' + month_now + ':success'

    def get_download_error_name(self,publish_time):
        month_now = publish_time[:7]
        return self.env + ':' + 'download_error' + ':' + self.province + ':' + self.name + ':' + month_now + ':error'

    # 添加下载任务set 先使用默认日期过滤，再使用redis集合去重，默认使用去重的redis key为当前爬虫名称，可修改指定名称作为去重判断
    def add_download_task(self, union_id, publish_time, check_rule='normal'):
        '''
        :param union_id: 任务唯一标识,url
        :param publish_time: 任务发布时间
        :param spider_name: 爬虫名称
        :param check_rule: 检查规则，默认为normal，可选值有：normal,simple,url  
        '''

        # 先过滤日期，超过日期的不再添加
        if  self.check_published_time(publish_time) == False:
            
            return True


        if self.check_rule == None:
            self.check_rule = check_rule

        # 更新最后一次发布时间
        if self.last_publish_time == None or self.date_to_timestamp(self.last_publish_time) < self.date_to_timestamp(publish_time[:10]):
            self.last_publish_time = publish_time[:10]

        # 生成redis key
        success_name = self.get_success_name(publish_time)
        # ready_name = self.get_ready_name(publish_time)

        if check_rule == 'normal':
            check_value = json.dumps({"url": union_id, "publish_time": publish_time})
        else:
            check_value = json.dumps({"url": union_id})

        # 判断是否已经存在success集合中
        success_exist = self.MASTER.sismember(success_name, check_value)
        if success_exist == False:

            # 本轮爬取link加一
            self.count_download_link += 1

            return False
        
        return True

    # 下载成功回调函数
    def content_download_success(self, meta):
        
        success_name = self.get_success_name(meta['publish_time'])
        failed_name = self.get_download_error_name(meta['publish_time'])
 
        if self.check_rule == 'normal':
            check_value = json.dumps({"url": meta['url'], "publish_time": meta['publish_time']})
        else:
            check_value = json.dumps({"url": meta['url']})

        # 添加到success集合中
        self.MASTER.sadd(success_name, check_value)
        self.count_download_success += 1

        # 如果失败集合里面有，删除
        # title,url,publish_time
        failed_check_value = json.dumps({"url": meta['url'], "title": meta['title'], "publish_time": meta['publish_time']})
        if self.MASTER.sismember(failed_name, failed_check_value):
            self.MASTER.srem(failed_name, failed_check_value)

    def content_download_error(self, request, response):
        
    

        meta = request.meta

        # 部分代码传递方式不一致，做兼容处理
        if meta.get('item') != None:
            meta = meta.get('item')

        self.max_error_num += 1




        # fail_name = self.get_download_error(meta['publish_time'])
    
        # # 只监控详情数据获取部分，获取详情部分代码meta传递下面两个变量
        # if meta.get('url') != None and meta.get('publish_time') != None:
        #     self.max_error_num -= 1
        #     filter_key = meta.get('url') + meta.get('title') + meta.get('publish_time')
        #     md5_key = hashlib.md5(filter_key.encode(encoding='UTF-8')).hexdigest()
        #     ready_name = self.env + ':' + 'download_error' + ':' + self.province + ':' + self.name + ':' + meta.get('publish_time').strip()[:7] + ':' + md5_key
            
        #     if self.MASTER.hexists(ready_name, 'retry_num') == False:
        #         self.MASTER.hmset(ready_name,{"time": time.strftime("%Y-%m-%d %H:%M:%S"), "response_code": response.status,"url": meta.get('url'), "title": meta.get('title'),"publish_time": meta.get('publish_time'), "retry_num": self.retry_num})
            
        #     else:
        #         # 获取重试次数
        #         retry_num = self.MASTER.hget(ready_name, 'retry_num')
        #         if int(retry_num) > 1:
        #             self.MASTER.hincrby(ready_name, 'retry_num', -1)
        #         else:
        #             self.max_error_num += 1
        #             self.count_download_link -= 1
        #             print('self.count_download_link', self.count_download_link)

        
    # 正常结束，调用检查更新代码
    def closed(self, reason):


        if self.page_over == False or self.max_error_num < 0 or self.count_download_link != self.count_download_success:
         
            update_map = {'running_status': 'faild', 'province': self.province, 'city': self.city, 'county': '','current_directory':self.current_directory}
        else:
            update_map = {'running_status': 'success', 'retry_times': '0', 'last_publish_time': self.last_publish_time,'province': self.province, 'city': self.city, 'county': '','current_directory':self.current_directory}

        if hasattr(self, 'county'):
            update_map['county'] = self.county

        print('count_download_link:%s' % self.count_download_link)
        print('self.page_over', self.page_over)
        print('self.max_error_num', self.max_error_num)
        print('count_download_success:%s' % self.count_download_success)

        if self.last_publish_time != None:
            self.MASTER.hmset(self.event_key, update_map)


    def page_wait(self, url, time_limit):
         
        if time_limit > 0:

            check_content = False
                  
            # # 天津特殊处理
            # if 'tj.gov.cn' in url:
            #     content = self.driver.execute_script("return document.documentElement.outerHTML")
            #     if '业务繁忙，请稍后再试' in content:
            #         check_content = True
                
            if '错误' in self.driver.title or '出错' in self.driver.title or '稍等...' in self.driver.title or time_limit == 1 or check_content == True:
                
                print('刷新页面', url)
                self.driver.execute_script("window.location.href='%s'" % url)
                time.sleep(3)
                time_limit -= 1
                return self.page_wait(url, time_limit)

            if self.driver.title.strip() == '':
                time.sleep(1)
                time_limit -= 1
                return self.page_wait(url, time_limit)
        else:
            self.max_error_num -= 1


    def parse(self, response):
        pass
