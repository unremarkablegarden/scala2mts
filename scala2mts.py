#!/usr/bin/env python3
# Path: scala2mts.py
# by Olle Holmberg, 2022

"""
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
"""

import sys
import os
import getopt
import math
import functools
import operator

# define defaults
input_file = None
output_file = None
program_number = 1

base_note = 69
base_freq = 440
# base_note = 60
# base_freq = 432
# base_note = 48
# base_freq = 261.625565

# parse command line arguments
try:
  opts, args = getopt.getopt(sys.argv[1:], "hi:o:n:f:p:", ["help", "input=", "output=", "base_note=", "base_freq=", "program_number="])
except getopt.GetoptError as err:
	print(err)
	sys.exit(2)
for o, a in opts:
	if o in ("-h", "--help"):
		print(__doc__)
		sys.exit()
	elif o in ("-i", "--input"):
		input_file = a
	elif o in ("-o", "--output"):
		output_file = a
	elif o in ("-n", "--base_note"):
		base_note = int(a)
	elif o in ("-f", "--base_freq"):
		base_freq = float(a)
	elif o in ("-p", "--program_number"):
    # first is actually 0, but we want to start at 1
		program_number = int(a) - 1
	else:
		assert False, "unhandled option"
		
# check for required arguments
if input_file is None:
	print("Error: input file is required")
	sys.exit(2)
  
# set output file name if not specified
if output_file is None:
  # remove file extension
  output_file = os.path.splitext(input_file)[0]
  # add .syx extension
  output_file = output_file + ".syx"
  

# read the Scala file
with open(input_file, 'r') as f:
	scala_lines = f.readlines()

# parse the Scala file
scala_name = scala_lines[0].strip()
# remove the ! and space from the name
scala_name = scala_name[2:]
# remove the .scl extension
scala_name = scala_name.replace(".scl", "")
# replace dashes and underlines with spaces
scala_name = scala_name.replace("-", " ")
scala_name = scala_name.replace("_", " ")


# scala_description = the first scala_lines line that doesn't start with !
scala_description = ""
for line in scala_lines:
  if not line.startswith("!"):
    scala_description = line.strip()
    break


# get the number of notes
# notes_per_octave = the first scala_lines line that starts with a number
notes_per_octave = 0
for line in scala_lines:
  if line.startswith(" "):
    notes_per_octave = int(line.strip())
    break


# notes raw data
scala_notes = []
for line in scala_lines:
  if line.startswith(" "):
    note = line.strip()
    scala_notes.append(note)
    
# remove the first element, the number of notes
scala_notes.pop(0)

  
# function to convert a frequency to a ratio
def ratio_to_float(strrat):
    nden = strrat.replace("/", ":").split(":")
    if nden[0] == "x":
        return None
    elif len(nden) == 1:
        res = float(nden[0])
        return res
    elif len(nden) == 2:
        num, denom = nden
        res = float(num)/float(denom)
        return res

    else:
        raise Exception("%s is not a valid number or ratio" % strrat)


# function to convert a ratio to a frequency
def ratio_to_cents(ratio):
    if ratio is not None:
        res = 1200 * math.log(ratio, 2)
    else:
        res = None
    return res

  
# check if notes are frequencies or ratios
scala_notes_are_ratios = False
if "/" in scala_notes[0]:
  scala_notes_are_ratios = True
  
scala_cents = []
if scala_notes_are_ratios:
  # convert ratios to cents
  for note in scala_notes:
    ratio = ratio_to_float(note)
    cents = ratio_to_cents(ratio)
    scala_cents.append(cents)
else:
  # put scala_notes in scala_cents
  scala_cents = scala_notes


# function to calculate ratio of cents
def cents_to_ratio(cents):
  ratio = 2**(cents/1200)
  return ratio

# calculate ratios of scale
scala_ratios = []
for note in scala_cents:
  ratio = cents_to_ratio(float(note))
  scala_ratios.append(ratio)

# add the base frequency to the start of the list
scala_ratios.insert(0, 1)

# function to calculate frequency of note, based on base note and base frequency, using scala_ratios between notes, and the notes per octave
def note_to_hz(note, base_note, base_freq, scala_ratios, notes_per_octave):
  # calculate the note number within the octave
  note_in_octave = (note - base_note) % notes_per_octave
  # calculate the ratio of the note
  ratio = scala_ratios[note_in_octave]
  # calculate the octave of the note
  octave = (note - base_note) // notes_per_octave
  octave_size = scala_ratios[notes_per_octave]
  # calculate the frequency of the note
  freq = base_freq * (octave_size**octave) * ratio
  return freq
  
  
# calculate frequencies of notes
scala_freqs = []
for i in range(0, 128):
  freq = note_to_hz(i, base_note, base_freq, scala_ratios, notes_per_octave)
  scala_freqs.append(freq)

# function to convert number to hex
def num_to_hex(num):
  hex = format(num, '02x')
  return hex

# print(num_to_hex(69))
# outputs 45

# calculate hz of all notes in standard tuning
# function to calculate freq of note
def note_to_hz_std(note):
  freq = 440 * 2**((note - 69)/12)
  return freq

# calculate freqs of all notes in standard tuning
std_freqs = []
for i in range(0, 128):
  freq = note_to_hz_std(i)
  std_freqs.append(freq)
  
