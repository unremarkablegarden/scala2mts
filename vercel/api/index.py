from flask import Flask, render_template, request, Response
import io, functools, operator, math

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                program_number = int(request.form.get('program_number', 0))
                base_note = int(request.form.get('base_note', 69))
                base_freq = float(request.form.get('base_freq', 440))
            except ValueError:
                return "Invalid input. Please provide valid numbers."

            text = file.read().decode('utf-8')
            output_filename = file.filename + ".syx"
            output_file = scl_to_syx(text, program_number, base_note, base_freq)

            return stream_file(output_file, output_filename)
            
        else:
            return 'Error: No file uploaded'
        
    return render_template('upload.html')

# --------------------------------------------------------

def stream_file(output_file, output_filename):
    def generate():
        yield output_file

    response = Response(generate(), mimetype='application/octet-stream')
    response.headers.set('Content-Disposition', 'attachment', filename=output_filename)
    return response

# --------------------------------------------------------

def scl_to_syx(file, program_number, base_note, base_freq):
    # Use the program_number, base_note, and base_freq as needed
    
    # parse the Scala file
    scala_lines = file.splitlines()
    scala_name = scala_lines[0].strip()
    # remove the ! and space from the name
    scala_name = scala_name[2:]
    # remove the .scl extension
    scala_name = scala_name.replace(".scl", "")

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

    
    # calculate ratios of scale
    scala_ratios = []
    for note in scala_cents:
        ratio = cents_to_ratio(float(note))
        scala_ratios.append(ratio)

    # add the base frequency to the start of the list
    scala_ratios.insert(0, 1)

    # calculate frequencies of notes
    scala_freqs = []
    for i in range(0, 128):
        freq = note_to_hz(i, base_note, base_freq, scala_ratios, notes_per_octave)
        scala_freqs.append(freq)

    # calculate freq_data of all notes in scala_freqs
    scala_freq_data = []
    for freq in scala_freqs:
        freq_data = hz_to_freq_data(freq)
        scala_freq_data.append(freq_data)

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
    
    # f.write(sysex)
    
    return sysex


# --------------------------------------------------------

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

# function to calculate ratio of cents
def cents_to_ratio(cents):
	ratio = 2**(cents/1200)
	return ratio

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
	
# --------------------------------------------------------

if __name__ == '__main__':
    app.run()
