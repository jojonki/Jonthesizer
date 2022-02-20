"""These oscillators and modulators are design at the following blog.
Making A Synth With Python
https://python.plainenglish.io/making-a-synth-with-python-oscillators-2cb8e68e9c3b
"""
import math
from abc import ABC, abstractmethod
from collections.abc import Iterable
import scipy.signal


def get_osc_by_type(wave_type, freq, sample_rate, wave_range=None):
    if wave_range is None:
        wave_range = (-1, 1)
    if wave_type == 'sine':
        return SineOscillator(freq,
                              wave_range=wave_range,
                              sample_rate=sample_rate)
    elif wave_type == 'square':
        return SquareOscillator(freq,
                                wave_range=wave_range,
                                sample_rate=sample_rate)
    elif wave_type == 'sawtooth':
        return SawtoothOscillator(freq,
                                  wave_range=wave_range,
                                  sample_rate=sample_rate)
    elif wave_type == 'triangle':
        return TriangleOscillator(freq,
                                  wave_range=wave_range,
                                  sample_rate=sample_rate)
    assert False, f'Invalid wave_type: {wave_type}'


class Oscillator(ABC):

    def __init__(self,
                 freq=440,
                 phase=0,
                 amp=1,
                 sample_rate=None,
                 wave_range=(-1, 1)):
        self._freq = freq
        self._amp = amp
        self._phase = phase
        self._sample_rate = sample_rate
        self._wave_range = wave_range

        # Properties that will be changed
        self._f = freq
        self._a = amp
        self._p = phase

    @property
    def init_freq(self):
        return self._freq

    @property
    def init_amp(self):
        return self._amp

    @property
    def init_phase(self):
        return self._phase

    @property
    def freq(self):
        return self._f

    @freq.setter
    def freq(self, value):
        if value == 0:
            print(self._f, value)
        self._f = value
        self._post_freq_set()

    @property
    def amp(self):
        return self._a

    @amp.setter
    def amp(self, value):
        self._a = value
        self._post_amp_set()

    @property
    def phase(self):
        return self._p

    @phase.setter
    def phase(self, value):
        self._p = value
        self._post_phase_set()

    def _post_freq_set(self):
        pass

    def _post_amp_set(self):
        pass

    def _post_phase_set(self):
        pass

    @abstractmethod
    def _initialize_osc(self):
        pass

    @staticmethod
    def squish_val(val, min_val=0, max_val=1):
        return (((val + 1) / 2) * (max_val - min_val)) + min_val

    @abstractmethod
    def __next__(self):
        return None

    def __iter__(self):
        self.freq = self._freq
        self.phase = self._phase
        self.amp = self._amp
        self._initialize_osc()
        return self


class SineOscillator(Oscillator):

    def _post_freq_set(self):
        self._step = (2 * math.pi * self._f) / self._sample_rate

    def _post_phase_set(self):
        self._p = (self._p / 360) * 2 * math.pi

    def _initialize_osc(self):
        self._i = 0

    def __next__(self):
        val = math.sin(self._i + self._p)
        self._i = self._i + self._step
        if self._wave_range != (-1, 1):
            val = self.squish_val(val, *self._wave_range)
        return val * self._a


class SquareOscillator(SineOscillator):

    def __init__(self,
                 freq=440,
                 phase=0,
                 amp=1,
                 sample_rate=44_100,
                 wave_range=(-1, 1),
                 threshold=0):
        super().__init__(freq, phase, amp, sample_rate, wave_range)
        self.threshold = threshold

    def __next__(self):
        val = math.sin(self._i + self._p)
        self._i = self._i + self._step
        if val < self.threshold:
            val = self._wave_range[0]
        else:
            val = self._wave_range[1]
        return val * self._a


class SawtoothOscillator(Oscillator):

    def _post_freq_set(self):
        self._period = self._sample_rate / self._f
        # self._post_phase_set

    def _post_phase_set(self):
        self._p = ((self._p + 90) / 360) * self._period

    def _initialize_osc(self):
        self._i = 0

    def __next__(self):
        div = (self._i + self._p) / self._period
        val = 2 * (div - math.floor(0.5 + div))
        self._i = self._i + 1
        if self._wave_range != (-1, 1):
            val = self.squish_val(val, *self._wave_range)
        return val * self._a


class TriangleOscillator(SawtoothOscillator):

    def __next__(self):
        div = (self._i + self._p) / self._period
        val = 2 * (div - math.floor(0.5 + div))
        val = (abs(val) - 0.5) * 2
        self._i = self._i + 1
        if self._wave_range != (-1, 1):
            val = self.squish_val(val, *self._wave_range)
        return val * self._a


def amp_mode(init_amp, env):
    return env * init_amp


