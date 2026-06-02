from __future__ import annotations

import pandera.pandas as pa


def utc_timestamp_column(nullable: bool = False) -> pa.Column:
    """Return a Pandera Column that accepts any UTC-aware datetime regardless of resolution."""
    return pa.Column(
        checks=pa.Check(
            lambda s: hasattr(s, "dt") and s.dt.tz is not None,
            error="timestamp must be timezone-aware (UTC)",
        ),
        nullable=nullable,
    )
