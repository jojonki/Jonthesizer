import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from scipy.signal import hilbert
from scipy.signal import medfilt
from scipy.signal import hann
from sklearn.cluster import KMeans

CHUNK = 8000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 8000

fig = plt.figure(1, figsize=(18, 6))
ax = plt.subplot(2, 1, 1)
x = range(CHUNK)
y = np.zeros(CHUNK)
lines, = plt.plot(x, y)

ax2 = plt.subplot(2, 1, 2)
x = range(CHUNK)
y = np.zeros(CHUNK)
z = np.zeros(CHUNK)
lines2, = plt.plot(x, y)

y_buf = np.zeros(CHUNK * 2)
z_buf = np.zeros(CHUNK * 2)
window = hann(CHUNK * 2)

p = pyaudio.PyAudio()


def callback(in_data, frame_count, time_info, status):
    global y, y_buf, window

    yy = np.frombuffer(in_data, dtype="int16")

    for i in range(CHUNK):
        y_buf[i] = y_buf[i + CHUNK]
        y_buf[i + CHUNK] = yy[i]

    z_buf = y_buf * window
    analytic_signal = hilbert(z_buf)
    z_buf = np.abs(analytic_signal)

    for i in range(CHUNK):
        y[i] = y_buf[i + int(CHUNK / 2)]
        z[i] = z_buf[i + int(CHUNK / 2)] / window[i + int(CHUNK / 2)]

    y_max = max(1.1 * max(abs(y.min()), abs(y.max())), 100.0)
    y_max2 = max(1.1 * z.max(), 100.0)
    ax.set_ylim(-y_max, y_max)
    ax2.set_ylim(-y_max2 * 0.1, y_max2)
    lines.set_data(x, y)
    lines2.set_data(x, z)

    return (None, pyaudio.paContinue)


stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

stream.start_stream()

while stream.is_active():
    plt.pause(0.01)
    time.sleep(0.01)

stream.stop_stream()
stream.close()
p.terminate()