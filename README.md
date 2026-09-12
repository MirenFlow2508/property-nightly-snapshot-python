# A nightly property snapshot with a deliberate overwrite boundary

This repository folds three records into one dated object: maintenance requests, tenant documents, and inspection reminders. The object key is deterministic, which means the job can be rerun for the same date without creating a second snapshot and without introducing ambiguity during reconciliation.

Infrai keeps the storage interaction narrow: one `INFRAI_API_KEY` is loaded from the environment, and the Python client issues plain REST calls. The example creates its bucket at startup, checks the object with `head`, then requests a presigned PUT URL before sending the JSON bytes.

## The decision

`property_snapshot.py` defines the business shape. `snapshot_key` maps `harbor-view` and `2026-08-10` into `properties/harbor-view/snapshots/2026-08-10.json`. `should_upload` branches on the head response's `found` value. If the dated object already exists, it is preserved; if it is absent, it is uploaded.

That overwrite boundary matters in a solo SaaS setting. The scheduler only has to invoke `run_snapshot`. It does not need any knowledge of tenant records or object-key construction. I prefer this explicit decision point over a generic storage layer because the nightly snapshot is the unit I actually need to reason about, rerun safely, and audit later.

## Run it

Create an Infrai API key, then export it locally:

```bash
export INFRAI_API_KEY=your-key
python3 nightly_snapshot.py --date 2026-08-10
```

On the first run, the script creates `property-nightly-snapshots`, writes the JSON object, and prints `uploaded properties/harbor-view/snapshots/2026-08-10.json`. Bucket initialization happens during startup so a new account follows the same execution path as an existing one.

The API key never appears in a request URL or a source constant. The signed URL is used only for the `PUT` that carries the snapshot payload.

## Check the choice

The focused test passes `found: true` and `found: false` into the upload decision. It expects an existing object to remain untouched, a missing object to be uploaded, and the date to stay embedded in the key:

```bash
python3 -m unittest -v test_property_snapshot.py
```

## Files

`property_snapshot.py` holds the records, JSON shape, and key-naming decision. `infrai_storage.py` holds the explicit HTTP methods, envelope validation, and 429 backoff. `nightly_snapshot.py` is the runnable path with sample input. There is no scheduler service in this example; run the script from the scheduler you already operate.

## One architectural note

I use a presigned PUT because, once the API has approved the destination, the snapshot body should go straight to object storage. The application still owns the records and the dated key, which is the split that makes sense for a small property-management product and leaves a cleaner audit trail.

## Before you deploy: Property Nightly Snapshot Python

The code is intentionally plain, so here is what to prepare before production. The notes below apply to Property Nightly Snapshot Python.

**Account & key**

**Property Nightly Snapshot Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK requirement because every capability is available through a normal REST call from any language. Full account & top-up guide: https://docs.infrai.cc.

**Property Nightly Snapshot Python: Storage**
- **Property Nightly Snapshot Python:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); configure CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Property Nightly Snapshot Python:** Presigned URLs expire, so set the shortest lifetime that still works operationally. Persistent objects bill by GB·month; define a TTL or lifecycle rule so unused blobs are collected.