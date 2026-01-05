/*
 * scala2mts.c
 * Convert Scala files to SysEx files for MTS (MIDI Tuning Standard 1.0)
 *
 * Author: Olle Holmberg, 2022-2023
 * C port: 2026
 * License: GPL v3
 *
 * https://github.com/unremarkablegarden/scala2mts
 * Reference: https://musescore.org/sites/musescore.org/files/2018-06/midituning.pdf
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <getopt.h>
#include <ctype.h>
#include <stdint.h>

#define MAX_NOTES 128
#define MAX_LINE 1024
#define MAX_SCALE_NOTES 128
#define SYSEX_SIZE (6 + 16 + 384 + 2)  /* header + name + tuning data + checksum + footer */

/* Default values */
static int base_note = 69;
static double base_freq = 440.0;
static int program_number = 1;
static char *input_file = NULL;
static char *output_file = NULL;

/* Scale data */
typedef struct {
    char name[17];           /* 16 chars + null */
    char description[256];
    int notes_per_octave;
    double cents[MAX_SCALE_NOTES];
    double ratios[MAX_SCALE_NOTES + 1];  /* +1 for base ratio at index 0 */
    int num_notes;
} ScalaScale;

static void print_usage(void) {
    printf("Convert Scala files to SysEx files for use with the Prophet rev2 and Cirklon.\n");
    printf("MTS - MIDI Tuning standard 1.0\n\n");
    printf("(Works with scala files that use ratios or cents)\n\n");
    printf("Arguments:\n");
    printf("-i input file: the Scala file to convert\n");
    printf("-o output file: the SysEx file to create (default: the input file name with .syx extension)\n");
    printf("-n base_note: the base note as a number (default = 69 = A4)\n");
    printf("-f base_freq: the base frequency of the Scala file (default = 440.000)\n");
    printf("-p program_number: which memory slot to store the tuning in the synth\n");
    printf("-h help: show this help message\n");
}

/* Convert a ratio string like "3/2" or "700.0" to a float */
static double ratio_to_float(const char *str) {
    char *colon, *slash;
    double num, denom;

    /* Check for ratio format (with / or :) */
    slash = strchr(str, '/');
    colon = strchr(str, ':');

    if (slash != NULL) {
        num = atof(str);
        denom = atof(slash + 1);
        if (denom != 0.0) {
            return num / denom;
        }
        return 0.0;
    } else if (colon != NULL) {
        num = atof(str);
        denom = atof(colon + 1);
        if (denom != 0.0) {
            return num / denom;
        }
        return 0.0;
    }

    /* Just a number (cents value) */
    return atof(str);
}

/* Convert a ratio to cents */
static double ratio_to_cents(double ratio) {
    if (ratio > 0.0) {
        return 1200.0 * log2(ratio);
    }
    return 0.0;
}

/* Convert cents to ratio */
static double cents_to_ratio(double cents) {
    return pow(2.0, cents / 1200.0);
}

/* Calculate frequency of a note */
static double note_to_hz(int note, int base_n, double base_f,
                         const double *ratios, int notes_per_octave) {
    int note_in_octave = (note - base_n) % notes_per_octave;
    int octave = (note - base_n) / notes_per_octave;
    double octave_size = ratios[notes_per_octave];
    double ratio;

    /* Handle negative modulo */
    if (note_in_octave < 0) {
        note_in_octave += notes_per_octave;
        octave -= 1;
    }

    ratio = ratios[note_in_octave];
    return base_f * pow(octave_size, octave) * ratio;
}

/* Convert frequency to MTS frequency data (3 bytes) */
static void hz_to_freq_data(double freq, uint8_t *out) {
    double semitone_f, cents, cents_fraction, msb_f, rest, lsb_f;
    int semitone, msb, lsb;

    /* Limit frequency to MIDI range */
    if (freq < 8.1757989156) {
        freq = 8.1757989156;
    } else if (freq > 12543.853951) {
        freq = 12543.853951;
    }

    /* Calculate semitone and cents */
    semitone_f = 12.0 * log2(freq / 440.0) + 69.0;
    semitone = (int)round(semitone_f);

    cents = round(1200.0 * log2(freq / 440.0) + 6900.0);
    cents_fraction = cents - (semitone * 100.0);

    if (cents_fraction < 0) {
        semitone -= 1;
        cents_fraction += 100.0;
    }

    /* Clamp semitone to valid range */
    if (semitone < 0) semitone = 0;
    if (semitone > 127) semitone = 127;

    /* Calculate MSB and LSB */
    msb_f = cents_fraction / 0.78125;
    msb = (int)msb_f;
    rest = fmod(cents_fraction, 0.78125);
    lsb_f = rest / 0.0061;
    lsb = (int)lsb_f;

    /* Clamp to 7-bit values */
    if (msb > 127) msb = 127;
    if (lsb > 127) lsb = 127;

    out[0] = (uint8_t)semitone;
    out[1] = (uint8_t)msb;
    out[2] = (uint8_t)lsb;
}

