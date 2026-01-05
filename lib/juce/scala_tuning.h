/*
 * scala_tuning.h
 * Header-only C++ library for Scala tuning file support
 *
 * Convert MIDI notes to frequencies/ratios using microtonal scales.
 * Designed for real-time audio applications (JUCE, etc.)
 *
 * Author: Olle Holmberg, 2022-2023
 * Library version: 2026
 * License: GPL v3
 *
 * https://github.com/unremarkablegarden/scala2mts
 *
 * Usage:
 *   scala::Tuning tuning;
 *   tuning.loadFile("my_scale.scl");
 *   double freq = tuning.noteToHz(60);  // Get frequency for MIDI note 60
 */

#ifndef SCALA_TUNING_H
#define SCALA_TUNING_H

#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <cmath>
#include <array>
#include <algorithm>
#include <cctype>

namespace scala {

class Tuning {
public:
    Tuning() {
        // Initialize with 12-TET as fallback
        initDefault12TET();
    }

    /**
     * Load a Scala (.scl) file.
     * @param filename Path to the .scl file
     * @return true if successful, false on error
     */
    bool loadFile(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            return false;
        }

        std::string line;
        bool foundDescription = false;
        bool foundNoteCount = false;

        cents_.clear();
        ratios_.clear();

        // First line is the name (starts with !)
        if (std::getline(file, line)) {
            line = trim(line);
            if (line.size() >= 2 && line[0] == '!' && line[1] == ' ') {
                name_ = line.substr(2);

                // Remove path if present
                size_t lastSlash = name_.rfind('/');
                if (lastSlash != std::string::npos) {
                    name_ = name_.substr(lastSlash + 1);
                }

                // Remove .scl extension
                size_t extPos = name_.find(".scl");
                if (extPos != std::string::npos) {
                    name_ = name_.substr(0, extPos);
                }
            }
        }

        // Parse remaining lines
        while (std::getline(file, line)) {
            line = trim(line);

            if (line.empty()) continue;
            if (line[0] == '!') continue;

            if (!foundDescription) {
                description_ = line;
                foundDescription = true;
                continue;
            }

            if (!foundNoteCount) {
                notesPerOctave_ = std::stoi(line);
                foundNoteCount = true;
                continue;
            }

            // Parse interval (ratio or cents)
            double cents = parseInterval(line);
            cents_.push_back(cents);
        }

        file.close();

        // Compute ratios from cents
        ratios_.push_back(1.0);  // Base ratio (unison)
        for (double c : cents_) {
            ratios_.push_back(centsToRatio(c));
        }

        loaded_ = true;
        computeTables();
        return true;
    }

    /**
     * Set the base MIDI note (default: 69 = A4)
     * Call computeTables() or loadFile() after changing.
     */
    void setBaseNote(int note) {
        baseNote_ = note;
        if (loaded_) computeTables();
    }

    /**
     * Set the base frequency in Hz (default: 440.0)
     * Call computeTables() or loadFile() after changing.
     */
    void setBaseFrequency(double hz) {
        baseFreq_ = hz;
        if (loaded_) computeTables();
    }

    /**
     * Convert MIDI note to frequency in Hz.
     * O(1) lookup - safe for audio thread.
     * @param midiNote MIDI note number (0-127)
     * @return Frequency in Hz
     */
    double noteToHz(int midiNote) const {
        if (midiNote < 0) midiNote = 0;
        if (midiNote > 127) midiNote = 127;
        return freqTable_[midiNote];
    }

    /**
     * Convert MIDI note to ratio (relative to base note).
     * O(1) lookup - safe for audio thread.
     * @param midiNote MIDI note number (0-127)
     * @return Ratio relative to base frequency
     */
    double noteToRatio(int midiNote) const {
        if (midiNote < 0) midiNote = 0;
        if (midiNote > 127) midiNote = 127;
        return ratioTable_[midiNote];
    }

    /**
     * Get the number of notes per octave in the loaded scale.
     */
    int getNotesPerOctave() const {
        return notesPerOctave_;
    }

    /**
     * Get the scale name (from .scl file).
     */
    const std::string& getName() const {
        return name_;
    }

