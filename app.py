import signal
import sys

import numpy as np
import pyaudio
import PyQt6.QtWidgets as qtw
import pyqtgraph as pg
from pygame import midi
from PyQt6.QtCore import Qt
from pyqtgraph.Qt import QtCore

from envelope import Envelope
from midi import MidiThread, ProgramSignals, initialize_midi
from oscillators import (Chain, ModulatedOscillator, ModulatedVolume,
                         WaveAdder, amp_mod, freq_mod, get_osc_by_type,
                         lowpass_filter)
from widgets import ADSRWidget, LabelDial, SpectrogramWidget, WaveWidget

signal.signal(signal.SIGINT, signal.SIG_DFL)

RATE = 22_050
buf_size = 256


class Window(qtw.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setup_midi()

        self.base_f = 440
        self.wave_type = 'sine'
        self.lfo_wave_type = 'sine'
        self.wave_ptr = 0

        self.setGeometry(100, 100, 1300, 600)
        self.build_ui_components()

        self.stream = pyaudio.PyAudio().open(rate=RATE,
                                             channels=1,
                                             format=pyaudio.paInt16,
                                             output=True,
                                             frames_per_buffer=buf_size)
        self.osc = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_buffer)
        print('timer', buf_size / RATE * 1000)
        self.timer.start(buf_size / RATE * 1000)

        self.show()

    def setup_midi(self):
        midi_in = initialize_midi()
        # Instantiate a signal
        program_signals = ProgramSignals()
        self.workThread = MidiThread(self, midi_in, program_signals)
        program_signals.midi_signal.connect(self.on_midi_message)
        self.workThread.start()

    def build_ui_components(self):
        self.setWindowTitle('Jonthesizer')

        layout_left = qtw.QHBoxLayout()
        layout_plot = qtw.QHBoxLayout()
        layout_right = qtw.QVBoxLayout()
        layout_wave_select = qtw.QVBoxLayout()
        layout_left = qtw.QHBoxLayout()

        layout_left.setContentsMargins(0, 0, 0, 0)

        # osc1/2
        n_selectors = 2
        wave_list = ['sine', 'square', 'sawtooth', 'triangle']
        toggle_events = [self.on_osc1_selected, self.on_lfo_wave_selected]
        btn_groups = []
        for i in range(n_selectors):
            btn_groups.append(qtw.QButtonGroup(self))
            if i == 0:
                label = qtw.QLabel('OSC1')
            elif i == 1:
                label = qtw.QLabel('LFO')

            layout_wave_select.addWidget(label)
            for j, wave in enumerate(wave_list):
                rad = qtw.QRadioButton(wave)
                btn_groups[i].addButton(rad)
                if j == 0:
                    rad.setChecked(True)
                rad.toggled.connect(toggle_events[i])
                layout_wave_select.addWidget(rad)

        layout_left.addLayout(layout_wave_select)

        # Wave plot
        self.wave_plot = WaveWidget()
        layout_plot.addWidget(self.wave_plot)

        # Spectrogram plot
        self.spec_plot = SpectrogramWidget(sample_rate=RATE, buf_size=buf_size)
        layout_plot.addWidget(self.spec_plot)

        # ADSR plot
        self.adsr_plot = ADSRWidget(sample_rate=RATE, buf_size=buf_size)
        layout_plot.addWidget(self.adsr_plot)

        # Set plots
        layout_right.addLayout(layout_plot)

        # dials
        layout_dials = qtw.QHBoxLayout()
        layout_dials.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ADSR
        self.adsr = {}
        for adsr_type, init_value in [('Attack', 200), ('Decay', 400),
                                      ('Sustain', 400), ('Release', 500)]:
            label_dial = LabelDial(text=adsr_type,
                                   range_min=1,
                                   range_max=1000,
                                   value_changed=self.update_adsr_dial)
            label_dial.dial.setValue(int(init_value))
            self.adsr[adsr_type] = label_dial
            layout_dials.addLayout(self.adsr[adsr_type])
        self.update_adsr_dial()

        # LFO
        self.lfo = {}
        for lfo_type, init_value, range_min, range_max in [('LFO Freq', 0, 0,
                                                            50)]:
            label_dial = LabelDial(text=lfo_type,
                                   range_min=range_min,
                                   range_max=range_max,
                                   value_changed=self.update_lfo_dial)
            self.lfo[lfo_type] = label_dial
            label_dial.dial.setValue(init_value)
            self.lfo[adsr_type] = label_dial
            layout_dials.addLayout(self.lfo[lfo_type])
        self.update_lfo_dial()

        # low pass
        self.lpf = {}
        for lpf_type, init_value, range_min, range_max in [
            ('Cutoff', 0, 0, 8000),
            ('LPF Intensity', 100, 0, 100),
        ]:
            label_dial = LabelDial(text='Filter',
                                   range_min=range_min,
                                   range_max=range_max,
                                   value_changed=self.update_lpf_dial)
            self.lpf[lpf_type] = label_dial
            label_dial.dial.setValue(init_value)
            layout_dials.addLayout(label_dial)

        layout_right.addLayout(layout_dials)

        layout_left.addLayout(layout_right)

        widget = qtw.QWidget()
        widget.setLayout(layout_left)

        self.setCentralWidget(widget)
        pg.setConfigOptions(antialias=True)

    def update_buffer(self):
        if not self.osc:
            return

        buf = np.array([next(self.osc) for _ in range(buf_size)])
        buf = lowpass_filter(wave=buf,
                             sample_rate=RATE,
                             cutoff=self.cutoff,
                             order=5,
                             lpf_intensity=self.lpf_intensity)

        samples = np.int16([b * 32767 for b in buf]).tobytes()
        self.stream.write(samples)

        self.wave_plot.curve.setData(buf)
        self.spec_plot.update(buf)

    def update_adsr_dial(self):
        for adsr_type, widget in self.adsr.items():
            val = widget.dial.value()
            if adsr_type == 'Attack':
                self.attack_duration = val / 1000
                self.adsr[adsr_type].label.setText(
                    f'Attack\n{self.attack_duration*1000:.1f}ms')
            elif adsr_type == 'Decay':
                self.decay_duration = val / 1000
                self.adsr[adsr_type].label.setText(
                    f'Decay\n{self.decay_duration*1000:.1f}ms')
            elif adsr_type == 'Sustain':
                self.sustain_level = val / 1000
                self.adsr[adsr_type].label.setText(
                    f'Sustain\n{self.sustain_level:.2f}')
            elif adsr_type == 'Release':
                self.release_duration = val / 1000
                self.adsr[adsr_type].label.setText(
                    f'Release\n{self.release_duration*1000:.1f}ms')

        try:
            self.env = Envelope(attack_duration=self.attack_duration,
                                decay_duration=self.decay_duration,
                                sustain_level=self.sustain_level,
                                release_duration=self.release_duration,
                                sample_rate=RATE)
            self.adsr_plot.curve.setData(self.env.get_shape())
        except AttributeError as e:
            pass

    def update_lfo_dial(self):
        for lfo_type, widget in self.lfo.items():
            val = widget.dial.value()
            if lfo_type == 'LFO Freq':
                self.lfo_freq = val
                widget.label.setText(f'LFO Freq\n{val} Hz')

    def update_lpf_dial(self):
        for lpf_type, widget in self.lpf.items():
            val = widget.dial.value()
            if lpf_type == 'Cutoff':
                self.cutoff = val
                if val == 0:
                    val = '-'
                widget.label.setText(f'Cutoff\n{val} Hz')
            elif lpf_type == 'LPF Intensity':
                self.lpf_intensity = val / 100
                widget.label.setText(
                    f'LPF Intensity\n{self.lpf_intensity:.1f}')

    def on_osc1_selected(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            print("You have selected : " + radio_button.text())
            self.wave_type = radio_button.text()

    def on_lfo_wave_selected(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            print('lfo', radio_button.text())
            self.lfo_wave_type = radio_button.text()

    def note_on(self):
        sample_rate = RATE
        print('note on base f', self.base_f)
        if self.lfo_freq == 0:
            osc = ModulatedOscillator(
                get_osc_by_type(self.wave_type,
                                freq=self.base_f,
                                sample_rate=sample_rate), )

        else:
            osc = ModulatedOscillator(
                get_osc_by_type(self.wave_type,
                                freq=self.base_f,
                                sample_rate=sample_rate),
                get_osc_by_type(self.lfo_wave_type,
                                freq=self.lfo_freq,
                                sample_rate=sample_rate,
                                wave_range=(0.2, 1.0)),
                amp_mod=amp_mod,
                freq_mod=freq_mod,
            )

        self.osc = iter(
            WaveAdder(
                Chain(
                    osc,
                    ModulatedVolume(
                        Envelope(
                            attack_duration=self.attack_duration,
                            decay_duration=self.decay_duration,
                            sustain_level=self.sustain_level,
                            release_duration=self.release_duration,
                            sample_rate=sample_rate,
                        )),
                ),
                stereo=False,
            ))

    def note_off(self):
        self.osc.trigger_note_release()

    def on_midi_message(self, event):
        status, note, freq = event
        if status == 0x90:  # note on
            self.base_f = freq
            self.note_on()
        elif status == 0x80:  # note off
            self.note_off()


def main():
    try:
        App = qtw.QApplication(sys.argv)
        window = Window()
        sys.exit(App.exec())
    except KeyboardInterrupt as e:
        sys.exit()
        pass


if __name__ == '__main__':
    main()