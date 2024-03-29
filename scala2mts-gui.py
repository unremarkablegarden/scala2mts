#!/usr/bin/env python3
# Path: scala2mts-gui.py
# Author: Olle Holmberg, 2022
# License: GPL v3
# v0.0.5 - 2023-06-30
# 
# https://github.com/unremarkablegarden/scala2mts
# 
# Reference: https://musescore.org/sites/musescore.org/files/2018-06/midituning.pdf


import tkinter as tk
from tkinter import filedialog
import os
import math
import functools
import operator
import traceback
import chardet



def convert_file():
	input_file = input_entry.get()
	output_file = output_entry.get()
	base_note = base_note_entry.get()
	base_freq = base_freq_entry.get()
	program_number = program_number_entry.get()
	
	# Validate input
	if not os.path.isfile(input_file):
		result_label.config(text="Invalid input file!")
		return

	# Execute your conversion logic here
	try:
		convert_scl_to_syx(input_file, output_file, base_note, base_freq, program_number)
		# deal with the result
		# result_label.config(text="Conversion completed!")
	except Exception as e:
		result_label.config(text=str(e))
		traceback.print_exc()
		print(e)
	
	# result_label.config(text="Conversion completed!")

def browse_input_file():
	file_path = filedialog.askopenfilename(filetypes=[("Scala Files", "*.scl")])
	input_entry.delete(0, tk.END)
	input_entry.insert(tk.END, file_path)
	
	# Set the output file to be in the same directory with the same filename, except for the extension
	output_directory = os.path.dirname(file_path)
	output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".syx"
	output_entry.delete(0, tk.END)
	output_entry.insert(tk.END, os.path.join(output_directory, output_filename))


def browse_output_file():
	file_path = filedialog.asksaveasfilename(filetypes=[("SysEx Files", "*.syx")])
	output_entry.delete(0, tk.END)
	output_entry.insert(tk.END, file_path)



# Create main window
window = tk.Tk()
window.title("Scala to MIDI MTS SysEx Converter")

# Create input file selection
input_label = tk.Label(window, text="Input File:")
input_label.grid(row=0, column=0, sticky=tk.W)

input_entry = tk.Entry(window, width=50)
input_entry.grid(row=0, column=1)

browse_input_button = tk.Button(window, text="Browse", command=browse_input_file)
browse_input_button.grid(row=0, column=2)

# Create output file selection
output_label = tk.Label(window, text="Output File:")
output_label.grid(row=1, column=0, sticky=tk.W)

output_entry = tk.Entry(window, width=50)
output_entry.grid(row=1, column=1)

browse_output_button = tk.Button(window, text="Browse", command=browse_output_file)
browse_output_button.grid(row=1, column=2)

# Create base note entry
base_note_label = tk.Label(window, text="Base Note:")
base_note_label.grid(row=2, column=0, sticky=tk.W)

base_note_entry = tk.Entry(window, width=10)
base_note_entry.grid(row=2, column=1)
base_note_entry.insert(tk.END, "69")

# Create base frequency entry
base_freq_label = tk.Label(window, text="Base Frequency:")
base_freq_label.grid(row=3, column=0, sticky=tk.W)

base_freq_entry = tk.Entry(window, width=10)
base_freq_entry.grid(row=3, column=1)
base_freq_entry.insert(tk.END, "440.000")

# Create program number entry
program_number_label = tk.Label(window, text="Program Number:")
program_number_label.grid(row=4, column=0, sticky=tk.W)

program_number_entry = tk.Entry(window, width=10)
program_number_entry.grid(row=4, column=1)
program_number_entry.insert(tk.END, "0")

# Create convert button
convert_button = tk.Button(window, text="Convert", command=convert_file)
convert_button.grid(row=5, column=0, columnspan=3)

# Create result label
result_label = tk.Label(window, text="")
result_label.grid(row=6, column=0, columnspan=3)

def convert_scl_to_syx(input_file, output_file, base_note, base_freq, program_number):
	input_file = str(input_file)
	output_file = str(output_file)
	base_note = int(base_note)
	base_freq = float(base_freq)
	program_number = int(program_number)
	
	"""
	Convert Scala files to SysEx files for use with the Prophet rev2 and Cirklon.
	MTS - MIDI Tuning standard 1.0

	(Works with scala files that use ratios or cents)

	Arguments:
	-i input file: the Scala file to convert
	-o output file: the SysEx file to create (default: the input file name with .syx extension)
	-n base_note: the base note as a number (default = 69 = A4)
	-f base_freq: the base frequency of the Scala file (default = 440.000)
	-p program_number: which memory slot to store the tuning in the synth
	-h help: show this help message
	"""

	# define defaults
	# input_file = None
	# output_file = None
	# program_number = 1
	# base_note = 69
	# base_freq = 440
	# base_note = 48
	# base_freq = 261.625565

	# parse command line arguments
			
	# check for required arguments
	if input_file is None:
		# print("Error: input file is required")
		# throw Exception to the the tkinter window, this function is being try: except:ed
		raise Exception("Input file is required")
		
	# set output file name if not specified
	if output_file is None:
		raise Exception("Output file is required")	

	# read the Scala file, new
	# Open the file in binary mode to avoid decoding errors
	with open(input_file, 'rb') as f:
		# Detect the file encoding
		result = chardet.detect(f.read())
		file_encoding = result['encoding']

	# Reopen the file with the detected encoding and convert it to UTF-8
	with open(input_file, 'r', encoding=file_encoding) as f:
		scala_lines = f.readlines()

	# parse the Scala file
	scala_name = scala_lines[0].strip()
	# remove the ! and space from the name
	scala_name = scala_name[2:]
	# remove the .scl extension
	scala_name = scala_name.replace(".scl", "")
	# replace dashes and underlines with spaces
	# scala_name = scala_name.replace("-", " ")
	# scala_name = scala_name.replace("_", " ")


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
	for i in range(len(scala_notes)):
			if "/" in scala_notes[i]:
					ratio = ratio_to_float(scala_notes[i])
					cents = ratio_to_cents(ratio)
					scala_cents.append(cents) 
			else: 
					scala_cents.append(scala_notes[i])

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
		note = int(note)
		base_note = int(base_note)
		base_freq = float(base_freq)
		notes_per_octave = int(notes_per_octave)
		
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
							repeated 128 times, one for each MIDI note number
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
	# AND with 7F
	checksum = checksum & 0x7F
	# convert checksum to hex
	checksum = num_to_hex(checksum)

	# sysex
	sysex = header + " " + data + " " + checksum + " " + footer

	# remove spaces from sysex
	sysex = sysex.replace(" ", "")

	# convert sysex to bytes
	sysex = bytes.fromhex(sysex)

	# print()

	def write_file(sysex):
		# open output_file in binary write mode
		f = open(output_file, "wb")
		# write sysex to output_file
		f.write(sysex)
		f.close()
		print("Wrote sysex to " + output_file)
		result_label.config(text="Wrote sysex to " + output_file)
		return "Wrote sysex to " + output_file
		
		

	# check if output_file exists
	if os.path.isfile(output_file):
		# exception if output_file exists
		raise Exception("Output file " + str(output_file) + " already exists.")
	else:
		write_file(sysex)
		# return success message in try: except: block
		return "Wrote sysex to " + output_file



# Start the GUI event loop
window.mainloop()
