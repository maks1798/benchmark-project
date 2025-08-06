#!/usr/bin/env python3
import os, toml, numpy as np, time, threading
import soundfile as sf
from datetime import datetime
from utils.gpu_utils import init_nvml, poll_fan_speed, dump_card_info
from utils.audio_utils import record_audio, save_wav, compute_rms_dbfs
from utils.benchmark_utils import run_furmark, save_noise_log, save_fan_log

# Load config
cfg = toml.load("config.toml")
bm, au, an = cfg['benchmark'], cfg['audio'], cfg['analysis']

# Create timestamped run folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
data_root = bm.get('data_root', 'data')
run_folder = os.path.join(data_root, timestamp)
os.makedirs(run_folder, exist_ok=True)

# Paths for this run
log_path       = os.path.join(run_folder, bm['log_path'])
wav_out        = os.path.join(run_folder, au['wav_out'])
noise_csv      = os.path.join(run_folder, an['noise_log_csv'])
spectrum_csv   = os.path.join(run_folder, an['spectrum_csv'])
fan_csv        = os.path.join(run_folder, 'fan_log.csv')
card_info_json = os.path.join(run_folder, 'card_info.json')

print(f"Starting benchmark; outputs will go to: {run_folder}")

# Init NVML & dump card info
handle = init_nvml()
dump_card_info(handle, card_info_json)

# Prepare audio buffer
total_samples = int(bm['duration'] * au['fs'])
audio_buf     = np.zeros((total_samples, au['channels']), dtype='float32')

# Start audio recording in background
record_thread = threading.Thread(
    target=record_audio,
    args=(bm['duration'], au['fs'], au['channels'], audio_buf)
)
record_thread.start()

# Poll fan speeds in parallel (1 Hz)
t_start = time.time()
fan_log = []
while time.time() - t_start < bm['duration']:
    fan_log.append((time.time() - t_start, poll_fan_speed(handle)))
    time.sleep(1.0)

# Run FurMark benchmark
run_furmark(
    bm['exe_path'], bm['width'], bm['height'], bm['msaa'], bm['duration'], log_path
)

# Wait for audio thread to finish
record_thread.join()

# Save full audio recording
save_wav(audio_buf, au['fs'], wav_out)

# Compute & save noise log (per-second dBFS)
rms_db = compute_rms_dbfs(audio_buf, au['fs'])
times  = list(range(bm['duration']))
save_noise_log(times, rms_db, noise_csv)

# Save fan log
save_fan_log(fan_log, fan_csv)

print("Run complete:")
print(f" - FurMark log: {log_path}")
print(f" - Audio WAV:   {wav_out}")
print(f" - Noise CSV:   {noise_csv}")
print(f" - Fan CSV:     {fan_csv}")
print(f" - Card info:   {card_info_json}")
