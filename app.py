import subprocess
import time
import argparse

import pyaudio
import numpy as np

parser = argparse.ArgumentParser(description="Controla automáticamente el volumen del sistema basado en el nivel de decibelios capturado.")
parser.add_argument("--min_dB", type=float, default=90, help="El nivel mínimo de decibelios antes de subir el volumen.")
parser.add_argument("--max_dB", type=float, default=105, help="El nivel máximo de decibelios antes de bajar el volumen.")
parser.add_argument("--wait_time", type=float, default=1, help="Tiempo de espera (en segundos) para cambiar el volumen.")
args = parser.parse_args()


previus_volume = 0
last_change_time = time.time()
min_delay_between_changes = args.wait_time
min_dB = args.min_dB
max_dB = args.max_dB


def set_volume(level):
    try:
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
    except subprocess.SubprocessError as e:
        print(f"Error al ajustar el volumen: {e}")


def should_adjust_volume(new_dB, prev_dB, threshold=10):
    global last_change_time
    current_time = time.time()
    if abs(new_dB - prev_dB) > threshold and (current_time - last_change_time) > min_delay_between_changes:
        last_change_time = current_time
        return True
    return False


def audio_callback(in_data, frame_count, time_info, status):
    global previus_volume
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    volume = np.linalg.norm(audio_data) * 10

    reference_value = 1.0
    volume_dB = 20 * np.log10(volume / reference_value) if volume > 0 else 0

    if should_adjust_volume(volume_dB, previus_volume, threshold=10):
        if volume_dB > max_dB:
            print("Adjusting volume: lower.")
            set_volume(85)
        elif volume_dB < min_dB:
            print("Adjusting volume: higher.")
            set_volume(100)
        previus_volume = volume_dB
    print(f"Volume: {volume}, Volume (dB): {volume_dB}")
    return (in_data, pyaudio.paContinue)


p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024,
                stream_callback=audio_callback)

stream.start_stream()

try:
    while stream.is_active():
        pass
except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
