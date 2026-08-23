"""Runnable nightly snapshot example."""

from datetime import date
import argparse

from infrai_storage import StorageClient
from property_snapshot import (
    InspectionReminder,
    MaintenanceRequest,
    TenantDocument,
    should_upload,
    snapshot_key,
    snapshot_payload,
)


BUCKET = "property-nightly-snapshots"


def sample_records() -> tuple[list[MaintenanceRequest], list[TenantDocument], list[InspectionReminder]]:
    return (
        [MaintenanceRequest("mr-104", "3B", "Replace leaking tap", "open")],
        [TenantDocument("doc-22", "3B", "lease", "2026-08-09")],
        [InspectionReminder("in-8", "3B", "2026-08-14", "Mina")],
    )


def run_snapshot(snapshot_date: date) -> str:
    client = StorageClient()
    client.create_bucket(BUCKET)
    maintenance, documents, inspections = sample_records()
    key = snapshot_key("harbor-view", snapshot_date)
    if should_upload(client.head_object(BUCKET, key)):
        body = snapshot_payload("harbor-view", maintenance, documents, inspections, snapshot_date)
        client.upload_signed_url(client.presign_put(BUCKET, key), body)
        return f"uploaded {key}"
    return f"already present {key}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write one property snapshot to object storage")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    print(run_snapshot(date.fromisoformat(args.date)))
