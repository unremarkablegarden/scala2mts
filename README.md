# 𝓢𝓬𝓪𝓵𝓪 𝟐 𝓜𝓣𝓢 
Python script to convert Scala tuning files to MIDI Tuning Standard SysEx (for use with hardware synths and sequencers, like the Cirklon and Prophet)

Works with Scala files defined in just intonation (ratios) or in cents. Works with non-2/1 octave tunings and non-octave-repeating tunings.

# Usage

> python scala2mts.py -h

```
Convert Scala files to SysEx files for use with the Prophet rev2 and Cirklon.
MTS - MIDI Tuning standard 1.0

(Works with scala files that use ratios or cents)

Arguments:
-i input file: the Scala file to convert
-o output file: the SysEx file to create (default: the input file name with .syx extension)
-n base_note: the base note as a number (default = 69 = A4)
-f base_freq: the base frequency of the Scala file (default = 440.000)
-p program_number: which memory slot to store the tuning in the synth (default = 1 = first)
-h help: show this help message
```

> python scala2mts.py -i grady-sisiutl.scl -n 48 -f 298 -p 7

```
base_note: 48
base_freq: 298.0
notes_per_octave: 12
scala_ratios: [1, 1.037037037037037, 1.125, 1.1666666666666667, 1.2727272727272727, 1.3333333333333333, 1.375, 1.5, 1.5555555555555556, 1.696969696969697, 1.75, 1.8333333333333335, 2.0]
——————————
F0 7E 00 08 01 06 67 72 61 64 79 20 73 69 63 69 75 74 69 6c 20 20 0e 20 00 0e 70 51 10 25 0f 10 75 61 12 37 05 13 1d 38 13 62 47 15 22 47 15 73 19 17 34 3d 17 78 28 18 60 00 1a 20 00 1a 70 51 1c 25 0f 1c 75 61 1e 37 05 1f 1d 38 1f 62 47 21 22 47 21 73 19 23 34 3d 23 78 28 24 60 00 26 20 00 26 70 51 28 25 0f 28 75 61 2a 37 05 2b 1d 38 2b 62 47 2d 22 47 2d 73 19 2f 34 3d 2f 78 28 30 60 00 32 20 00 32 70 51 34 25 0f 34 75 61 36 37 05 37 1d 38 37 62 47 39 22 47 39 73 19 3b 34 3d 3b 78 28 3c 60 00 3e 20 00 3e 70 51 40 25 0f 40 75 61 42 37 05 43 1d 38 43 62 47 45 22 47 45 73 19 47 34 3d 47 78 28 48 60 00 4a 20 00 4a 70 51 4c 25 0f 4c 75 61 4e 37 05 4f 1d 38 4f 62 47 51 22 47 51 73 19 53 34 3d 53 78 28 54 60 00 56 20 00 56 70 51 58 25 0f 58 75 61 5a 37 05 5b 1d 38 5b 62 47 5d 22 47 5d 73 19 5f 34 3d 5f 78 28 60 60 00 62 20 00 62 70 51 64 25 0f 64 75 61 66 37 05 67 1d 38 67 62 47 69 22 47 69 73 19 6b 34 3d 6b 78 28 6c 60 00 6e 20 00 6e 70 51 70 25 0f 70 75 61 72 37 05 73 1d 38 73 62 47 75 22 47 75 73 19 77 34 3d 77 78 28 78 60 00 7a 20 00 7a 70 51 7c 25 0f 7c 75 61 7e 37 05 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 7f 00 00 81 F7

Output file grady-sisiutl.syx already exists. Overwrite? (y/n)
y
Wrote sysex to grady-sisiutl.syx
```

# Requirements

Python 3

—

*RIP http://www.microtonalsoftware.com/scl-scala-to-mts-converter.html*
