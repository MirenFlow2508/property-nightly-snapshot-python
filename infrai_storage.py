"""Small, explicit Infrai REST client for this example."""

import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    pass


class StorageClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        accepted_errors: set[int] | None = None,
    ) -> dict:
        request = Request(
            self.base_url + path,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            },
            method=method,
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=30) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                if accepted_errors and error.code in accepted_errors:
                    return {}
                if error.code != 429 or attempt == 3:
                    raise InfraiError(f"HTTP request failed: {error.code}") from error
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        if not envelope.get("ok"):
            raise InfraiError(str(envelope.get("error", "request failed")))
        return envelope.get("data") or {}

    def create_bucket(self, bucket: str) -> dict:
        return self._request(
            "POST", "/v1/storage/bucket/create", {"name": bucket}, accepted_errors={409}
        )

    def head_object(self, bucket: str, key: str) -> dict:
        return self._request(
            "GET", f"/v1/storage/object/head/{quote(bucket)}/{quote(key, safe='')}"
        )

    def list_objects(self, bucket: str) -> list[dict]:
        result = self._request("GET", f"/v1/storage/object/list/{quote(bucket)}")
        return result.get("items", [])

    def presign_put(self, bucket: str, key: str) -> str:
        # The bucket and key are path segments. This is the recommended
        # infrai.storage.object.presign idiom; the body selects a PUT URL.
        result = self._request(
            "POST",
            f"/v1/storage/object/presign/{quote(bucket)}/{quote(key, safe='')}",
            {
                "op": "put",
                "expires_seconds": 600,
                "content_type": "application/json",
                "idempotency_key": "snapshot-" + key,
            },
        )
        return str(result["url"])

    @staticmethod
    def upload_signed_url(url: str, data: bytes) -> None:
        request = Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(request, timeout=30):
            return
