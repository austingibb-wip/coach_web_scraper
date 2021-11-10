from unittest import TestCase
import sys
import time


def fail_with_message_to_file(message, file=sys.stderr):
    print(message, file=file)
    exit(-1)


def retry_function_sleep(fun, max_tries=10, sleep_time=0.3, on_exception=None):
    for i in range(max_tries):
        try:
            fun()
            return True
        except Exception as e:
            if on_exception:
                on_exception()
            time.sleep(sleep_time)
            continue
    return False


class _RetryTest(TestCase):
    def test_retry_success(self):
        run_count = 0
        max_retries = 3

        def fun():
            nonlocal run_count, max_retries
            run_count += 1
            if run_count < max_retries:
                raise Exception("Error case.")
            else:
                s = "batman senpai"

        result = retry_function_sleep(fun, max_retries)
        self.assertEqual(result, True)

    def test_retry_fail(self):
        run_count = 0
        max_retries = 3

        def fun():
            nonlocal run_count, max_retries
            run_count += 1
            if run_count < max_retries + 1:
                raise Exception("Error case.")
            else:
                s = "batman senpai"

        result = retry_function_sleep(fun, max_retries)
        self.assertEqual(result, False)
