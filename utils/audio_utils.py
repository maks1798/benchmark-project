import sounddevice as sd, soundfile as sf, numpy as np

def record_audio(duration, fs, channels, buf):
    def callback(indata, frames, time, status, b=buf, idx=[0]):
        b[idx[0]:idx[0]+frames] = indata
        idx[0] += frames
    stream = sd.InputStream(samplerate=fs, channels=channels, callback=callback)
    stream.start()
    sd.sleep(int(duration * 1000))
    stream.stop()

def save_wav(buf, fs, out_path):
    sf.write(out_path, buf, fs)

def compute_rms_dbfs(buf, fs):
    sec = len(buf) // fs
    rms_db = []
    for s in range(sec):
        seg = buf[s*fs:(s+1)*fs]
        rms = np.sqrt(np.mean(seg**2))
        db  = 20 * np.log10(rms + 1e-9)
        rms_db.append(db)
    return rms_db