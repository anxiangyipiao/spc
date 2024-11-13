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
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Connected to MySQL database")
        except MySQLError as e:
            print(f"Error connecting to MySQL database: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("Connection closed")

    def execute_query(self, query, params=None):
        """执行查询操作"""
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchall()
                return result
        except MySQLError as e:
            print(f"Error executing query: {e}")
            return []

    def execute_insert(self, query, params=None):
        """执行插入操作"""
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.connection.commit()
                return cursor.lastrowid
        except MySQLError as e:
            print(f"Error executing insert: {e}")
            self.connection.rollback()
            return None

    def execute_update(self, query, params=None):
        """执行更新操作"""
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.connection.commit()
                return cursor.rowcount
        except MySQLError as e:
            print(f"Error executing update: {e}")
            self.connection.rollback()
            return 0

    def execute_delete(self, query, params=None):
        """执行删除操作"""
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self.connection.commit()
                return cursor.rowcount
        except MySQLError as e:
            print(f"Error executing delete: {e}")
            self.connection.rollback()
            return 0

    def insert_item_to_origin(self, item):
        """
        插入或更新数据项。

        :param table_name: 表名
        :param item: 包含键值对的字典
        """
        table_name = mysql_config['origin_table']

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



if __name__ == '__main__':
    mysql_client = MySQLClient()
    mysql_client.connect()
    query = "SELECT * FROM users"
    result = mysql_client.execute_query(query)
    print(result)
    mysql_client.close()