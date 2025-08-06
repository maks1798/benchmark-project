#!/usr/bin/env python3
import os
import toml
import numpy as np
import time
import threading
import soundfile as sf
from datetime import datetime
from shutil import which

from utils.gpu_utils import dump_card_info, poll_gpu_metrics
from utils.audio_utils import record_audio, save_wav, compute_rms_dbfs
from utils.benchmark_utils import run_furmark, save_noise_log, save_fan_log

# ─── Load config ─────────────────────────────────────────────────────────────┐
cfg = toml.load("config.toml")
bm, au, an = cfg["benchmark"], cfg["audio"], cfg["analysis"]
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Resolve and verify FurMark executable ───────────────────────────────────┐
exe = bm["exe_path"]
# If user provided just the name, try to find it on PATH
if not os.path.isabs(exe):
    found = which(exe)
    if found:
        exe = found
# Fallback: treat as relative to cwd
if not os.path.isfile(exe):
    print(f"Error: FurMark executable not found at `{bm['exe_path']}`.")
    print("Please set `exe_path` in config.toml to the full path or ensure it's on your PATH.")
    exit(1)
bm["exe_path"] = exe
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Create timestamped run folder ────────────────────────────────────────────┐
timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
data_root   = bm.get("data_root", "data")
run_folder  = os.path.join(data_root, timestamp)
os.makedirs(run_folder, exist_ok=True)
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Prepare output paths ─────────────────────────────────────────────────────┐
log_path         = os.path.join(run_folder, bm["log_path"])
wav_out          = os.path.join(run_folder, au["wav_out"])
noise_csv        = os.path.join(run_folder, an["noise_log_csv"])
spectrum_csv     = os.path.join(run_folder, an["spectrum_csv"])
card_info_xml    = os.path.join(run_folder, "card_info.xml")
gpu_metrics_csv  = os.path.join(run_folder, "gpu_metrics.csv")
# ──────────────────────────────────────────────────────────────────────────────┘

print(f"Starting benchmark; outputs will go to: {run_folder}")
print(f"Using FurMark executable: {exe}")

# ─── Dump full card info via nvidia-smi ───────────────────────────────────────┐
dump_card_info(card_info_xml)
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Prepare audio buffer ─────────────────────────────────────────────────────┐
total_samples = int(bm["duration"] * au["fs"])
audio_buf     = np.zeros((total_samples, au["channels"]), dtype="float32")
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Start audio recording thread ─────────────────────────────────────────────┐
record_thread = threading.Thread(
    target=record_audio,
    args=(bm["duration"], au["fs"], au["channels"], audio_buf),
    daemon=True
)
record_thread.start()
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Start GPU metrics logging thread ────────────────────────────────────────┐
gpu_thread = threading.Thread(
    target=poll_gpu_metrics,
    args=(gpu_metrics_csv, 1, bm["duration"]),
    daemon=True
)
gpu_thread.start()
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Run FurMark CLI benchmark ────────────────────────────────────────────────┐
run_furmark(
    bm["exe_path"],
    bm["width"],
    bm["height"],
    bm["msaa"],
    bm["duration"],
    log_path
)
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Wait for recording & logging to finish ──────────────────────────────────┐
record_thread.join()
gpu_thread.join()
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Save full audio to WAV ──────────────────────────────────────────────────┐
save_wav(audio_buf, au["fs"], wav_out)
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Compute & save per-second noise (dBFS) ──────────────────────────────────┐
rms_db = compute_rms_dbfs(audio_buf, au["fs"])
times  = list(range(bm["duration"]))
save_noise_log(times, rms_db, noise_csv)
# ──────────────────────────────────────────────────────────────────────────────┘

# ─── Final summary ────────────────────────────────────────────────────────────┐
print("Run complete:")
print(f" - FurMark log:     {log_path}")
print(f" - Audio WAV:       {wav_out}")
print(f" - Noise CSV:       {noise_csv}")
print(f" - Card info XML:   {card_info_xml}")
print(f" - GPU metrics CSV: {gpu_metrics_csv}")
# ──────────────────────────────────────────────────────────────────────────────┘
