import subprocess
import csv
import time

def run_furmark(exe, width, height, msaa, duration, log_path):
    cmd = [exe,
           f"/width={width}",
           f"/height={height}",
           f"/msaa={msaa}",
           f"/benchmark={duration}",
           "/log"]
    with open(log_path, 'w') as lf:
        subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)

def save_noise_log(times, db_vals, out_csv):
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["second","dBFS"])
        w.writerows(zip(times, db_vals))

def save_fan_log(entries, out_csv):
    with open(out_csv, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["time_s","fan_pct"])
        w.writerows(entries)