from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, ConsumerRecord
from typing import Optional, Any
from functools import lru_cache
from settings import settings

import json
import logging
from datetime import datetime, timedelta


TOPIC_NAME = "notification_events"
GROUP_ID = "base-backend"


def key_serializer(value: Optional[str]):
    if value is None:
        return None
    return value.encode("UTF-8")


def key_deserializer(value: Optional[bytes]):
    if value is None:
        return None
    return value.decode("UTF-8")


def value_serializer(obj: Optional[Any]):
    def _default(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, timedelta):
            return value.total_seconds()
        try:
            return str(value)
        except:
            return "(Unsupported json type)"

    if obj is None:
        return None

    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=_default).encode(
        "UTF-8"
    )


def value_deserializer(value: Optional[bytes]):
    if value is None:
        return None
    return json.loads(value.decode("UTF-8"))


@lru_cache()
def producer():
    return AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_HOSTS.split(","),
        key_serializer=key_serializer,
        value_serializer=value_serializer,
    )


@lru_cache()
def consumer():
    return AIOKafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=settings.KAFKA_HOSTS.split(","),
        group_id=GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        key_deserializer=key_deserializer,
        value_deserializer=value_deserializer,
    )


async def producer_start():
    kafka = producer()
    logging.info("Starting producer...")
    await kafka.start()


async def producer_stop():
    kafka1 = producer()
    logging.info("Stopping producer...")
    await kafka1.stop()


async def consumer_start():
    kafka = consumer()
    logging.info("Starting consumer...")
    await kafka.start()


async def consumer_stop():
    kafka = consumer()
    logging.info("Stopping consumer...")
    await kafka.stop()
