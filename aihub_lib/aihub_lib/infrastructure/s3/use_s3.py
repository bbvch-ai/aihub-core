import boto3
import s3fs
from botocore.config import Config
from fastapi import Request
from mypy_boto3_s3 import S3Client

from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings


def use_s3(request: Request) -> S3Client:
    """FastAPI dependency that provides the S3 client from app state."""
    return request.app.state.s3_client


def use_s3_public(request: Request) -> S3Client:
    """FastAPI dependency that provides the public S3 client for presigned URLs."""
    return request.app.state.s3_public_client


def use_s3_service(request: Request) -> S3AnonymousFileAccessService:
    """FastAPI dependency that provides the S3 file access service with injected clients."""
    return S3AnonymousFileAccessService(
        s3_client=request.app.state.s3_client,
        s3_public_client=request.app.state.s3_public_client,
        s3_settings=request.app.state.s3_settings,
    )


def create_s3_service() -> S3AnonymousFileAccessService:
    """
    Factory function to create S3AnonymousFileAccessService with default settings.

    Use this when dependency injection is not available (e.g., in cached static methods).
    For FastAPI endpoints, prefer using the `use_s3_service` dependency.
    """
    settings = S3StorageSettings()
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.ENDPOINT,
        aws_access_key_id=settings.ACCESS_KEY,
        aws_secret_access_key=settings.SECRET_KEY.get_secret_value(),
        region_name=settings.REGION,
        config=Config(signature_version="s3v4"),
    )
    s3_public_client = boto3.client(
        "s3",
        endpoint_url=settings.get_public_endpoint(),
        aws_access_key_id=settings.ACCESS_KEY,
        aws_secret_access_key=settings.SECRET_KEY.get_secret_value(),
        region_name=settings.REGION,
        config=Config(signature_version="s3v4"),
    )
    return S3AnonymousFileAccessService(
        s3_client=s3_client,
        s3_public_client=s3_public_client,
        s3_settings=settings,
    )


def create_s3_filesystem() -> s3fs.S3FileSystem:
    """
    Factory function to create an S3FileSystem for file operations.

    Used by document loaders and API services that need to read/write files
    to S3-compatible storage (MinIO, SeaweedFS, AWS S3).

    """
    s3_config = S3StorageSettings()

    client_kwargs = {
        "region_name": s3_config.REGION,
        "endpoint_url": s3_config.ENDPOINT,
    }

    config_kwargs = {
        "signature_version": "s3v4",
        "retries": {"max_attempts": 3},
    }

    return s3fs.S3FileSystem(
        key=s3_config.ACCESS_KEY,
        secret=s3_config.SECRET_KEY.get_secret_value(),
        client_kwargs=client_kwargs,
        config_kwargs=config_kwargs,
        anon=False,
    )
