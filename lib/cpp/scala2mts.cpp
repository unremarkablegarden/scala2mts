/*
 * scala2mts.cpp
 * Convert Scala files to SysEx files for MTS (MIDI Tuning Standard 1.0)
 *
 * Author: Olle Holmberg, 2022-2023
 * C++ port: 2026
 * License: GPL v3
 *
 * https://github.com/unremarkablegarden/scala2mts
 * Reference: https://musescore.org/sites/musescore.org/files/2018-06/midituning.pdf
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdint>
#include <algorithm>
#include <iomanip>
#include <getopt.h>

class ScalaScale {
public:
    std::string name;
    std::string description;
    int notes_per_octave = 0;
    std::vector<double> cents;
    std::vector<double> ratios;

    bool parseFile(const std::string& filename);

private:
    static std::string trim(const std::string& str);
    static double ratioStringToFloat(const std::string& str);
    static double ratioToCents(double ratio);
};

class MTSConverter {
public:
    static double centsToRatio(double cents);
    static double noteToHz(int note, int baseNote, double baseFreq,
                           const std::vector<double>& ratios, int notesPerOctave);
    static void hzToFreqData(double freq, uint8_t* out);
    static std::vector<uint8_t> buildSysex(const ScalaScale& scale,
                                            int baseNote, double baseFreq,
                                            int programNumber);
};

// Trim whitespace from both ends of string
std::string ScalaScale::trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\r\n");
    return str.substr(start, end - start + 1);
}

// Convert ratio string like "3/2" or "700.0" to float
double ScalaScale::ratioStringToFloat(const std::string& str) {
    size_t slashPos = str.find('/');
    size_t colonPos = str.find(':');

    if (slashPos != std::string::npos) {
        double num = std::stod(str.substr(0, slashPos));
        double denom = std::stod(str.substr(slashPos + 1));
        if (denom != 0.0) return num / denom;
        return 0.0;
    } else if (colonPos != std::string::npos) {
        double num = std::stod(str.substr(0, colonPos));
        double denom = std::stod(str.substr(colonPos + 1));
        if (denom != 0.0) return num / denom;
        return 0.0;
    }

    return std::stod(str);
}

// Convert ratio to cents
double ScalaScale::ratioToCents(double ratio) {
    if (ratio > 0.0) {
        return 1200.0 * std::log2(ratio);
    }
    return 0.0;
}

// Parse Scala file
bool ScalaScale::parseFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: cannot open file " << filename << std::endl;
        return false;
    }

    std::string line;
    bool foundDescription = false;
    bool foundNoteCount = false;

    // First line is the name (starts with !)
    if (std::getline(file, line)) {
        line = trim(line);
        if (line.size() >= 2 && line[0] == '!' && line[1] == ' ') {
            name = line.substr(2);

            // Remove path if present
            size_t lastSlash = name.rfind('/');
            if (lastSlash != std::string::npos) {
                name = name.substr(lastSlash + 1);
            }

            // Remove .scl extension
            size_t extPos = name.find(".scl");
            if (extPos != std::string::npos) {
                name = name.substr(0, extPos);
            }

            // Truncate to 16 characters
            if (name.length() > 16) {
                name = name.substr(0, 16);
            }
        }
    }

    // Parse remaining lines
    while (std::getline(file, line)) {
        line = trim(line);

        // Skip empty lines
        if (line.empty()) continue;

        // Skip comment lines
        if (line[0] == '!') continue;

        // First non-comment line is the description
        if (!foundDescription) {
            description = line;
            foundDescription = true;
            continue;
        }

        // Second non-comment line is the note count
        if (!foundNoteCount) {
            notes_per_octave = std::stoi(line);
            foundNoteCount = true;
            continue;
        }

        // Remaining lines are note values
        double value;
        if (line.find('/') != std::string::npos || line.find(':') != std::string::npos) {
            double ratio = ratioStringToFloat(line);
            value = ratioToCents(ratio);
        } else {
            value = std::stod(line);
        }
        cents.push_back(value);
    }

    file.close();

    // Compute ratios from cents
    ratios.push_back(1.0);  // Base ratio
    for (double c : cents) {
        ratios.push_back(MTSConverter::centsToRatio(c));
    }

    return true;
}

// Convert cents to ratio
double MTSConverter::centsToRatio(double cents) {
    return std::pow(2.0, cents / 1200.0);
}

// Calculate frequency of a note
double MTSConverter::noteToHz(int note, int baseNote, double baseFreq,
                               const std::vector<double>& ratios, int notesPerOctave) {
    int noteInOctave = (note - baseNote) % notesPerOctave;
    int octave = (note - baseNote) / notesPerOctave;

    // Handle negative modulo
    if (noteInOctave < 0) {
        noteInOctave += notesPerOctave;
        octave -= 1;
    }

    double octaveSize = ratios[notesPerOctave];
    double ratio = ratios[noteInOctave];

    return baseFreq * std::pow(octaveSize, octave) * ratio;
}

// Convert frequency to MTS frequency data (3 bytes)
void MTSConverter::hzToFreqData(double freq, uint8_t* out) {
    // Limit frequency to MIDI range
    if (freq < 8.1757989156) {
        freq = 8.1757989156;
    } else if (freq > 12543.853951) {
        freq = 12543.853951;
    }

    // Calculate semitone and cents
    double semitoneF = 12.0 * std::log2(freq / 440.0) + 69.0;
    int semitone = static_cast<int>(std::round(semitoneF));

    double totalCents = std::round(1200.0 * std::log2(freq / 440.0) + 6900.0);
    double centsFraction = totalCents - (semitone * 100.0);

    if (centsFraction < 0) {
        semitone -= 1;
        centsFraction += 100.0;
    }

    // Clamp semitone to valid range
    if (semitone < 0) semitone = 0;
    if (semitone > 127) semitone = 127;

    // Calculate MSB and LSB
    int msb = static_cast<int>(centsFraction / 0.78125);
    double rest = std::fmod(centsFraction, 0.78125);
    int lsb = static_cast<int>(rest / 0.0061);

    // Clamp to 7-bit values
    if (msb > 127) msb = 127;
    if (lsb > 127) lsb = 127;

    out[0] = static_cast<uint8_t>(semitone);
    out[1] = static_cast<uint8_t>(msb);
    out[2] = static_cast<uint8_t>(lsb);
}

// Build SysEx message
std::vector<uint8_t> MTSConverter::buildSysex(const ScalaScale& scale,
                                               int baseNote, double baseFreq,
                                               int programNumber) {
    std::vector<uint8_t> sysex;

    // Calculate all frequencies
    std::vector<double> freqs(128);
    for (int i = 0; i < 128; i++) {
        freqs[i] = noteToHz(i, baseNote, baseFreq, scale.ratios, scale.notes_per_octave);
    }

    // Header: F0 7E 00 08 01 tt
    sysex.push_back(0xF0);
    sysex.push_back(0x7E);
    sysex.push_back(0x00);
    sysex.push_back(0x08);
    sysex.push_back(0x01);
    sysex.push_back(static_cast<uint8_t>(programNumber & 0x7F));

    // Tuning name (16 ASCII characters)
    for (int i = 0; i < 16; i++) {
        if (i < static_cast<int>(scale.name.length())) {
            char c = scale.name[i];
            if (c >= 32 && c <= 126) {
                sysex.push_back(static_cast<uint8_t>(c));
            } else {
                sysex.push_back(' ');
            }
        } else {
            sysex.push_back(' ');
        }
    }

    // Frequency data (128 notes * 3 bytes = 384 bytes)
    uint8_t freqData[3];
    for (int i = 0; i < 128; i++) {
        hzToFreqData(freqs[i], freqData);
        sysex.push_back(freqData[0]);
        sysex.push_back(freqData[1]);
        sysex.push_back(freqData[2]);
    }

    // Calculate checksum: XOR of bytes from 7E to end of tuning data, AND 0x7F
    uint8_t checksum = 0;
    for (size_t i = 1; i < sysex.size(); i++) {
        checksum ^= sysex[i];
    }
    checksum &= 0x7F;

    sysex.push_back(checksum);
    sysex.push_back(0xF7);

    return sysex;
}

void printUsage() {
    std::cout << "Convert Scala files to SysEx files for use with the Prophet rev2 and Cirklon.\n";
    std::cout << "MTS - MIDI Tuning standard 1.0\n\n";
    std::cout << "(Works with scala files that use ratios or cents)\n\n";
    std::cout << "Arguments:\n";
    std::cout << "-i input file: the Scala file to convert\n";
    std::cout << "-o output file: the SysEx file to create (default: the input file name with .syx extension)\n";
    std::cout << "-n base_note: the base note as a number (default = 69 = A4)\n";
    std::cout << "-f base_freq: the base frequency of the Scala file (default = 440.000)\n";
    std::cout << "-p program_number: which memory slot to store the tuning in the synth\n";
    std::cout << "-h help: show this help message\n";
}

bool fileExists(const std::string& filename) {
    std::ifstream f(filename);
    return f.good();
}

int main(int argc, char* argv[]) {
    std::string inputFile;
    std::string outputFile;
    int baseNote = 69;
    double baseFreq = 440.0;
    int programNumber = 1;

    int opt;
    while ((opt = getopt(argc, argv, "hi:o:n:f:p:")) != -1) {
        switch (opt) {
            case 'h':
                printUsage();
                return 0;
            case 'i':
                inputFile = optarg;
                break;
            case 'o':
                outputFile = optarg;
                break;
            case 'n':
                baseNote = std::stoi(optarg);
                break;
            case 'f':
                baseFreq = std::stod(optarg);
                break;
            case 'p':
                programNumber = std::stoi(optarg);
                break;
            default:
                printUsage();
                return 2;
        }
    }

    // Check for required arguments
    if (inputFile.empty()) {
        if (argc == 1) {
            printUsage();
            return 0;
        }
        std::cerr << "Error: input file is required\n";
        return 2;
    }

    // Set default output file
    if (outputFile.empty()) {
        outputFile = inputFile;
        size_t dotPos = outputFile.rfind('.');
        if (dotPos != std::string::npos) {
            outputFile = outputFile.substr(0, dotPos);
        }
        outputFile += ".syx";
    }

    // Parse Scala file
    ScalaScale scale;
    if (!scale.parseFile(inputFile)) {
        return 1;
    }

    // Print info
    std::cout << "Base note: " << baseNote << "\n";
    std::cout << "Base freq: " << baseFreq << "\n";
    std::cout << "Notes per octave: " << scale.notes_per_octave << "\n";
    std::cout << "————————————————————\n";
    std::cout << "Intervals\n";
    for (size_t i = 0; i < scale.cents.size(); i++) {
        std::cout << (i + 1) << " = " << std::fixed << std::setprecision(3) << scale.cents[i] << "\n";
    }
    std::cout << "————————————————————\n";

    // Build SysEx message
    std::vector<uint8_t> sysex = MTSConverter::buildSysex(scale, baseNote, baseFreq, programNumber);

    // Print SysEx data
    for (size_t i = 0; i < sysex.size(); i++) {
        std::cout << std::hex << std::uppercase << std::setfill('0') << std::setw(2)
                  << static_cast<int>(sysex[i]);
        if ((i + 1) % 35 == 0) {
            std::cout << "\n";
        } else if ((i + 1) % 2 == 0) {
            std::cout << " ";
        }
    }
    std::cout << std::dec << "\n————————————————————\n\n";

    // Check if output file exists
    if (fileExists(outputFile)) {
        std::cout << "Output file " << outputFile << " already exists. Overwrite? (y/n) [enter]\n";
        std::string response;
        std::getline(std::cin, response);
        if (response.empty() || (response[0] != 'y' && response[0] != 'Y')) {
            std::cout << "Aborting.\n";
            return 0;
        }
    }

    // Write output file
    std::ofstream outFile(outputFile, std::ios::binary);
    if (!outFile.is_open()) {
        std::cerr << "Error: cannot create file " << outputFile << "\n";
        return 1;
    }

    outFile.write(reinterpret_cast<const char*>(sysex.data()), sysex.size());
    outFile.close();

    std::cout << "Wrote sysex to " << outputFile << "\n";
    return 0;
}
