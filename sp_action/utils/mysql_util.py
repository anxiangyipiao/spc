# -*- coding: utf-8 -*-
import pymysql
from pymysql.err import MySQLError
from sp_action.utils.config_util import mysql_config

class MySQLClient:
    
    def __init__(self, host=mysql_config['server'],
                    port=mysql_config['port'],
                    user=mysql_config['username'],
                    password=mysql_config['password'],
                    database=mysql_config['db']
                ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connect()

    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                # cursorclass=pymysql.cursors.DictCursor
            )
            print("Connected to MySQL database")
            
        except MySQLError as e:
            print(f"Error connecting to MySQL database: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("Connection closed")

    def insert_item_to_origin(self, item):
        """
        插入或更新数据项。

        :param table_name: 表名
        :param item: 包含键值对的字典
        """
        table_name = mysql_config['origin_table']

        item.pop('entry_time')

        keys = list(item.keys())
        values = list(item.values())

        key_str = ','.join(['`%s`' % k for k in keys])
        values_str = ','.join(['%s'] * len(values))
        update_str = ','.join([f'`{k}`=%s' for k in keys])

        sql = f'INSERT INTO `{table_name}` ({key_str}) VALUES ({values_str}) ON DUPLICATE KEY UPDATE {update_str}'

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, values + values)
                self.connection.commit()
                print(f'----- 插入/更新成功: -----')
        except MySQLError as e:
            print(f'----- 插入/更新失败: {e} -----')
            self.connection.rollback()


    def insert_item_to_simple(self, item):
        """
        插入或更新数据项。

        :param table_name: 表名
        :param item: 包含键值对的字典
        """
        table_name = mysql_config['table']

        item.pop('contents')
        item.pop('entry_time')

        keys = list(item.keys())
        values = list(item.values())

        key_str = ','.join(['`%s`' % k for k in keys])
        values_str = ','.join(['%s'] * len(values))
        update_str = ','.join([f'`{k}`=%s' for k in keys])

        sql = f'INSERT INTO `{table_name}` ({key_str}) VALUES ({values_str}) ON DUPLICATE KEY UPDATE {update_str}'

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, values + values)
                self.connection.commit()
                print(f'----- 插入/更新成功: -----')
        except MySQLError as e:
            print(f'----- 插入/更新失败: {e} -----')
            self.connection.rollback()


    def get_filter_title(self):

        filter_titles = []
        
        with self.connection.cursor() as cursor:

            cursor.execute('SELECT contains_keyword FROM c_contains_keyword')
            results = cursor.fetchall()
            for row in results:
                filter_titles.append(row[0])
            
            return filter_titles
    
    def get_important_title(self):

        important_title = ['变压器', '主变', '油浸', '油变', '35KV', '中性点', '整流变', '配变', '厂用变', '变电站','66KV', '10KV', '220KV']

        return important_title