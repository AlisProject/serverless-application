import time


class TimeUtil:
    @staticmethod
    def generate_sort_key():
        return int(time.time() * 1000000)
