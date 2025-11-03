import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

# 为缺失的第三方依赖注入简单替身，避免测试环境安装真实包
if "fake_useragent" not in sys.modules:
    sys.modules["fake_useragent"] = SimpleNamespace(
        UserAgent=lambda: SimpleNamespace(random="test-agent")
    )
if "DrissionPage" not in sys.modules:
    sys.modules["DrissionPage"] = SimpleNamespace(
        SessionPage=object,
        SessionOptions=object,
    )

from cache import cache_manager
from query_ip import query_service


class TestIPCacheConcurrency(unittest.TestCase):
    def setUp(self) -> None:
        self.ip = "36.184.64.231"
        cache_manager.delete_cache(self.ip)

    def tearDown(self) -> None:
        cache_manager.delete_cache(self.ip)

    def test_concurrent_same_ip_query_only_hits_upstream_once(self) -> None:
        call_count = 0
        call_count_lock = threading.Lock()

        def fake_query(ip, *args, **kwargs):
            nonlocal call_count
            with call_count_lock:
                call_count += 1
            time.sleep(0.1)
            return {
                "ip": ip,
                "status": "success",
                "data": {"ip_info": "mocked"},
            }

        results = []
        threads = []

        with patch.object(query_service, "query_ip_with_httpx", side_effect=fake_query):
            for _ in range(5):
                thread = threading.Thread(
                    target=lambda: results.append(query_service.query_ip_with_cache(self.ip))
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        self.assertEqual(call_count, 1, "同一 IP 的并发查询应只触发一次远程调用")
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["data"], {"ip_info": "mocked"})
            self.assertIn("cached_at", result)


if __name__ == "__main__":
    unittest.main()
