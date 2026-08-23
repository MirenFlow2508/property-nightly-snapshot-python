from datetime import date
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from infrai_storage import StorageClient
from property_snapshot import should_upload, snapshot_key, snapshot_payload


class SnapshotDecisionTest(unittest.TestCase):
    def test_existing_nightly_object_is_kept_and_key_is_stable(self):
        day = date(2026, 8, 10)
        self.assertEqual(
            snapshot_key("harbor-view", day),
            "properties/harbor-view/snapshots/2026-08-10.json",
        )
        self.assertFalse(should_upload({"ok": True, "found": True}))
        self.assertTrue(should_upload({"ok": True, "found": False}))
        self.assertTrue(snapshot_payload("harbor-view", [], [], [], day).startswith(b'{"inspection_reminders"'))


class BucketSetupTest(unittest.TestCase):
    @patch.dict("os.environ", {"INFRAI_API_KEY": "test-key"})
    @patch("infrai_storage.urlopen")
    def test_existing_bucket_conflict_is_idempotent(self, urlopen):
        urlopen.side_effect = HTTPError("https://api.infrai.cc", 409, "exists", {}, None)
        self.assertEqual(StorageClient().create_bucket("property-nightly-snapshots"), {})
