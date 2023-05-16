# run this script to generate gcode. make sure settings in gcode_maker.py match the settings for your printer.

import midi_parsing as mp
import gcode_maker as gm
from tkinter import filedialog
from tkinter import Tk

root = Tk()
root.withdraw()
file_names = filedialog.askopenfilename(filetypes = [('MIDI files','*.mid')], multiple = True)
file_names = list(file_names)

# strip .mid from full file path to replace later with .gcode
for i in range(len(file_names)):
    if '.mid' not in file_names[i]:
        raise Exception('Please select a MIDI file')
    file_names[i] = file_names[i].replace('.mid', '')

# strip file path from file names to print to console (better readability)
short_file_names = file_names[:]
for i in range(len(short_file_names)):
    while '/' in short_file_names[i]:
        short_file_names[i] = short_file_names[i][(short_file_names[i].find('/') + 1):]

# use midi files for generation of musical gcode
source_files = file_names[:]
target_files = file_names[:]
for i in range(len(file_names)):
    source_files[i] = file_names[i] + '.mid'
    target_files[i] = file_names[i] + '.gcode'

# enable/disable output from mp.parse
verbose = True

# generate gcode files
for i in range(len(file_names)):
    print(f'\n{short_file_names[i]}')
    sync = mp.parse(source_files[i], verbose)
    gm.printer_gcode(target_files[i], sync)
print('\nFinished\n')