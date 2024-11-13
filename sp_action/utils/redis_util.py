import redis
from sp_action.utils.config_util import redis_config


class RedisClient:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.init_redis(redis_config)
        return cls._instance

    def init_redis(self, config):
        self.pool = redis.ConnectionPool(
            host=config['host'],
            port=config['port'],
            password=config['password'],
            db=config['db'],
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def get_client(self):
        return self.client


# redis_client = RedisClient().get_client()
