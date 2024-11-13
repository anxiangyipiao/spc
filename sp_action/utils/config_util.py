# -*- coding: utf-8 -*-
import configparser
import os

class ConfigLoader:

    def __init__(self,config_file='config.ini'):
        current_dir = os.path.dirname(os.path.abspath(__file__)).split('utils')[0]
        self.config = configparser.ConfigParser()
        # 构建配置文件的绝对路径
        config_path = os.path.join(current_dir, config_file)
        self.config.read(config_path, encoding='utf-8')

    def get_redis_login_redirect(self):
        return {
            'host': self.config.get('redis_login_redirect', 'host'),
            'port': self.config.getint('redis_login_redirect', 'port'),
            'password': self.config.get('redis_login_redirect', 'password'),
            'db': self.config.getint('redis_login_redirect', 'db'),
        }

    def get_mysql(self):
        return {
            'server': self.config.get('mysql', 'server'),
            'port': self.config.getint('mysql', 'port'),
            'db': self.config.get('mysql', 'db'),
            'table': self.config.get('mysql', 'table'),
            'origin_table': self.config.get('mysql', 'origin_table'),
            'username': self.config.get('mysql', 'username'),
            'password': self.config.get('mysql', 'password')
        }

    def get_local(self):
        return {
            'env': self.config.get('local', 'env'),
            'notify_token': self.config.get('local', 'notify_token')
        }

    def get_ChaojiyingClient(self):
        return {
            'username': self.config.get('Chaojiying', 'username'),
            'password': self.config.get('Chaojiying', 'password'),
            'soft_id': self.config.getint('Chaojiying', 'soft_id')
        }



loader = ConfigLoader()
redis_config = loader.get_redis_login_redirect()
mysql_config = loader.get_mysql()
local_config = loader.get_local()
chaojiying_config = loader.get_ChaojiyingClient()


# print(redis_config)