"""AWS S3 batch ingestion adapter (FR-004)."""

from __future__ import annotations

import io
import logging

import pandas as pd

from src.ingestion.adapters.base import (
    AdapterConfig,
    AuthConfigError,
    BatchAdapter,
    ConnectorError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = frozenset({".csv", ".xlsx", ".xls"})


class S3AdapterConfig(AdapterConfig):
    bucket: str
    prefix: str = ""
    region: str = "us-east-1"
    # Credentials via boto3 credential chain (env vars, IAM role, ~/.aws/credentials)


class S3Adapter(BatchAdapter[S3AdapterConfig]):
    """Load CSV/XLSX files from an S3 bucket into canonical DataFrames."""

    def load(self, config: S3AdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            try:
                s3 = boto3.client("s3", region_name=config.region)
            except NoCredentialsError as exc:
                raise AuthConfigError(
                    adapter=self._name, credential_env_var="AWS_ACCESS_KEY_ID"
                ) from exc

            frames = self._list_and_load(s3, config, ClientError, NoCredentialsError)
        except (AuthConfigError, UnsupportedFormatError, ConnectorError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise ConnectorError(adapter=self._name, cause=exc, attempts=1) from exc

        self._log_done(frames)
        return frames

    def _list_and_load(self, s3, config: S3AdapterConfig, ClientError, NoCredentialsError) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=config.bucket, Prefix=config.prefix):
            for obj in page.get("Contents", []):
                key: str = obj["Key"]
                suffix = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""
                if suffix not in _SUPPORTED_SUFFIXES:
                    logger.info("adapter=%s skipping unsupported key=%s", self._name, key)
                    continue
                stem = key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                body = s3.get_object(Bucket=config.bucket, Key=key)["Body"].read()
                if suffix == ".csv":
                    frames[stem] = pd.read_csv(io.BytesIO(body))
                else:
                    frames[stem] = pd.read_excel(io.BytesIO(body), engine="openpyxl")
        return frames
