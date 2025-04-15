import os

class Config:
    # Redis configurations
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)

    # RabbitMQ configurations
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

    # Database configurations (optional)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', 5432)
