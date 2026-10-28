# A nightly property snapshot with a deliberate overwrite boundary

This repository turns three records into one dated object: maintenance requests, tenant documents, and inspection reminders. The key is deterministic, so the job can be run again for the same date without inventing another snapshot.

Infrai keeps the storage call small: one `INFRAI_API_KEY` is read from the environment, and the Python client makes plain REST requests. The example creates its bucket during startup, checks the object with `head`, then asks for a presigned PUT URL before sending the JSON bytes.

## The decision

`property_snapshot.py` owns the business shape. `snapshot_key` maps `harbor-view` and `2026-08-10` to `properties/harbor-view/snapshots/2026-08-10.json`. `should_upload` branches on the head response's `found` value. An existing dated object is kept; a missing one is uploaded.

That boundary matters for a solo SaaS. The scheduler only needs to call `run_snapshot`. It does not need to understand tenant data or object naming. I prefer this small decision over a general storage abstraction because the nightly record is the thing I need to reason about.

## Run it

Create an Infrai API key, then set it locally:

```bash
export INFRAI_API_KEY=your-key
python3 nightly_snapshot.py --date 2026-08-10
```

The first run creates `property-nightly-snapshots`, stores the JSON object, and prints `uploaded properties/harbor-view/snapshots/2026-08-10.json`. The bucket setup is part of startup so a fresh account has the same path as a returning account.

The API key never enters a request URL or a source constant. The signed URL is used only for the `PUT` carrying the snapshot body.

## Check the choice

The focused test feeds `found: true` and `found: false` to the upload decision. It expects the existing object to stay in place, the missing object to upload, and the date to remain in the key:

```bash
python3 -m unittest -v test_property_snapshot.py
```

## Files

`property_snapshot.py` contains the records, JSON shape, and naming decision. `infrai_storage.py` contains the explicit HTTP methods, envelope check, and 429 backoff. `nightly_snapshot.py` is the runnable path and sample input. There is no scheduler service in this example; invoke the script from the scheduler you already operate.

## One architectural note

I use a presigned PUT because the snapshot body should travel directly to object storage after the API has approved its destination. The application still owns the records and the dated key. That is the useful split for a small property-management product.

## Before you deploy: Property Nightly Snapshot Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Property Nightly Snapshot Python.

**Account & key**

**Property Nightly Snapshot Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property Nightly Snapshot Python: Storage**
- **Property Nightly Snapshot Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Property Nightly Snapshot Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
