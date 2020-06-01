# HVAD
A repository for the Helper with Vowel Acquisiton for Danish repository

HVAD runs in python but you need to have installed the program praat for it to work. Praat can be downloaded from:
http://www.fon.hum.uva.nl/praat/

Hvad also needs the following python packages to run:
- pyaudio
- numpy
- matplotlib.pyplot
- wave
- time
- parselmouth
- simpleaudio
- tkinter
- tkinter.font
- PIL
- random

If you don't have pyaudio installed it can be a little troublesome to get it. For Mac users try this: https://medium.com/@wagnernoise/installing-pyaudio-on-macos-9a5557176c4d. The package parselmouth is the python wrapping for praat, and will likely be one you will have to install. You will need simpleaudio as well for playback of sounds.

You will also need to go into the script (VowelLearning.py) and change the path on line 27 to the folder on your computer. You will probably also need to remove ", input_device_index=3" on line 36 (which will make it use the default mic input), unless you are using an external soundcard.


