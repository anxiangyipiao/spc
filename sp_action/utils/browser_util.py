# -*- coding: utf-8 -*-
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


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
        sp_file_path = os.path.dirname(os.path.abspath(__file__)).split('utils')[0]
        chrome_options = Options()

        # 防机器人识别机制
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 根据配置是否显示浏览器
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # 修改加载策略
        if self.page_load_strategy:
            chrome_options.page_load_strategy = self.page_load_strategy

        # 屏蔽图片、样式表和通知
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 屏蔽图片
                'stylesheet': 2,  # 屏蔽样式表
                'notifications': 2,  # 屏蔽通知
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # 尝试启动浏览器
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except (SessionNotCreatedException, WebDriverException) as e:
            print(f'启动浏览器失败: {e}')
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

        # 加载 stealth.min.js 脚本
        with open(sp_file_path + 'stealth.min.js', 'r') as f:
            js = f.read()

        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})

        # 设置页面加载超时时间
        self.driver.set_page_load_timeout(self.timeout)

    def page_wait(self, url, time_limit):

        # 特殊情况处理
        content = self.driver.execute_script("return document.documentElement.outerHTML")
        title = self.driver.title.strip()

        if '业务繁忙，请稍后再试' in content or '错误' in title or '出错' in title or '稍等...' in title:
            print('刷新页面', url)
            self.driver.execute_script("window.location.href='%s'" % url)
            time.sleep(3)
            return self.page_wait(url, time_limit - 1)

        if title == '':
            time.sleep(1)
            return self.page_wait(url, time_limit - 1)

    def get_cookie(self, format='str'):
        if self.driver is None:
            self.open_browser()
        cookies = self.driver.get_cookies()
        if format == 'dict':
            return {item['name']: item['value'] for item in cookies}
        else:
            return '; '.join([f"{item['name']}={item['value']}" for item in cookies])

    def close_browser(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None