from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier
import unittest

from public_usage import PublicUsage, UsageLimitError


class PublicUsageTests(unittest.TestCase):
    def test_session_and_shared_cap(self):
        usage = PublicUsage(per_session=2, global_daily=3)
        for _ in range(2):
            with usage.reserve("a"):
                pass
        with self.assertRaises(UsageLimitError), usage.reserve("a"):
            self.fail("must not call API")
        with usage.reserve("b"):
            pass
        with self.assertRaises(UsageLimitError), usage.reserve("c"):
            self.fail("must not call API")

    def test_failure_is_charged_but_releases_lease(self):
        usage = PublicUsage(per_session=2)
        with self.assertRaises(RuntimeError), usage.reserve("a"):
            raise RuntimeError("synthetic backend failure")
        with usage.reserve("a"):
            pass
        with self.assertRaises(UsageLimitError), usage.reserve("a"):
            pass

    def test_same_session_cannot_overlap(self):
        usage = PublicUsage()
        with usage.reserve("a"):
            with self.assertRaises(UsageLimitError), usage.reserve("a"):
                pass
            with usage.reserve("b"):
                pass

    def test_global_limit_is_atomic_under_concurrency(self):
        usage = PublicUsage(global_daily=5)
        barrier = Barrier(12)
        def request(index):
            barrier.wait()
            try:
                with usage.reserve(str(index)):
                    return True
            except UsageLimitError:
                return False
        with ThreadPoolExecutor(max_workers=12) as pool:
            self.assertEqual(sum(pool.map(request, range(12))), 5)

    def test_utc_rollover_does_not_clear_active_lease(self):
        instant = [datetime(2026, 10, 14, 23, 59, tzinfo=timezone.utc)]
        usage = PublicUsage(per_session=1, clock=lambda: instant[0])
        with usage.reserve("a"):
            instant[0] += timedelta(minutes=2)
            with self.assertRaises(UsageLimitError), usage.reserve("a"):
                pass
        with usage.reserve("a"):
            pass

    def test_expired_request_cannot_release_new_lease(self):
        now = [0]
        usage = PublicUsage(timer=lambda: now[0])
        first = usage.reserve("a")
        first.__enter__()
        now[0] = 600
        with usage.reserve("a"):
            first.__exit__(None, None, None)
            with self.assertRaises(UsageLimitError), usage.reserve("a"):
                pass
        with usage.reserve("a"):
            pass

    def test_invalid_identity_fails_closed(self):
        for value in (None, "", 12):
            with self.assertRaises(UsageLimitError), PublicUsage().reserve(value):
                pass


if __name__ == "__main__":
    unittest.main()
