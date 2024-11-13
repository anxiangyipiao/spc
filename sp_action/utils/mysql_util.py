import pymysql
from pymysql.err import MySQLError

class MySQLUtil:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

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

