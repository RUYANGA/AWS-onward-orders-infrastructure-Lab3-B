#!/usr/bin/env python3
"""Client check: the order system adds servers under load and removes them afterwards.

Sends concurrent order bookings for a few minutes (no third-party tools needed).
Watch the server count rise in another terminal:
  watch -n 15 aws autoscaling describe-auto-scaling-groups \
     --auto-scaling-group-names onward-dev-orders --query "AutoScalingGroups[0].DesiredCapacity"
Scale-out follows CPU > 50% within a few minutes; scale-in follows ~15 minutes of
low CPU after the test (target tracking removes servers more cautiously than it adds them).

Usage: 4-load-test.py http://<alb-dns> [minutes] [concurrency]
"""
import sys
import threading
import time
import urllib.parse
import urllib.request

url = sys.argv[1].rstrip("/")
minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 8
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 60
body = urllib.parse.urlencode({
    "merchant": "Load Test Ltd", "recipient_phone": "+2348000000000",
    "pickup_zone": "A", "dropoff_zone": "D", "weight_kg": "7", "speed": "express"}).encode()
stop = time.time() + minutes * 60
counts = {"ok": 0, "err": 0}
lock = threading.Lock()


def worker():
    while time.time() < stop:
        try:
            with urllib.request.urlopen(f"{url}/orders", data=body, timeout=10) as r:
                ok = r.status == 201
        except Exception:
            ok = False
        with lock:
            counts["ok" if ok else "err"] += 1


threads = [threading.Thread(target=worker, daemon=True) for _ in range(workers)]
for t in threads:
    t.start()
while time.time() < stop:
    time.sleep(15)
    print(time.strftime("%H:%M:%S"), counts, flush=True)
print("done", counts)
