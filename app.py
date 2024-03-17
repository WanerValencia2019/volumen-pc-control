import pyaudio
import numpy as np
import subprocess
import time

previus_volume = 0
last_change_time = time.time()
min_delay_between_changes = 5  # seconds


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
        if volume_dB > 103:
            print("Adjusting volume: lower.")
            set_volume(85)
        elif volume_dB < 100:
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
