import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.http import HtmlResponse

class BrowserManager:
    def __init__(self, use_profix=False, timeout=360, page_load_strategy='', headless=True):
        self.driver = None
        self.use_profix = use_profix
        self.timeout = timeout
        self.page_load_strategy = page_load_strategy
        self.headless = headless

    def open_browser(self):
        if self.driver is not None:
            return
        sp_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
        chrome_options = Options()
        
        # 修改windows.navigator.webdriver，防机器人识别机制，selenium自动登陆判别机制
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        # 根据配置是否显示浏览器
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 可根据需要修改加载策略
        if self.page_load_strategy:
            chrome_options.page_load_strategy = self.page_load_strategy
        
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 屏蔽图片
                'stylesheet': 2,
                'notifications': 2,  # 屏蔽消息推送
            }
        }
        
        # 添加屏蔽chrome浏览器禁用图片的设置
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except SessionNotCreatedException:
            print('浏览器驱动不匹配，尝试重新下载')
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, options=chrome_options)
        except WebDriverException as e:
            print('启动浏览器失败', e)
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, options=chrome_options)
        
        with open(sp_file_path + 'stealth.min.js', 'r') as f:
            js = f.read()
        
        # 调用函数在页面加载前执行脚本
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})
        self.driver.set_page_load_timeout(self.timeout)

    def driver_get_page(self, url, ret_type='source', wait=0.5):
        if self.driver is None:
            self.open_browser()
        self.driver.get(url)
        self.page_wait(url, 5)
        time.sleep(wait)
        if ret_type == 'html':
            content = self.driver.execute_script("return document.documentElement.outerHTML")
        else:
            content = self.driver.page_source
        return HtmlResponse(url=url, body=content, encoding='utf-8')

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
            raise Exception("页面加载超时")

    def get_cookie(self, format='str'):
        if self.driver is None:
            self.open_browser()
        cookies = self.driver.get_cookies()
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

    def close_browser(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None