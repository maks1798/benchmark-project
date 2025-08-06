import pynvml

def init_nvml():
    pynvml.nvmlInit()
    return pynvml.nvmlDeviceGetHandleByIndex(0)

def dump_card_info(handle, out_json):
    import json
    info = {
        "driver_version": pynvml.nvmlSystemGetDriverVersion().decode(),
        "name":           pynvml.nvmlDeviceGetName(handle).decode(),
        "vbios":          pynvml.nvmlDeviceGetVbiosVersion(handle).decode(),
        "uuid":           pynvml.nvmlDeviceGetUUID(handle).decode()
    }
    # Add more fields as needed...
    with open(out_json, 'w') as f:
        json.dump(info, f, indent=2)

def poll_fan_speed(handle):
    # returns fan percentage (0–100)
    return pynvml.nvmlDeviceGetFanSpeed(handle)