"""
Frequency data format (all bytes in hex)

xx = semitone (MIDI note number to retune to, unit is 100 cents)
yy = MSB of fractional part (1/128 semitone = 100/128 cents = .78125 cent units)
zz = LSB of fractional part (1/16384 semitone = 100/16384 cents = .0061 cent units)

Frequency data shall be sent via system exclusive messages. Because system exclusive data bytes have their high bit set low, containing 7 bits of data, a 3-byte (21-bit) "frequency data word" is used for specifying a frequency with the suggested resolution. 

The first byte of the frequency data word specifies the nearest equal-tempered semitone below the frequency. 

The next two bytes (14 bits) specify the fraction of 100 cents above the semitone at which the frequency lies.
"""

# function to convert frequency to frequency data
def hz_to_freq_data(freq):
  # limit freq to bounds of MIDI note range
  if freq < 8.1757989156:
    freq = 8.1757989156
  elif freq > 12543.853951:
    freq = 12543.853951
    
  # calculate the nearest equal-tempered semitone below the frequency
  semitone = round(12 * math.log(freq/440, 2) + 69)
  # calculate the fraction of 100 cents above the semitone at which the frequency lies
  cents = round(1200 * math.log(freq/440, 2) + 6900)
  cents_fraction = cents - (semitone * 100)
  if (cents_fraction < 0):
    semitone = semitone - 1
    cents_fraction = cents_fraction + 100

  # calculate the MSB of the fractional part
  # 1 MSB = 1/128 semitone = 100/128 cents = .78125 cents
  # msb = how many times .78125 fits into cents_fraction
  msb = int(cents_fraction // .78125)
  rest = cents_fraction % .78125
  
  # calculate the LSB of the fractional part
  # 1 LSB = 1/16384 semitone = 100/16384 cents = .0061 cents
  lsb = int(rest // .0061)

  semitone_hex = num_to_hex(semitone)
  msb_hex = num_to_hex(msb)
  lsb_hex = num_to_hex(lsb)
  msb_hex = str(msb_hex)
  lsb_hex = str(lsb_hex)
  
  # space at the end added in list join later
  # return semitone_hex, msb_hex, lsb_hex
  return semitone_hex + " " + msb_hex + " " + lsb_hex
  

# calculate freq_data of all notes in scala_freqs
scala_freq_data = []
for freq in scala_freqs:
  freq_data = hz_to_freq_data(freq)
  scala_freq_data.append(freq_data)
  
"""
The format of the SysEx dump is as follows:

header = F0 7E 00 08 01 tt tn 
tuning_data = <xx yy zz> * 128
footer = ck F7

where

F0 7E = universal non-realtime SysEx header
00    = target device ID
08    = sub-ID #1 (MIDI tuning standard)
01    = sub-ID #2 (bulk dump reply)
tt    = tuning program number 0 to 127 in hexadecimal
tn    = tuning name (16 ASCII characters)
<xx yy zz>    = frequency data for one note,
                repeated 128 times
ck    = checksum (XOR of 7E 00 01 tt <388 bytes>)
F7    = end of SysEx message
"""

# convert program number to hex
program_number = num_to_hex(program_number)
# limit scala name to 16 characters and ASCII characters
scala_name = scala_name[:16]
scala_name = scala_name.encode('ascii', 'ignore').decode('utf-8')
# pad scala name with spaces to 16 characters
scala_name = scala_name.ljust(16)

# convert scala name to hex
scala_name_hex = []
for char in scala_name:
  char_hex = num_to_hex(ord(char))
  scala_name_hex.append(char_hex)
# join scala name hex list into string
scala_name_hex = " ".join(scala_name_hex)


header = 'F0 7E 00 08 01 ' + str(program_number)+ " " + scala_name_hex


data = scala_freq_data
# convert data to string
data = ' '.join(data)

footer = "F7"

"""
Dump messages the checksum field is calculated by successively XOR'ing the bytes in the message, excluding the F0, F7, and the checksum field... The resulting value is then AND'ed with 7F, to create a 7 bit value.
"""
# to_checksum = header less the first six chars, plus data, with spaces removed
to_checksum = header[6:] + ''.join(data).replace(" ", "")
# XOR of to_checksum
checksum = functools.reduce(operator.xor, (int(to_checksum[i:i+2], 16) for i in range(0, len(to_checksum), 2)))

# convert checksum to hex
checksum = num_to_hex(checksum)


print('base_note' + ': ' + str(base_note))
print('base_freq' + ': ' + str(base_freq))
print('notes_per_octave' + ': ' + str(notes_per_octave))
print('scala_ratios' + ': ' + str(scala_ratios))
print('——————————')


# sysex
sysex = header + " " + data + " " + checksum + " " + footer

print(sysex)

# remove spaces from sysex
sysex = sysex.replace(" ", "")

# convert sysex to bytes
sysex = bytes.fromhex(sysex)

print()

# check if output_file exists
if os.path.isfile(output_file):
  print("Output file " + output_file + " already exists. Overwrite? (y/n)")
  overwrite = input()
  if overwrite == "y":
    # open output_file in binary write mode
    f = open(output_file, "wb")
    # write sysex to output_file
    f.write(sysex)
    f.close()
    print("Wrote sysex to " + output_file)
  else:
    print("Aborting.")
else:
  # open output_file in binary write mode
  f = open(output_file, "wb")
  # write sysex to output_file
  f.write(sysex)
  f.close()
  print("Wrote sysex to " + output_file)
