# Jonthesizer
Jonthesizer is a simple software synthesizer based on PyQtGraph, developed entirely in Python.
[![Screenshot](https://user-images.githubusercontent.com/166852/154841472-3273be4d-9caf-4772-9464-3714144440e7.png)](https://www.youtube.com/watch?v=yK6398tRkCo "Jonthesizer")

## Setup
I only checked my application on M1 Mac. Though, this should work in other platforms.
```
brew install portaudio
pip install --global-option='build_ext' --global-option="-I$(brew --prefix)/include" --global-option="-L$(brew --prefix)/lib" pyaudio
```

This sinthesizer is controlled by a MIDI device. If you don't have a MIDI device, a MIDI simulator like [MidiKeys](https://flit.github.io/projects/midikeys/) is useful.

## Problems
This application is　still under development, so it has prbably many bugs. The following items are known issues.
- [ ] Cutoff artifacts
