"""ADSR Envelope class
The code is almost the same as the article below.
https://python.plainenglish.io/build-your-own-python-synthesizer-part-2-66396f6dad81
"""
import itertools

import numpy as np


class Envelope:

    def __init__(
        self,
        attack_duration=0.05,
        decay_duration=0.2,
        sustain_level=0.7,
        release_duration=0.3,
        sample_rate=None,
    ):
        assert attack_duration >= 0
        assert decay_duration >= 0
        assert 0 <= sustain_level <= 1
        assert release_duration >= 0
        assert sample_rate > 0
        self.attack_duration = attack_duration
        self.decay_duration = decay_duration
        self.sustain_level = sustain_level
        self.release_duration = release_duration
        self.sample_rate = sample_rate

    def __iter__(self):
        self.val = 0
        self.ended = False
        self.stepper = self.ads_stepper()
        return self

    def __next__(self):
        self.val = next(self.stepper)
        return self.val

    def trigger_note_on(self):
        self.val = 0
        self.ended = False
        self.stepper = self.ads_stepper()

    def trigger_note_release(self):
        self.stepper = self.r_stepper()

    def ads_stepper(self):
        attack_stepper = itertools.count(
            start=0, step=1 / (self.attack_duration * self.sample_rate))
        decay_stepper = itertools.count(
            start=1,
            step=-(1 - self.sustain_level) /
            (self.decay_duration * self.sample_rate))
        while True:
            if attack_stepper:
                val = next(attack_stepper)
                if val > 1:
                    attack_stepper = None
                    val = next(decay_stepper)
            elif decay_stepper:
                val = next(decay_stepper)
                if val <= self.sustain_level:
                    val = self.sustain_level
                    decay_stepper = None
            else:
                val = self.sustain_level
            self.val = val
            yield val

    def r_stepper(self):
        val = 1
        if self.release_duration > 0:
            release_stepper = itertools.count(
                self.val,
                step=-self.sustain_level /
                (self.release_duration * self.sample_rate))
        else:
            val = -1
        while True:
            if val <= 0:
                self.ended = True
                val = 0
            else:
                val = next(release_stepper)
            yield val

    def get_shape(self, note_on_duration=0.2):
        self.trigger_note_on()
        adsr = [
            next(self) for _ in range(
                int((self.attack_duration + self.decay_duration) *
                    self.sample_rate))
        ]
        adsr += [
            next(self) for _ in range(int(note_on_duration * self.sample_rate))
        ]
        self.trigger_note_release()
        adsr += [
            next(self)
            for _ in range(int(self.release_duration * self.sample_rate))
        ]
        adsr = np.array(adsr)
        return adsr
