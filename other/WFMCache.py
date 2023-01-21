import aiohttp, time, datetime
from .wf import errors

class WFMCache:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.cache = {"pc": {}, "xbox": {}, "switch": {}, "ps4": {}}
        self.cache_time = {"pc": {}, "xbox": {}, "switch": {}, "ps4": {}}

        self.do_debug = True

    async def _request(self, path: str, max_cache_age=200, platform="pc", params=None):
        if path in self.cache[platform] and max_cache_age > (time.time() - self.cache_time[platform][path]):
            if self.do_debug:
                print(f"Used cached value for {path} at {datetime.datetime.now()}")
            return self.cache[platform][path]

        headers = {"Platform": platform}
        async with self.session.get(path, headers=headers, params=params) as response:
            if self.do_debug:
                print(f"Used live value for {path} at {datetime.datetime.now()}")
            if response.status == 200:
                json = await response.json()
                self.cache_time[platform][path] = time.time()
                self.cache[platform][path] = json
            else:
                raise errors.APIError()

            return json
