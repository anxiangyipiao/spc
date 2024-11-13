import hashlib
import requests
from sp_action.utils.config_util import chaojiying_config

class ChaojiyingClient:
    def __init__(self):

        self.password = self._md5(chaojiying_config['password'].encode('utf-8'))
        self.base_params = {
            'user': chaojiying_config['username'],
            'pass2': self.password,
            'softid': chaojiying_config['soft_id'],
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    @staticmethod
    def _md5(data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()

    def post_pic(self, im, codetype):
        """
        根据字节信息传输图片
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, timeout=20, files=files, headers=self.headers)
        return r.json()

    def post_pic_base64(self, base64_str, codetype):
        """
        根据图片的base64传输图片
        base64_str: 图片的base64字符
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
            'file_base64': base64_str
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, headers=self.headers)
        return r.json()

    def report_error(self, im_id):
        """
        报告错误
        im_id: 报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, timeout=20, headers=self.headers)
        return r.json()



# chaojiying = ChaojiyingClient()

