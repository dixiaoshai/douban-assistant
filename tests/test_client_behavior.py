from __future__ import annotations

import unittest

import requests

from douban_assistant.douban import DoubanClient, DoubanFetchError, looks_like_login_page


class FakeSession:
    def __init__(self, exc: Exception | None = None) -> None:
        self.headers: dict[str, str] = {}
        self.trust_env = True
        self._exc = exc

    def get(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        raise AssertionError("FakeSession.get should only be used for exception tests")


class DoubanClientBehaviorTests(unittest.TestCase):
    def test_client_disables_env_proxy_inheritance(self) -> None:
        session = FakeSession()

        DoubanClient(session=session)

        self.assertFalse(session.trust_env)

    def test_fetch_collect_page_wraps_request_errors(self) -> None:
        session = FakeSession(exc=requests.exceptions.ReadTimeout("timed out"))
        client = DoubanClient(session=session)

        with self.assertRaises(DoubanFetchError) as context:
            client.fetch_collect_page("100654183")

        self.assertIn("Failed to fetch Douban page", str(context.exception))

    def test_login_page_detection_ignores_generic_app_download_copy(self) -> None:
        html = """
        <html>
          <body>
            <div id="top-nav-appintro">
              <p class="qrcode">扫码直接下载</p>
            </div>
            <title>我读过的书(242)</title>
          </body>
        </html>
        """

        self.assertFalse(looks_like_login_page(html))


if __name__ == "__main__":
    unittest.main()
