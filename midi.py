from pyqtgraph.Qt import QtGui, QtCore
import time
import pygame


class ProgramSignals(QtCore.QObject):
    midi_signal = QtCore.Signal(list)


class MidiThread(QtCore.QThread):

    def __init__(self, Parent, midi_in, program_signals):
        QtCore.QThread.__init__(self)
        self.midi_in = midi_in
        self.program_signals = program_signals

    def __del__(self):
        self.wait()

    def run(self):
        notes_dict = {}
        while True:
            if notes_dict:
                self.program_signals.midi_signal.emit((status, note, freq))
                notes_dict = {}
            if self.midi_in.poll():
                # Add or remove notes  from notes_dict
                for event in self.midi_in.read(num_events=16):
                    (status, note, vel, _), _ = event
                    if status == 0x80 and note in notes_dict:
                        # del notes_dict[note]
                        # freq = midi.midi_to_frequency(note)
                        # notes_dict[note] = (status, note, freq)
                        pass
                    elif status == 0x90 and note not in notes_dict:
                        pass
                        # freq = midi.midi_to_frequency(note)
                        # notes_dict[note] = (status, note, freq)
                    freq = pygame.midi.midi_to_frequency(note)
                    notes_dict[note] = (status, note, freq)
            time.sleep(0.01)


def initialize_midi():
    pygame.midi.init()
    default_id = pygame.midi.get_default_input_id()
    assert default_id != -1, f'Not found a midi device in your machine'
    midi_in = pygame.midi.Input(device_id=default_id)
    return midi_in