    /**
     * Get the scale description (from .scl file).
     */
    const std::string& getDescription() const {
        return description_;
    }

    /**
     * Get the interval values in cents.
     */
    const std::vector<double>& getCents() const {
        return cents_;
    }

    /**
     * Get the interval ratios.
     */
    const std::vector<double>& getRatios() const {
        return ratios_;
    }

    /**
     * Check if a scale file has been successfully loaded.
     */
    bool isLoaded() const {
        return loaded_;
    }

    /**
     * Get the current base note.
     */
    int getBaseNote() const {
        return baseNote_;
    }

    /**
     * Get the current base frequency.
     */
    double getBaseFrequency() const {
        return baseFreq_;
    }

private:
    std::string name_;
    std::string description_;
    int notesPerOctave_ = 12;
    int baseNote_ = 69;
    double baseFreq_ = 440.0;

    std::vector<double> cents_;
    std::vector<double> ratios_;
    std::array<double, 128> freqTable_;
    std::array<double, 128> ratioTable_;
    bool loaded_ = false;

    /**
     * Initialize with standard 12-tone equal temperament.
     */
    void initDefault12TET() {
        notesPerOctave_ = 12;
        name_ = "12-TET";
        description_ = "12-tone equal temperament";

        cents_.clear();
        ratios_.clear();

        // 12-TET intervals in cents
        for (int i = 1; i <= 12; i++) {
            cents_.push_back(100.0 * i);
        }

        // Compute ratios
        ratios_.push_back(1.0);
        for (double c : cents_) {
            ratios_.push_back(centsToRatio(c));
        }

        computeTables();
    }

    /**
     * Pre-compute frequency and ratio tables for all 128 MIDI notes.
     */
    void computeTables() {
        for (int note = 0; note < 128; note++) {
            double ratio = computeNoteRatio(note);
            ratioTable_[note] = ratio;
            freqTable_[note] = baseFreq_ * ratio;
        }
    }

    /**
     * Compute the ratio for a specific MIDI note relative to base.
     */
    double computeNoteRatio(int note) const {
        int noteInOctave = (note - baseNote_) % notesPerOctave_;
        int octave = (note - baseNote_) / notesPerOctave_;

        // Handle negative modulo for notes below base
        if (noteInOctave < 0) {
            noteInOctave += notesPerOctave_;
            octave -= 1;
        }

        double octaveSize = ratios_[notesPerOctave_];
        double ratio = ratios_[noteInOctave];

        return std::pow(octaveSize, octave) * ratio;
    }

    /**
     * Convert cents to frequency ratio.
     */
    static double centsToRatio(double cents) {
        return std::pow(2.0, cents / 1200.0);
    }

    /**
     * Parse an interval string (ratio like "3/2" or cents like "700.0").
     * @return Interval in cents
     */
    static double parseInterval(const std::string& str) {
        // Check for ratio format (contains / or :)
        size_t slashPos = str.find('/');
        size_t colonPos = str.find(':');

        if (slashPos != std::string::npos) {
            double num = std::stod(str.substr(0, slashPos));
            double denom = std::stod(str.substr(slashPos + 1));
            if (denom != 0.0) {
                return ratioToCents(num / denom);
            }
            return 0.0;
        } else if (colonPos != std::string::npos) {
            double num = std::stod(str.substr(0, colonPos));
            double denom = std::stod(str.substr(colonPos + 1));
            if (denom != 0.0) {
                return ratioToCents(num / denom);
            }
            return 0.0;
        }

        // Plain cents value
        return std::stod(str);
    }

    /**
     * Convert frequency ratio to cents.
     */
    static double ratioToCents(double ratio) {
        if (ratio > 0.0) {
            return 1200.0 * std::log2(ratio);
        }
        return 0.0;
    }

    /**
     * Trim whitespace from both ends of a string.
     */
    static std::string trim(const std::string& str) {
        size_t start = str.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        size_t end = str.find_last_not_of(" \t\r\n");
        return str.substr(start, end - start + 1);
    }
};

} // namespace scala

#endif // SCALA_TUNING_H
