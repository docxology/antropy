# Copyright (c) 2026 Daniel Ari Friedman
"""Deterministic complete CSV projections of strict power decision and summary records."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from io import StringIO

from pydantic import BaseModel

from antropy_hd.orchestration import canonical_json
from scripts.power_models import PowerDecision, PowerSummary


@dataclass(frozen=True, slots=True)
class PowerCSV:
    """Ordered headers and canonical values; nulls and nested intervals remain explicit."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def text(self) -> str:
        """Serialize with the same newline contract across platforms."""
        stream = StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(self.headers)
        writer.writerows(self.rows)
        return stream.getvalue()


def _projection(records: Iterable[BaseModel], headers: tuple[str, ...]) -> PowerCSV:
    return PowerCSV(
        headers=headers,
        rows=tuple(
            tuple(canonical_json(record.model_dump(mode="json")[key]) for key in headers)
            for record in records
        ),
    )


def decision_csv(records: tuple[PowerDecision, ...]) -> PowerCSV:
    """Project every declared decision field, including full actual test provenance."""
    return _projection(records, tuple(PowerDecision.model_fields))


def summary_csv(records: tuple[PowerSummary, ...]) -> PowerCSV:
    """Project every summary field without dropping denominators or interval statuses."""
    return _projection(records, tuple(PowerSummary.model_fields))
