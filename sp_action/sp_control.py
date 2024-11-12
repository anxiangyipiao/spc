import inspect
import sys
from redis.sentinel import Sentinel
import configparser, hashlib, json, os, time, scrapy
from datetime import datetime
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter
import redis
import time
import requests
from hashlib import md5
from datetime import datetime, timedelta



from sp_action.utils.config_loader import ConfigLoader


from sp_action.utils import RedisClient,local_config


class ZhaotoubiaoBaseSpider(scrapy.Spider):
    name = 'base_spider'
    start_urls = ["https"]
    province = ''
    city = ''
    MYSETINEL = ''
    
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
    
    # 单网址获取错误超过该次数，跳过
    retry_num = 3
    
    # 是否使用chrome下载数据
    download_by_driver = False
    download_by_drission = False
    driver = None
    
    env = local_config['env']

    
    # 翻页结束标志
    page_over = False

    check_rule = None

    config_ext = None

    task_list = []
    titles_list = []

    custom_settings = {
        "ITEM_PIPELINES": {'sp_action.pipelines.TransformerAddPipeline': 300},
        'DOWNLOAD_DELAY': 0.3,
        'DOWNLOAD_TIMEOUT': 30,
        # "CONCURRENT_REQUESTS" : 1
        'DOWNLOADER_MIDDLEWARES': {
        'sp_action.middlewares.DownloaderMiddleware': 100,
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


    def get_success_name(self,publish_time):
        
        month_now = publish_time[:7]
        return self.env + ':' + 'download_link' + ':' + self.province + ':' + self.name + ':' + month_now + ':success'

    def get_ready_name(self,publish_time):
        
        month_now = publish_time[:7]
        return self.env + ':' + 'download_link' + ':' + self.province + ':' + self.name + ':' + month_now + ':ready'

    def get_new_link_name(self,publish_time):
            
            month_now = publish_time[:7]
            return self.env + ':' + 'new_link' + ':' + self.province + ':' + self.name + ':' + month_now + month_now
    
    
    # 添加下载任务set 先使用默认日期过滤，再使用redis集合去重，默认使用去重的redis key为当前爬虫名称，可修改指定名称作为去重判断
    def add_download_task(self, union_id, publish_time, check_rule='normal'):
        '''
        :param union_id: 任务唯一标识,url
        :param publish_time: 任务发布时间
        :param spider_name: 爬虫名称
        :param check_rule: 检查规则，默认为normal，可选值有：normal,simple,url  
        '''
        if self.check_rule == None:
            self.check_rule = check_rule

        if self.last_publish_time == None or self.date_to_timestamp(self.last_publish_time) < self.date_to_timestamp(publish_time[:10]):
            self.last_publish_time = publish_time[:10]

        # 先过滤日期，超过日期的不再添加
        if  self.check_published_time(publish_time) == False:
            
            return True
        
        success_name = self.get_success_name(publish_time)
        ready_name = self.get_ready_name(publish_time)

        if check_rule == 'normal':
            check_value = json.dumps({"url": union_id, "publish_time": publish_time})
        else:
            check_value = json.dumps({"url": union_id})

        # 判断是否已经存在success集合中
        success_exist = self.MASTER.sismember(success_name, check_value)
        if success_exist == False:

            # 判断是否已经存在ready集合中
            ready_exist = self.MASTER.sismember(ready_name, check_value)
            
            # ready集合中不存在，添加到ready集合中
            if ready_exist == False:
                
                self.MASTER.sadd(ready_name, check_value)

            # 判断是否已经存在任务列表中
            if check_value not in self.task_list:
                self.count_download_link += 1
                self.task_list.append(check_value)
                self.MASTER.hincrby(self.event_key, 'count_download_link', 1)

            return False
        
        return True

    # 下载成功回调函数
    def download_success(self, meta):
        
        url = meta['url']
        title = meta['title']
        publish_time = meta['publish_time']
        
        dic_data = {}
        dic_data['title'] = title
        dic_data['publish_time'] = publish_time
        dic_data['url'] = url

        self.titles_list.append(dic_data)


        success_name = self.get_success_name(publish_time)
        ready_name = self.get_ready_name(publish_time)
        new_name = self.get_new_link_name(publish_time)
           
        if self.check_rule == 'normal':
            check_value = json.dumps({"url": url, "publish_time": publish_time})
        
        else:
            check_value = json.dumps({"url": url})
        
        # 判断是否已经存在ready集合中
        if self.MASTER.sismember(ready_name, check_value):
            self.count_download_success += 1
            # 移动到success集合中
            self.MASTER.smove(ready_name, success_name, check_value)
        
        self.MASTER.sadd(new_name, json.dumps({"url": url, "publish_time": publish_time, "title": title}))

    # 时间对比，控制翻页
    def check_published_time(self, publish_time):
        
        # 提前结束
        if self.max_error_num < 0:
            return False
        
        # 转时间戳对比
        check_time = self.date_to_timestamp(publish_time)
        return check_time > (self.last_published_timestamp - int(self.published_check_offset_day) * 86400)

    # 通过redis检测数据是否重复
    def record_error(self, request, response):
        meta = request.meta
        # 部分代码传递方式不一致，做兼容处理
        if meta.get('item') != None:
            meta = meta.get('item')
        # 只监控详情数据获取部分，获取详情部分代码meta传递下面两个变量
        if meta.get('url') != None and meta.get('publish_time') != None:
            self.max_error_num -= 1
            filter_key = meta.get('url') + meta.get('title') + meta.get('publish_time')
            md5_key = hashlib.md5(filter_key.encode(encoding='UTF-8')).hexdigest()
            ready_name = self.env + ':' + 'download_error' + ':' + self.province + ':' + self.name + ':' + meta.get(
                'publish_time').strip()[:7] + ':' + md5_key
            if self.MASTER.hexists(ready_name, 'retry_num') == False:
                self.MASTER.hmset(ready_name,
                                  {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "response_code": response.status,
                                   "url": meta.get('url'), "title": meta.get('title'),
                                   "publish_time": meta.get('publish_time'), "retry_num": self.retry_num})
            else:
                # 获取重试次数
                retry_num = self.MASTER.hget(ready_name, 'retry_num')
                if int(retry_num) > 1:
                    self.MASTER.hincrby(ready_name, 'retry_num', -1)
                else:
                    self.max_error_num += 1
                    self.count_download_link -= 1
                    print('self.count_download_link', self.count_download_link)

    def date_to_timestamp(self, date_str):
        date_str = date_str.strip()
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        return int(dt.timestamp())

    # 正常结束，调用检查更新代码
    def closed(self, reason):
        # 如果开启过浏览器，尝试关闭
        if self.driver != None:
            try:
                print('close driver！')
                self.driver.close()
                self.driver.quit()
            except:
                pass
        print('closed', reason)
        if self.page_over == False or self.max_error_num < 0 or self.count_download_link != self.count_download_success:
            # current_hour = datetime.now().hour
            # if current_hour in (23, 0, 1, 2, 3, 4, 5):
            #     return
            update_map = {'running_status': 'faild', 'province': self.province, 'city': self.city, 'county': '','current_directory':self.current_directory}
        else:
            update_map = {'running_status': 'success', 'retry_times': '0', 'last_publish_time': self.last_publish_time,
                          'province': self.province, 'city': self.city, 'county': '','current_directory':self.current_directory}
        if hasattr(self, 'county'):
            update_map['county'] = self.county
        if hasattr(self, 'file_type'):
            update_map['file_type'] = self.file_type

        print(update_map)
        print('count_download_link:%s' % self.count_download_link)
        print('self.page_over', self.page_over)
        print('self.max_error_num', self.max_error_num)
        print('count_download_success:%s' % self.count_download_success)


        if self.last_publish_time != None:
            self.MASTER.hmset(self.event_key, update_map)

    def get_redis_titles(self, new_month):
        spider_name_redis = self.env + ':' + 'new_link' + ':' + self.province + ':' + self.name + ':' + new_month
        lis = self.MASTER.smembers(spider_name_redis)
        project_redis_list = []
        for i in lis:
            dates = json.loads(i)
            project_redis_list.append(dates['title'] + dates['publish_time'])
        project_redis_names = dict(Counter(project_redis_list))
        # 重复项目名称和重复次
        project_redis_names_dict = {key: value for key, value in project_redis_names.items() if value > 1}
        return project_redis_names_dict

    # 打开浏览器
    def openBrowser(self, use_profix=False, timeout=360, page_load_strategy=''):
        if self.driver != None:
            return
        sp_file_path = os.path.split(os.path.realpath(__file__))[0] + os.sep
        chrome_options = Options()
        # 修改windows.navigator.webdriver，防机器人识别机制，selenium自动登陆判别机制
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 根据配置是否显示浏览器
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # 可根据需要修改加载策略
        if page_load_strategy != '':
            chrome_options.page_load_strategy = page_load_strategy
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 屏蔽图片
                'stylesheet': 2,
                'notifications': 2,  # 屏蔽消息推送
            }
        }
        print("启动1")
        # 添加屏蔽chrome浏览器禁用图片的设置
        # chrome_options.add_experimental_option("prefs", prefs)
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("启动2")
        except SessionNotCreatedException:
            print('浏览器驱动不匹配，尝试重新下载')
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
        except WebDriverException as e:
            print('启动浏览器失败', e)
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
        with open(sp_file_path + 'stealth.min.js', 'r') as f:
            js = f.read()
        # 调用函数在页面加载前执行脚本
        # self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})
        self.driver.set_page_load_timeout(timeout)

    def driver_get_page(self, url, request, ret_type='source', wait=0.5):
        if self.driver == None:
            self.openBrowser()
        self.driver.get(url)
        self.page_wait(url, 5)
        time.sleep(wait)
        if ret_type == 'html':
            content = self.driver.execute_script("return document.documentElement.outerHTML")
        else:
            content = self.driver.page_source
        return HtmlResponse(url=url, body=content, encoding='utf-8', request=request)

    def drission_page(self, url, request):
        if self.driver == None:
            co = ChromiumOptions().auto_port()
            self.driver = ChromiumPage(co)
        self.driver.get(url, retry=3, timeout=10, interval=2)
        time.sleep(0.5)
        return HtmlResponse(url=url, body=self.driver.html, encoding='utf-8', request=request)

    def page_wait(self, url, time_limit):
        if time_limit > 0:
            check_content = False
            # 天津特殊处理
            if 'tj.gov.cn' in url:
                content = self.driver.execute_script("return document.documentElement.outerHTML")
                if '业务繁忙，请稍后再试' in content:
                    check_content = True
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

    def get_cookie(self, driver, format='str'):
    
        cookies = driver.get_cookies()
        if format != 'str':
            cookies_dict = {}
            for item in cookies:
                cookies_dict[item['name']] = item['value']
            return cookies_dict
        else:
            _cookie = ''
            for item in cookies:
                _cookie = _cookie + item['name'] + '=' + item['value'] + ';'
            return _cookie

    def parse(self, response):
        pass
