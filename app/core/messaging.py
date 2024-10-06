# app/core/messaging.py
import aio_pika
from core.config import settings
from urllib.parse import quote_plus

async def get_rabbitmq_connection():
    """
    Establishes a robust connection to RabbitMQ using the provided configuration.
    """
    username = quote_plus(settings.RABBITMQ_DEFAULT_USER)
    password = quote_plus(settings.RABBITMQ_DEFAULT_PASS)
    url = f"amqp://{username}:{password}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"

    connection = await aio_pika.connect_robust(url)
    return connection

async def publish_message(connection: aio_pika.RobustConnection, queue_name: str, message: str):
    """
    Publishes a message to the specified RabbitMQ queue.
    """
    async with connection.channel() as channel:
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=queue.name
        )
