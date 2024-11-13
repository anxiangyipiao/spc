# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from w3lib.http import basic_auth_header
from sp_action.utils import BrowserManager
from scrapy.http import HtmlResponse
from curl_cffi import requests as tl_requests
from scrapy import signals
from scrapy.utils.response import response_status_message
import random
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class SpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # # middleware.
        # if request.method == 'GET' and spider.download_by_driver == True and request.meta.get('download_by_driver') == None:
        #     return spider.driver_get_page(request.url, request)
            
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # if response.status != 200:
        #     spider.record_error(request, response)
        # # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        # print(response.status, response.url)
        return response

    def process_exception(self, request, exception, spider):
        
        # 处理error
        
        # spider.download_error(request, exception)
        
        
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)



class SeleniumMiddleware:
    def __init__(self, use_profix=False, timeout=360, page_load_strategy='', headless=True):
        self.browser_manager = BrowserManager(use_profix, timeout, page_load_strategy, headless)
        self.browser_manager.open_browser()

    def process_request(self, request, spider):
        if  request.meta.get('download_by_driver') == True:
            # 如果meta中存在'download_by_driver'且为True，则使用浏览器下载页面
            self.browser_manager.driver.get(request.url)
            # 等待页面加载完成，最多等待5秒
            self.browser_manager.page_wait(request.url, 5)
            # 获取页面的HTML源代码
            content = self.browser_manager.driver.page_source
            # 返回一个HtmlResponse对象，包含页面的URL、内容、编码和原始请求
            return HtmlResponse(request.url, body=content, encoding='utf-8', request=request)

    def process_exception(self, request, exception, spider):
        if self.browser_manager.driver:
            self.browser_manager.driver.quit()
            self.browser_manager.open_browser()
            return HtmlResponse(request.url, status=500, body=b'', encoding='utf-8', request=request)

    def spider_closed(self, spider):
        self.browser_manager.close_browser()



class RetryDownloaderMiddleware:
    def __init__(self):
        self.max_retry_times = 3
        self.proxy_list = [
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
            'http://proxy3.example.com:8080'
        ]

    def process_request(self, request, spider):
        # 检查是否需要使用代理
        if 'retry_times' in request.meta and request.meta['retry_times'] > 0:
            request.meta['proxy'] = random.choice(self.proxy_list)
        return None

    def process_response(self, request, response, spider):
        if response.status >= 400:
            retry_times = request.meta.get('retry_times', 0) + 1
            if retry_times <= self.max_retry_times:
                request.meta['retry_times'] = retry_times
                return request
            else:
                self._handle_download_failure(request, spider)

        return response

    def _handle_download_failure(self, request, spider):
        # 处理下载失败的情况
        spider.logger.error(f"Download failed for {request.url}")
        # 可以在这里添加更多的处理逻辑，例如记录到数据库或发送通知
        # ...


class ProxyDownloaderMiddleware:

    def process_request(self, request, spider):
        proxy = "h154.kdltps.com:15818"
        request.meta['proxy'] = "http://%(proxy)s" % {'proxy': proxy}
        # 用户名密码认证
        request.headers['Proxy-Authorization'] = basic_auth_header('t10902206553199', 'j6hbvavd')  # 白名单认证可注释此行
        request.headers["Connection"] = "close"

        if request.method == 'GET' and spider.download_by_driver == True:
            return spider.driver_get_page(request.url, request)
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        if response.status != 200:
            spider.record_error(request, response)
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        print(response.status, response.url)
        return response


class TlsDownloaderMiddleware:
    def trans_byte_header(self, headers):
        ret_header = {}
        for key, item in headers.items():
            ret_header[key.decode("utf-8")] = item[0].decode("utf-8")
        return ret_header

    def process_request(self, request, spider):
        headers = self.trans_byte_header(request.headers)
        if request.method == 'POST':
            ret = tl_requests.request(request.method, request.url, headers=headers, data=request.body.decode("utf-8"))
        else:
            ret = tl_requests.request(request.method, request.url, headers=headers, data=request.body.decode("utf-8"))
        return HtmlResponse(url=request.url, body=ret.text, encoding='utf-8', request=request)

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        if response.status != 200:
            spider.record_error(request, response)
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        print(response.status, response.url)
        return response


class FiddlerDownloaderMiddleware:

    def process_request(self, request, spider):
        proxy = "127.0.0.1:8080"
        request.meta['proxy'] = "http://%(proxy)s" % {'proxy': proxy}
        # # 用户名密码认证
        # request.headers['Proxy-Authorization'] = basic_auth_header('t15933522671761', 'xnyr1icq')  # 白名单认证可注释此行
        # request.headers["Connection"] = "close"

        if request.method == 'GET' and spider.download_by_driver == True:
            return spider.driver_get_page(request.url, request)
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        if response.status != 200:
            spider.record_error(request, response)
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        print(response.status, response.url)
        return response