import asyncio
import logging

from mongoengine.connection import get_connection
from nats.aio.client import Client as NATS
from pymilvus import MilvusClient
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def check_nats(nc: NATS | None) -> bool:
    """
    Check if NATS connection is healthy by flushing (sends PING, waits for PONG).
    """
    if nc is None:
        return False
    try:
        await nc.flush(timeout=5)
        return True
    except Exception as e:
        logger.debug(f"NATS health check failed: {e}")
        return False


def check_nats_sync(nc: NATS | None, loop: asyncio.AbstractEventLoop) -> bool:
    """
    Synchronous wrapper for NATS health check, for use in non-async contexts.
    """
    if nc is None:
        return False
    try:
        future = asyncio.run_coroutine_threadsafe(nc.flush(timeout=5), loop)
        future.result(timeout=5)
        return True
    except Exception as e:
        logger.debug(f"NATS health check failed: {e}")
        return False


async def check_redis(redis: Redis | None) -> bool:
    """
    Check if Redis connection is healthy by pinging the server.
    """
    if redis is None:
        return False
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
        return False


def check_redis_sync(redis: Redis | None, loop: asyncio.AbstractEventLoop) -> bool:
    """
    Synchronous wrapper for Redis health check, for use in non-async contexts.
    """
    if redis is None:
        return False
    try:
        future = asyncio.run_coroutine_threadsafe(redis.ping(), loop)
        return future.result(timeout=5)
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
        return False


def check_milvus(milvus_client: MilvusClient | None) -> bool:
    """
    Check if Milvus connection is healthy by listing collections.
    """
    if milvus_client is None:
        return False
    try:
        # list_collections is a lightweight operation to verify connectivity
        milvus_client.list_collections()
        return True
    except Exception as e:
        logger.debug(f"Milvus health check failed: {e}")
        return False


def check_mongodb() -> bool:
    """
    Check if MongoDB connection is available by pinging the admin database.

    Uses the global MongoEngine connection.
    """
    try:
        conn = get_connection()
        conn.admin.command("ping")
        return True
    except Exception as e:
        logger.debug(f"MongoDB health check failed: {e}")
        return False


def check_s3(s3_client: object | None) -> bool:
    """
    Check if S3 connection is healthy by listing buckets.
    """
    if s3_client is None:
        return False
    try:
        # list_buckets is a lightweight operation to verify connectivity
        s3_client.list_buckets()  # type: ignore[union-attr]
        return True
    except Exception as e:
        logger.debug(f"S3 health check failed: {e}")
        return False
