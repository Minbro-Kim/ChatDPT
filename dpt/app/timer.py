import threading
import time

class Timer:
    def __init__(self, interval):
        self.interval = interval
        self.job = None

    def job(self, func):
        self.job = func
        self.start()

    def start(self):
        def run():
            while True:
                self.job()
                time.sleep(self.interval)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()