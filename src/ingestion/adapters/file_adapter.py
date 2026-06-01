"""File upload adapter: CSV (UTF-8, UTF-8-BOM) and XLSX (FR-002)."""

from __future__ import annotations

import pathlib

import pandas as pd

from src.ingestion.adapters.base import (
    AdapterConfig,
    BatchAdapter,
    EncodingError,
    SchemaMismatchError,
    UnsupportedFormatError,
)

_SUPPORTED_SUFFIXES = frozenset({".csv", ".xlsx", ".xls"})


class FileAdapterConfig(AdapterConfig):
    path: str
    encoding: str = "utf-8"


class FileAdapter(BatchAdapter[FileAdapterConfig]):
    """Load CSV or XLSX files into canonical DataFrames.

    CSV: reads one file that must contain all required tables as a flat export
    OR a directory where each file stem matches a canonical table name.
    XLSX: one sheet per canonical table name.
    """

    def load(self, config: FileAdapterConfig) -> dict[str, pd.DataFrame]:
        self._log_start()
        try:
            frames = self._read(config)
        except (UnsupportedFormatError, EncodingError, SchemaMismatchError):
            raise
        except Exception as exc:
            self._log_error(exc)
            raise
        self._log_done(frames)
        return frames

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read(self, config: FileAdapterConfig) -> dict[str, pd.DataFrame]:
        p = pathlib.Path(config.path)
        suffix = p.suffix.lower()

        if p.is_dir():
            return self._read_directory(p, config.encoding)

        if suffix not in _SUPPORTED_SUFFIXES:
            raise UnsupportedFormatError(adapter=self._name, detected_type=suffix or "(no extension)")

        if suffix in (".xlsx", ".xls"):
            return self._read_xlsx(p)

        return self._read_csv_single(p, config.encoding)

    def _read_directory(self, directory: pathlib.Path, encoding: str) -> dict[str, pd.DataFrame]:
        frames: dict[str, pd.DataFrame] = {}
        for f in sorted(directory.iterdir()):
            suffix = f.suffix.lower()
            if suffix not in _SUPPORTED_SUFFIXES:
                continue
            if suffix in (".xlsx", ".xls"):
                frames.update(self._read_xlsx(f))
            else:
                frames[f.stem] = self._read_csv_file(f, encoding)
        return frames

    def _read_xlsx(self, path: pathlib.Path) -> dict[str, pd.DataFrame]:
        try:
            xl = pd.ExcelFile(path, engine="openpyxl")
        except Exception as exc:
            raise UnsupportedFormatError(
                adapter=self._name, detected_type=path.suffix
            ) from exc
        return {sheet: xl.parse(sheet) for sheet in xl.sheet_names}

    def _read_csv_single(self, path: pathlib.Path, encoding: str) -> dict[str, pd.DataFrame]:
        df = self._read_csv_file(path, encoding)
        return {path.stem: df}

    def _read_csv_file(self, path: pathlib.Path, encoding: str) -> pd.DataFrame:
        # Handle UTF-8-BOM transparently
        enc = "utf-8-sig" if encoding.lower() in ("utf-8", "utf-8-sig") else encoding
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as exc:
            raise EncodingError(
                adapter=self._name,
                path=str(path),
                detected_encoding=encoding,
            ) from exc