/* Trim whitespace from string */
static char *trim(char *str) {
    char *end;

    /* Trim leading space */
    while (isspace((unsigned char)*str)) str++;

    if (*str == 0) return str;

    /* Trim trailing space */
    end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;

    end[1] = '\0';
    return str;
}

/* Parse Scala file */
static int parse_scala_file(const char *filename, ScalaScale *scale) {
    FILE *f;
    char line[MAX_LINE];
    int found_description = 0;
    int found_note_count = 0;
    int note_index = 0;
    char *trimmed;
    char *last_slash;

    f = fopen(filename, "r");
    if (f == NULL) {
        fprintf(stderr, "Error: cannot open file %s\n", filename);
        return -1;
    }

    memset(scale, 0, sizeof(ScalaScale));

    /* First line is the name (starts with !) */
    if (fgets(line, sizeof(line), f) != NULL) {
        trimmed = trim(line);
        if (trimmed[0] == '!' && trimmed[1] == ' ') {
            strncpy(scale->name, trimmed + 2, 16);
            scale->name[16] = '\0';

            /* Remove path if present */
            last_slash = strrchr(scale->name, '/');
            if (last_slash != NULL) {
                memmove(scale->name, last_slash + 1, strlen(last_slash + 1) + 1);
            }

            /* Remove .scl extension */
            char *ext = strstr(scale->name, ".scl");
            if (ext != NULL) {
                *ext = '\0';
            }
        }
    }

    /* Parse remaining lines */
    while (fgets(line, sizeof(line), f) != NULL) {
        trimmed = trim(line);

        /* Skip empty lines */
        if (strlen(trimmed) == 0) continue;

        /* Skip comment lines */
        if (trimmed[0] == '!') continue;

        /* First non-comment line is the description */
        if (!found_description) {
            strncpy(scale->description, trimmed, sizeof(scale->description) - 1);
            found_description = 1;
            continue;
        }

        /* Second non-comment line is the note count */
        if (!found_note_count) {
            scale->notes_per_octave = atoi(trimmed);
            found_note_count = 1;
            continue;
        }

        /* Remaining lines are note values */
        if (note_index < MAX_SCALE_NOTES) {
            double value;

            /* Check if it's a ratio (contains / or :) */
            if (strchr(trimmed, '/') != NULL || strchr(trimmed, ':') != NULL) {
                double ratio = ratio_to_float(trimmed);
                value = ratio_to_cents(ratio);
            } else {
                value = atof(trimmed);
            }

            scale->cents[note_index] = value;
            note_index++;
        }
    }

    fclose(f);

    scale->num_notes = note_index;

    /* Compute ratios from cents */
    scale->ratios[0] = 1.0;  /* Base ratio */
    for (int i = 0; i < scale->num_notes; i++) {
        scale->ratios[i + 1] = cents_to_ratio(scale->cents[i]);
    }

    return 0;
}

