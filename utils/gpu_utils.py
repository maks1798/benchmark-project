# utils/gpu_utils.py

import os
import subprocess
import csv

def dump_card_info(out_json):
    """
    Full snapshot of GPU state: BIOS, PCI info, power limits, ECC status, etc.
    Outputs both XML and JSON versions under the run folder.
    """
    # XML dump (rich, all fields)
    xml_path = os.path.splitext(out_json)[0] + ".xml"
    with open(xml_path, "w") as f:
        subprocess.run(["nvidia-smi", "-q", "-x"], stdout=f, check=True)
    # (Optional) convert to JSON if you want—here we'll leave the XML
    print(f"Card info dumped to XML: {xml_path}")

def poll_gpu_metrics(out_csv, interval=1, duration=120):
    """
    Poll key metrics once per second (or custom interval) for `duration` seconds.
    Writes a CSV with columns:
      timestamp_s, temperature_C, utilization_gpu_pct,
      graphics_clock_MHz, memory_clock_MHz, power_draw_W, fan_speed_pct
    """
    field_list = [
        "timestamp_s",
        "temperature.gpu",
        "utilization.gpu",
        "clocks.current.graphics",
        "clocks.current.memory",
        "power.draw",
        "fan.speed"
    ]
    # Corresponding nvidia-smi query tokens (no units)
    query_fields = ",".join([
        "temperature.gpu",
        "utilization.gpu",
        "clocks.current.graphics",
        "clocks.current.memory",
        "power.draw",
        "fan.speed"
    ])

    with open(out_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(field_list)

        start = time0 = 0.0
        import time
        start = time.time()
        while True:
            elapsed = time.time() - start
            if elapsed > duration:
                break
            # Query nvidia-smi
            out = subprocess.check_output([
                "nvidia-smi",
                f"--query-gpu={query_fields}",
                "--format=csv,noheader,nounits"
            ])
            # Example out: "67, 12 %, 2100, 5000, 220.25 W, 45 %"
            # Normalize: strip %, W, then split
            parts = [p.strip().replace(" W","").replace(" %","") for p in out.decode().split(",")]
            row = [f"{elapsed:.1f}"] + parts
            writer.writerow(row)
            time.sleep(interval)
    print(f"GPU metrics logged to {out_csv}")
