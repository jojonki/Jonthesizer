# Jonthesizer

## Setup
```
brew install portaudio
pip install --global-option='build_ext' --global-option="-I$(brew --prefix)/include" --global-option="-L$(brew --prefix)/lib" pyaudio
pip install -r requirements.txt
```

## Arch
- app.py
- oscillators.py
- widgets.py

## TODOs
- [ ] Resolve cutoff artifacts