/* Build SysEx message */
static int build_sysex(const ScalaScale *scale, uint8_t *sysex,
                       int base_n, double base_f, int prog_num) {
    int pos = 0;
    uint8_t checksum = 0;
    double freqs[128];
    uint8_t freq_data[3];
    int i;

    /* Calculate all frequencies */
    for (i = 0; i < 128; i++) {
        freqs[i] = note_to_hz(i, base_n, base_f, scale->ratios, scale->notes_per_octave);
    }

    /* Header: F0 7E 00 08 01 tt */
    sysex[pos++] = 0xF0;
    sysex[pos++] = 0x7E;
    sysex[pos++] = 0x00;
    sysex[pos++] = 0x08;
    sysex[pos++] = 0x01;
    sysex[pos++] = (uint8_t)(prog_num & 0x7F);

    /* Tuning name (16 ASCII characters) */
    for (i = 0; i < 16; i++) {
        if (i < (int)strlen(scale->name)) {
            /* Keep only ASCII printable characters */
            char c = scale->name[i];
            if (c >= 32 && c <= 126) {
                sysex[pos++] = (uint8_t)c;
            } else {
                sysex[pos++] = ' ';
            }
        } else {
            sysex[pos++] = ' ';
        }
    }

    /* Frequency data (128 notes * 3 bytes = 384 bytes) */
    for (i = 0; i < 128; i++) {
        hz_to_freq_data(freqs[i], freq_data);
        sysex[pos++] = freq_data[0];
        sysex[pos++] = freq_data[1];
        sysex[pos++] = freq_data[2];
    }

    /* Calculate checksum: XOR of bytes from 7E to end of tuning data, AND 0x7F */
    for (i = 1; i < pos; i++) {
        checksum ^= sysex[i];
    }
    checksum &= 0x7F;

    sysex[pos++] = checksum;
    sysex[pos++] = 0xF7;

    return pos;
}

/* Write SysEx file */
static int write_sysex_file(const char *filename, const uint8_t *sysex, int size) {
    FILE *f = fopen(filename, "wb");
    if (f == NULL) {
        fprintf(stderr, "Error: cannot create file %s\n", filename);
        return -1;
    }

    fwrite(sysex, 1, size, f);
    fclose(f);

    printf("Wrote sysex to %s\n", filename);
    return 0;
}

/* Check if file exists */
static int file_exists(const char *filename) {
    FILE *f = fopen(filename, "r");
    if (f != NULL) {
        fclose(f);
        return 1;
    }
    return 0;
}

int main(int argc, char *argv[]) {
    int opt;
    ScalaScale scale;
    uint8_t sysex[SYSEX_SIZE];
    int sysex_size;
    char default_output[256];
    int i;

    /* Parse command line arguments */
    while ((opt = getopt(argc, argv, "hi:o:n:f:p:")) != -1) {
        switch (opt) {
            case 'h':
                print_usage();
                return 0;
            case 'i':
                input_file = optarg;
                break;
            case 'o':
                output_file = optarg;
                break;
            case 'n':
                base_note = atoi(optarg);
                break;
            case 'f':
                base_freq = atof(optarg);
                break;
            case 'p':
                program_number = atoi(optarg);
                break;
            default:
                print_usage();
                return 2;
        }
    }

    /* Check for required arguments */
    if (input_file == NULL) {
        if (argc == 1) {
            print_usage();
            return 0;
        }
        fprintf(stderr, "Error: input file is required\n");
        return 2;
    }

    /* Set default output file */
    if (output_file == NULL) {
        strncpy(default_output, input_file, sizeof(default_output) - 5);
        char *dot = strrchr(default_output, '.');
        if (dot != NULL) {
            strcpy(dot, ".syx");
        } else {
            strcat(default_output, ".syx");
        }
        output_file = default_output;
    }

    /* Parse Scala file */
    if (parse_scala_file(input_file, &scale) != 0) {
        return 1;
    }

    /* Print info */
    printf("Base note: %d\n", base_note);
    printf("Base freq: %.3f\n", base_freq);
    printf("Notes per octave: %d\n", scale.notes_per_octave);
    printf("————————————————————\n");
    printf("Intervals\n");
    for (i = 0; i < scale.num_notes; i++) {
        printf("%d = %.3f\n", i + 1, scale.cents[i]);
    }
    printf("————————————————————\n");

    /* Build SysEx message */
    sysex_size = build_sysex(&scale, sysex, base_note, base_freq, program_number);

    /* Print SysEx data */
    for (i = 0; i < sysex_size; i++) {
        printf("%02X", sysex[i]);
        if ((i + 1) % 35 == 0) {
            printf("\n");
        } else if ((i + 1) % 2 == 0) {
            printf(" ");
        }
    }
    printf("\n————————————————————\n\n");

    /* Check if output file exists */
    if (file_exists(output_file)) {
        char response[16];
        printf("Output file %s already exists. Overwrite? (y/n) [enter]\n", output_file);
        if (fgets(response, sizeof(response), stdin) != NULL) {
            if (response[0] != 'y' && response[0] != 'Y') {
                printf("Aborting.\n");
                return 0;
            }
        }
    }

    /* Write output file */
    return write_sysex_file(output_file, sysex, sysex_size);
}
