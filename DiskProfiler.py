import os
import threading
import time
import shutil


class DiskProfiler:
    def __init__(self, interval=0.001):
        self.path = os.getcwd()
        self.interval = interval
        self.running = False
        self.thread = None
        self.peak_used = 0
        self.increment = 0
        self._lock = threading.Lock()

    def _monitor(self):
        while self.running:
            with self._lock:
                self.peak_used = max(
                    self.peak_used, shutil.disk_usage(self.path).used)
            time.sleep(self.interval)

    def start(self):
        self.peak_used = shutil.disk_usage(self.path).used
        self.increment = self.peak_used
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.peak_used = self.peak_used / (1024**2)  # MB
        self.increment = (shutil.disk_usage(self.path).used -
                          self.increment) / (1024**2)  # MB


diskProfiler = DiskProfiler()
