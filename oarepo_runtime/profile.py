# profiling support
import atexit
import contextlib
import functools
import math
import time
from collections import Counter


class ProfilingTimer:
    def __init__(self):
        self.counts = Counter()
        self.sums = Counter()
        self.sums_squared = Counter()

    def time(self, function):
        @functools.wraps(function)
        def inner(*args, **kwargs):
            start = time.time()
            try:
                return function(*args, **kwargs)
            finally:
                stop = time.time()
                self.register(function, start, stop)

        return inner

    def register(self, function, start, stop):
        self.counts[function] += 1
        duration = stop - start
        self.sums[function] += duration
        self.sums_squared[function] += duration * duration

    @contextlib.contextmanager
    def time_block(self, name):
        start = time.time()
        try:
            yield
        finally:
            stop = time.time()
            self.register(name, start, stop)

    def display(self):
        for f in self.counts:
            print(f)
            print(f"Call count    :   {self.counts[f]}")
            print(f"Total time    :   {self.sums[f]}")
            print(f"Avg time      :   {self.sums[f] / self.counts[f]}")
            std_deviation = (
                math.sqrt(
                    self.counts[f] * self.sums_squared[f] - self.sums[f] * self.sums[f]
                )
                / self.counts[f]
            )
            print(f"Std deviation :   {std_deviation}")
            print()


timer = ProfilingTimer()
atexit.register(timer.display)
