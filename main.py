import toml, numpy as np, time, threading
import soundfile as sf
from utils.gpu_utils import init_nvml, poll_fan_speed, dump_card_info
from utils.audio_utils import record_audio, save_wav, compute_rms_dbfs
from utils.benchmark_utils import run_furmark, save_noise_log, save_fan_log

# Load config
tf = toml.load("config.toml")
bm, au, an = tf['benchmark'], tf['audio'], tf['analysis']

# Init NVML & dump card info
handle = init_nvml()
dump_card_info(handle, 'card_info.json')

# Prepare audio buffer
total_samples = int(bm['duration'] * au['fs'])
audio_buf = np.zeros((total_samples, au['channels']), dtype='float32')

# Start audio recording
record_thread = threading.Thread(
    target=record_audio,
    args=(bm['duration'], au['fs'], au['channels'], audio_buf)
)
record_thread.start()

# Poll fan speeds in parallel
t_start = time.time()
fan_log = []
while time.time() - t_start < bm['duration']:
    fan_log.append((time.time() - t_start, poll_fan_speed(handle)))
    time.sleep(1.0)

# Run FurMark benchmark
run_furmark(bm['exe_path'], bm['width'], bm['height'], bm['msaa'], bm['duration'], bm['log_path'])

# Ensure audio thread finished
record_thread.join()

# Save full audio
save_wav(audio_buf, au['fs'], au['wav_out'])

# Compute & save noise log
rms_db = compute_rms_dbfs(audio_buf, au['fs'])
times = list(range(bm['duration']))
save_noise_log(times, rms_db, an['noise_log_csv'])

# Save fan log
save_fan_log(fan_log, 'fan_log.csv')

print("Run complete: noise.wav, furmark_run.log, noise_log.csv, fan_log.csv, card_info.json")