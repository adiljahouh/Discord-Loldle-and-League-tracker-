import time
import aiohttp


class TokenBucket:
    def __init__(self, max_tokens, fill_rate, window_size, window_duration):
        self.capacity = max_tokens
        self._tokens = max_tokens  # Start completely filled out
        self.fill_rate = fill_rate
        self.timestamp = time.time()
        self._sliding_logs = []
        self.window_size = window_size
        self.window_duration = window_duration

    def can_consume(self, tokens):
        if tokens <= self.tokens and len(self.sliding_logs) < self.window_size:
            self.tokens -= tokens
            self.sliding_logs.append(time.time())
            return True
        return False

    @property
    def tokens(self):
        if self._tokens < self.capacity:
            now = time.time()
            elapsed = now - self.timestamp
            self._tokens = min(self.capacity, self._tokens + elapsed * self.fill_rate)
            self.timestamp = now
        return self._tokens

    @tokens.setter
    def tokens(self, num):
        self._tokens = num

    @property
    def sliding_logs(self):
        now = time.time()
        indx = self.bin_search(self._sliding_logs, now - self.window_duration)
        self._sliding_logs = self._sliding_logs[indx:]
        return self._sliding_logs

    @sliding_logs.setter
    def sliding_logs(self, arr):
        self._sliding_logs = arr

    def bin_search(self, arr, target):
        start, end = 0, len(arr) - 1
        while start <= end:
            mid = (start + end) // 2
            if arr[mid] <= target:
                start = mid + 1
            else:
                if mid == 0 or arr[mid - 1] <= target:
                    return mid
                end = mid - 1
        return 0

    async def request(self, url, params=None):
        while not self.can_consume(1):
            # print(f"TIMEOUT, WAITING: {self._tokens}, {len(self._sliding_logs)}")
            time.sleep(1)
        # print("REQUEST SENT")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
