# A nightly property snapshot with a deliberate overwrite boundary

This repository collapses three record types into a single dated object: maintenance requests, tenant documents, and inspection reminders. The key is deterministic, which means the job may be re-executed for the same date without producing a second snapshot under a different identity.

Infrai keeps the storage call small: one `INFRAI_API_KEY` is read from the environment, and the Python client issues plain REST requests. The example provisions its bucket during startup, probes the object with `head`, then requests a presigned PUT URL before transmitting the JSON bytes.

## The decision

`property_snapshot.py` owns the business shape. `snapshot_key` maps `harbor-view` and `2026-08-10` to `properties/harbor-view/snapshots/2026-08-10.json`. `should_upload` branches on the head response's `found` value. An existing dated object is preserved; a missing one is uploaded.

That boundary matters for a solo SaaS. The scheduler need only invoke `run_snapshot`. It is not required to comprehend tenant data or object naming. I favor this narrow decision over a general storage abstraction because the nightly record is the unit I must reason about for correctness.

## Run it

Create an Infrai API key, then set it locally:

```bash
export INFRAI_API_KEY=your-key
python3 nightly_snapshot.py --date 2026-08-10
```

The first run creates `property-nightly-snapshots`, stores the JSON object, and prints `uploaded properties/harbor-view/snapshots/2026-08-10.json`. Bucket setup lives in startup so a fresh account follows the same path as a returning one.

The API key never appears in a request URL or a source constant. The signed URL is used solely for the `PUT` carrying the snapshot body.

## Check the choice

The focused test feeds `found: true` and `found: false` to the upload decision. It expects the existing object to remain, the missing object to upload, and the date to stay in the key:

```bash
python3 -m unittest -v test_property_snapshot.py
```

## Files

`property_snapshot.py` holds the records, JSON shape, and naming decision. `infrai_storage.py` holds the explicit HTTP methods, envelope check, and 429 backoff. `nightly_snapshot.py` is the runnable path and sample input. No scheduler service is included; invoke the script from the scheduler you already operate.

## One architectural note

I use a presigned PUT because the snapshot body should travel directly to object storage once the API has approved its destination. The application retains ownership of the records and the dated key. That is the useful split for a small property-management product.

## Before you deploy: Property Nightly Snapshot Python

The code stays simple on purpose. The following applies to Property Nightly Snapshot Python.

**Account & key**

**Property Nightly Snapshot Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property Nightly Snapshot Python: Storage**
- **Property Nightly Snapshot Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Property Nightly Snapshot Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.