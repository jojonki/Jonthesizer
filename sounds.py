import math
import itertools
from pygame import midi
import struct
import numpy as np
import pyaudio

import seaborn as sns
import matplotlib.pyplot as plt

import numpy as np
from scipy.io import wavfile
from oscillators import *
from graphics import *
from collections.abc import Iterable

sample_rate = 44_100
buf_size = 256


class WaveAdder_old:

    def __init__(self, *oscillators):
        self.oscillators = oscillators
        self.n = len(oscillators)

    def __iter__(self):
        [iter(osc) for osc in self.oscillators]
        return self

    def __next__(self):
        return sum(next(osc) for osc in self.oscillators) / self.n

    def phase(self):
        return [osc._p for osc in self.oscillators]


class WaveAdder:

    def __init__(self, *generators, stereo=False):
        self.generators = generators
        self.stereo = stereo

    def _mod_channels(self, _val):
        val = _val
        if isinstance(_val, (int, float)) and self.stereo:
            val = (_val, _val)
        elif isinstance(_val, Iterable) and not self.stereo:
            val = sum(_val) / len(_val)
        return val

    def trigger_note_release(self):
        [
            gen.trigger_note_release() for gen in self.generators
            if hasattr(gen, "trigger_note_release")
        ]

    @property
    def ended(self):
        ended = [gen.ended for gen in self.generators if hasattr(gen, "ended")]
        return all(ended)

    def __iter__(self):
        [iter(gen) for gen in self.generators]
        return self

    def __next__(self):
        vals = [self._mod_channels(next(gen)) for gen in self.generators]
        if self.stereo:
            l, r = zip(*vals)
            val = (sum(l) / len(l), sum(r) / len(r))
        else:
            val = sum(vals) / len(vals)
        return val


def wave_to_file(wav, sample_rate, wav2=None, fname="temp.wav", amp=0.1):
    wav = np.array(wav)
    wav = np.int16(wav * amp * (2**15 - 1))

    if wav2 is not None:
        wav2 = np.array(wav2)
        wav2 = np.int16(wav2 * amp * (2**15 - 1))
        wav = np.stack([wav, wav2]).T

    wavfile.write(fname, sample_rate, wav)


def get_sin_oscillator(freq, sample_rate, amp=1, phase=0):
    phase = (phase / 360) * 2 * math.pi
    increment = (2 * math.pi * freq) / sample_rate
    return (math.sin(v + phase) * amp
            for v in itertools.count(start=0, step=increment))


def get_samples(notes_dict, num_samples):
    return [sum([int(next(osc) * 32767) \
            for _, osc in notes_dict.items()]) \
            for _ in range(num_samples)]


def audioplay(wav, sample_rate):
    wav = np.int16([b * 32767 for b in wav]).tobytes()
    # print(wav.min(), wav.max())
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        # frames_per_buffer=128,
        output=True)
    stream.write(wav)
    stream.stop_stream()
    stream.close()
    p.terminate()
    # print("Stop Streaming")