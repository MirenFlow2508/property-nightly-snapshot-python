"""Build the nightly property-management snapshot and decide its object key."""

from dataclasses import asdict, dataclass
from datetime import date
import json
from typing import Any, Iterable


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    unit: str
    summary: str
    status: str


@dataclass(frozen=True)
class TenantDocument:
    document_id: str
    unit: str
    kind: str
    received_on: str


@dataclass(frozen=True)
class InspectionReminder:
    reminder_id: str
    unit: str
    due_on: str
    inspector: str


def snapshot_payload(
    property_id: str,
    maintenance: Iterable[MaintenanceRequest],
    documents: Iterable[TenantDocument],
    inspections: Iterable[InspectionReminder],
    snapshot_date: date,
) -> bytes:
    """Return stable JSON bytes so the same night's input has one object body."""
    payload: dict[str, Any] = {
        "property_id": property_id,
        "snapshot_date": snapshot_date.isoformat(),
        "maintenance_requests": [asdict(item) for item in maintenance],
        "tenant_documents": [asdict(item) for item in documents],
        "inspection_reminders": [asdict(item) for item in inspections],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def snapshot_key(property_id: str, snapshot_date: date) -> str:
    """Use a deterministic key: rerunning the nightly job replaces one snapshot."""
    return f"properties/{property_id}/snapshots/{snapshot_date.isoformat()}.json"


def should_upload(head_result: dict[str, Any]) -> bool:
    """Upload only when the object is absent; this makes the job repeatable."""
    return not bool(head_result.get("found", False))
