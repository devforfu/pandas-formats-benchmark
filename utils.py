import gc
from multiprocessing import Process, Event, Value
import os
import time
from timeit import default_timer

import matplotlib.pyplot as plt
import numpy as np
import psutil


class Timer:
    """Simple util to measure execution time.
    Examples
    --------
    >>> import time
    >>> with Timer() as timer:
    ...     time.sleep(1)
    >>> print(timer)
    00:00:01
    """
    def __init__(self):
        self.start = None
        self.elapsed = None

    def __enter__(self):
        self.start = default_timer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = default_timer() - self.start

    def __str__(self):
        return self.verbose()

    def __float__(self):
        return self.elapsed

    def verbose(self):
        if self.elapsed is None:
            return '<not-measured>'
        return self.format_elapsed_time(self.elapsed)

    @staticmethod
    def format_elapsed_time(value: float):
        return time.strftime('%H:%M:%S', time.gmtime(value))
    
    
class MemoryTrackingProcess(Process):
    """A process that periodically measures the amount of RAM consumed by another process.
    
    This process is stopped as soon as the event is set.
    """
    def __init__(self, pid, event, **kwargs):
        super().__init__()
        self.p = psutil.Process(pid)
        self.event = event
        self.max_mem = Value('f', 0.0)
        
    def run(self):
        mem_usage = []
        while not self.event.is_set():
            info = self.p.memory_info()
            mem_bytes = info.rss
            mem_usage.append(mem_bytes)
            time.sleep(0.05)
        self.max_mem.value = np.max(mem_usage)


class MemoryTracker:
    """A context manager that runs MemoryTrackingProcess in background and collects 
    the information about used memory when the context is exited.
    """
    def __init__(self, pid=None):
        pid = pid or os.getpid()
        self.start_mem = psutil.Process(pid).memory_info().rss
        self.event = Event()
        self.p = MemoryTrackingProcess(pid, self.event)
    
    @property
    def memory(self):
        return self.p.max_mem.value - self.start_mem
    
    def __enter__(self):
        self.p.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.event.set()
        self.p.join()

        
class GC:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, ext_tb):
        self.collected = gc.collect()
        

class VisualStyle:
    def __init__(self, config, default=None):
        if default is None:
            default = plt.rcParams
        self.default = default.copy()
        self.config = config
        
    def replace(self):
        plt.rcParams = self.config
    
    def override(self, extra=None):
        plt.rcParams.update(self.config)
        if extra is not None:
            plt.rcParams.update(extra)

    def restore(self):
        plt.rcParams = self.default


class NotebookStyle(VisualStyle):
    def __init__(self):
        super().__init__({
            'figure.figsize': (11, 8),
            'axes.titlesize': 20,
            'axes.labelsize': 18,
            'xtick.labelsize': 14,
            'ytick.labelsize': 14,
            'font.size': 16
        })