class ModulatedOscillator:

    def __init__(self,
                 oscillator,
                 *modulators,
                 amp_mod=None,
                 freq_mod=None,
                 phase_mod=None):
        self.oscillator = oscillator
        self.modulators = modulators  # list
        self.amp_mod = amp_mod
        self.freq_mod = freq_mod
        self.phase_mod = phase_mod
        self._modulators_count = len(modulators)

    def __iter__(self):
        iter(self.oscillator)
        [iter(modulator) for modulator in self.modulators]
        return self

    def __next__(self):
        mod_vals = [next(modulator) for modulator in self.modulators]
        self._modulate(mod_vals)
        return next(self.oscillator)

    def _modulate(self, mod_vals):
        if not mod_vals:
            return
        if self.amp_mod is not None:
            new_amp = self.amp_mod(self.oscillator.init_amp, mod_vals[0])
            self.oscillator.amp = new_amp

        if self.freq_mod is not None:
            if self._modulators_count == 2:
                mod_val = mod_vals[1]
            else:
                mod_val = mod_vals[0]
            new_freq = self.freq_mod(self.oscillator.init_freq, mod_val)
            self.oscillator.freq = new_freq

        if self.phase_mod is not None:
            if self._modulators_count == 3:
                mod_val = mod_vals[2]
            else:
                mod_val = mod_vals[-1]
            new_phase = self.phase_mod(self.oscillator.init_phase, mod_val)
            self.oscillator.phase = new_phase

    def trigger_note_release(self):
        tr = "trigger_note_release"
        for modulator in self.modulators:
            if hasattr(modulator, tr):
                modulator.trigger_note_release()
        if hasattr(self.oscillator, tr):
            self.oscillator.trigger_note_release()

    @property
    def ended(self):
        e = "ended"
        ended = []
        for modulator in self.modulators:
            if hasattr(modulator, e):
                ended.append(modulator.ended)
        if hasattr(self.oscillator, e):
            ended.append(self.oscillator.ended)
        return all(ended)


class Chain:

    def __init__(self, generator, *modifiers):
        self.generator = generator
        self.modifiers = modifiers

    def __getattr__(self, attr):
        val = None
        if hasattr(self.generator, attr):
            val = getattr(self.generator, attr)
        else:
            for modifier in self.modifiers:
                if hasattr(modifier, attr):
                    val = getattr(modifier, attr)
                    break
            else:
                raise AttributeError(f"attribute '{attr}' does not exist")
        return val

    def trigger_note_release(self):
        tr = "trigger_note_release"
        if hasattr(self.generator, tr):
            self.generator.trigger_note_release()
        for modifier in self.modifiers:
            if hasattr(modifier, tr):
                modifier.trigger_note_release()

    @property
    def ended(self):
        ended = []
        e = "ended"
        if hasattr(self.generator, e):
            ended.append(self.generator.ended)
        ended.extend([m.ended for m in self.modifiers if hasattr(m, e)])
        return all(ended)

    def __iter__(self):
        iter(self.generator)
        [iter(mod) for mod in self.modifiers if hasattr(mod, "__iter__")]
        return self

    def __next__(self):
        val = next(self.generator)
        [next(mod) for mod in self.modifiers if hasattr(mod, "__iter__")]
        for modifier in self.modifiers:
            val = modifier(val)
        return val


class Volume:

    def __init__(self, amp=1.):
        self.amp = amp

    def __call__(self, val):
        _val = None
        if isinstance(val, Iterable):
            _val = tuple(v * self.amp for v in val)
        elif isinstance(val, (int, float)):
            _val = val * self.amp
        return _val


class ModulatedVolume(Volume):

    def __init__(self, modulator):
        super().__init__(0.)
        self.modulator = modulator

    def __iter__(self):
        iter(self.modulator)
        return self

    def __next__(self):
        self.amp = next(self.modulator)
        return self.amp

    def trigger_note_release(self):
        if hasattr(self.modulator, "trigger_note_release"):
            self.modulator.trigger_note_release()

    @property
    def ended(self):
        ended = False
        if hasattr(self.modulator, "ended"):
            ended = self.modulator.ended
        return ended


def amp_mod(init_amp, env):
    return env * init_amp


# def freq_mod(init_freq, val):
#     print(init_freq, val)
#     return init_freq * val


def freq_mod(init_freq, env, mod_amt=0.1, sustain_level=0.7):
    return init_freq + ((env - sustain_level) * init_freq * mod_amt)


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


def lowpass_filter(wave, sample_rate, cutoff, order, lpf_intensity=1.0):
    assert 0 < lpf_intensity <= 1.0
    if cutoff <= 0:
        return wave
    nyq = sample_rate * 0.5
    normal_cutoff = cutoff / nyq
    b, a = scipy.signal.butter(order, normal_cutoff, btype='low')
    wave2 = scipy.signal.lfilter(b, a, wave)
    wave = lpf_intensity * wave2 + (1.0 - lpf_intensity) * wave

    return wave
