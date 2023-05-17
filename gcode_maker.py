import numpy as np

# returns an array of settings for the printer
def printer_settings():

    # # configuration for: Ender 3

    # x_microstepping = 16
    # y_microstepping = 16
    # z_microstepping = 16

    # x_steps_mm = 5*x_microstepping
    # y_steps_mm = 5*y_microstepping
    # z_steps_mm = 25*z_microstepping

    # x_feed_max = 12000 # mm/min
    # y_feed_max = 12000 # mm/min
    # z_feed_max = 600 # mm/min
    # e_feed = -30 # mm/min

    # x_upper_limit = 220-10
    # y_upper_limit = 220-10
    # z_upper_limit = 250-10

    # x_lower_limit = 0+10
    # y_lower_limit = 0+10
    # z_lower_limit = 0+10

    # start_position_x = 110
    # start_position_y = 110
    # start_position_z = 125
    # start_position_e = 0

    # axis_labels = ['X', 'Y', 'Z', 'E'] # last axis must be E, not used to play notes
    # center_axis = [True, True, True, False]

    # settings_0 = [x_microstepping, y_microstepping, z_microstepping]
    # settings_1 = [x_steps_mm, y_steps_mm, z_steps_mm]
    # settings_2 = [x_feed_max, y_feed_max, z_feed_max, e_feed]
    # settings_3 = [x_upper_limit, y_upper_limit, z_upper_limit]
    # settings_4 = [x_lower_limit, y_lower_limit, z_lower_limit]
    # settings_5 = [start_position_x, start_position_y, start_position_z, start_position_e]
    # settings_6 = [axis_labels, center_axis]

    # configuration for: Lukrative525's custom printer (with modified settings)
 
    x_microstepping = 16
    y_microstepping = 16
    z_microstepping = 16
    a_microstepping = 16
    b_microstepping = 16

    x_steps_mm = 6.25*x_microstepping
    y_steps_mm = 6.25*y_microstepping
    z_steps_mm = 25*z_microstepping
    a_steps_mm = 10*a_microstepping
    b_steps_mm = 10*b_microstepping

    x_feed_max = 7527 # mm/min
    y_feed_max = 7527 # mm/min
    z_feed_max = 941 # mm/min
    a_feed_max = 4704 # mm/min
    b_feed_max = 4704 # mm/min
    e_feed = -30 # mm/min

    x_upper_limit = 128-10
    y_upper_limit = 110-10
    z_upper_limit = 200-10
    a_upper_limit = 200-10
    b_upper_limit = 200-10

    x_lower_limit = -128+10
    y_lower_limit = -110+10
    z_lower_limit = 0+10
    a_lower_limit = -200+10
    b_lower_limit = -200+10

    start_position_x = 0
    start_position_y = 0
    start_position_z = 100
    start_position_a = 0
    start_position_b = 0
    start_position_e = 0

    axis_labels = ['X', 'Y', 'Z', 'A', 'B', 'E'] # last axis must be E, not used to play notes
    center_axis = [True, True, True, False, False, False] # whether to actually move axis to center position (True) or to set to start position with G92 command (False)

    settings_0 = [x_microstepping, y_microstepping, z_microstepping, a_microstepping, b_microstepping]
    settings_1 = [x_steps_mm, y_steps_mm, z_steps_mm, a_steps_mm, b_steps_mm]
    settings_2 = [x_feed_max, y_feed_max, z_feed_max, a_feed_max, b_feed_max, e_feed]
    settings_3 = [x_upper_limit, y_upper_limit, z_upper_limit, a_upper_limit, b_upper_limit]
    settings_4 = [x_lower_limit, y_lower_limit, z_lower_limit, a_lower_limit, b_lower_limit]
    settings_5 = [start_position_x, start_position_y, start_position_z, start_position_a, start_position_b, start_position_e]
    settings_6 = [axis_labels, center_axis]

    # wrapping up

    settings = [settings_0, settings_1, settings_2, settings_3, settings_4, settings_5, settings_6]

    return(settings)

# for calculating frequencies of notes
def frequency(midi):

    # this formula calculates the frequency of our key number based on A440, key number 69
    frequency = 440*(2**((midi-69)/12))

    return frequency

# for generating musical gcode to run on FDM 3D printers
# file_name is a string containing the file you want to write the gcode to.
# sync is an array containing the correctly formatted notes. times in milliseconds.
def printer_gcode(file_name, sync):

    # log debugging data?
    debugging = True

    # import printer settings
    settings = printer_settings()

    channels = len(sync) - 1
    file_length = len(sync[0])
    frequencies = np.zeros((channels, file_length))
    durations = np.zeros((file_length))
    feeds = np.zeros((channels + 1, file_length))
    lengths = np.zeros((channels + 1, file_length))
    directions = np.ones(channels)
    positions = np.zeros(len(settings[6][0]))

    # go through each channel
    for j in range(channels):
        # go through each time segment
        for i in range(file_length):
            # only do these checks if the note doesn't contain a string
            if isinstance(sync[j][i][0], str) == False:
                # if the note is being turned ON
                if sync[j][i][0] > 0 and sync[j][i][1] == 1:
                    frequencies[j][i] = frequency(sync[j][i][0])
                # if the note is being turned OFF
                elif sync[j][i][0] > 0 and sync[j][i][1] == 0:
                    # then set frequency to 0
                    frequencies[j][i] = 0
                # if the note is not being turned OFF, but also not being turned ON
                elif sync[j][i][0] == 0 and sync[j][i][1] == 0:
                    # use the previous note frequency
                    frequencies[j][i] = frequencies[j][i - 1]
            # if there is a string, then it must be a key change or time signature change
            else:
                # use the previous note frequency
                frequencies[j][i] = frequencies[j][i - 1]

    for i in range(file_length):
        # set durations to whatever they are in 'sync'
        durations[i] = sync[0][i][2]

    # set feeds for non-extruder moves
    for j in range(channels):
        for i in range(file_length):
            feeds[j][i] = (frequencies[j][i]*60)/settings[1][j]
    # set feeds for extruder
    for i in range(file_length):
        feeds[-1][i] = settings[2][-1]

    # check to make sure the feeds required aren't too high for the printer
    axis_labels = settings[6][0]
    for j in range(channels):
        if np.amax(feeds[j]) > settings[2][j]:
            raise Exception(f'Feeds too high for the {axis_labels[j]} axis at {np.amax(feeds[j])} mm/min. Lower pitch of that channel or increase axis max feed rate.\n')

    # set movement lengths
    for j in range(channels + 1):
        for i in range(file_length):
            lengths[j][i] = feeds[j][i]*durations[i]/60000

    # set starting positions
    for j in range(channels + 1):
        positions[j] = settings[5][j]
    
    if len(axis_labels) - 1 < channels:
        raise Exception('Number of channels exceeds available axis labels. Remove channels or add more axes.')
    output = open(file_name, 'w')
    
    # allow cold extrusion
    output.write('M302 P1; allow cold extrusion\n')
    # relative extrusion
    output.write('M83; relative extruder moves\n')
    # reset these axes instead of centering
    for j in range(len(axis_labels)):
        if settings[6][1][j] == False:
            # reset axis instead of centering
            output.write(f'G92 {axis_labels[j]}0; reset {axis_labels[j]} axis/axes\n')
    # center these axes
    output.write('G1 F60000000')
    for j in range(len(axis_labels)):
        if settings[6][1][j] == True:
            output.write(f' {axis_labels[j]}{str(settings[5][j])}')
    output.write('; center axis/axes\n')
    output.write('G4 S1; pause for a second\n')

    # go line by line
    for i in range(file_length):
        # check to see if any of the non-extruder axes are moving
        moving = False
        for j in range(channels):
            if frequencies[j][i] != 0:
                moving = True

        # if there are moving non-extruder axes
        if moving == True:
            # for each non-extruder axis in this line
            for k in range(channels):
                # if we're not at the first line,
                if i > 0:
                    # and there's a break in between notes
                    if feeds[k][i - 1] == 0:
                        directions[k] = directions[k] * -1
                positions[k] += directions[k]*lengths[k][i] # calculate new position
                # if new position is outside limits:
                if positions[k] > settings[3][k] or positions[k] < settings[4][k]:
                    directions[k] = -1*directions[k] # reverse direction
                    positions[k] += 2*directions[k]*lengths[k][i] # and calculate new position in the opposite direction
                    # if new position is still outside limits:
                    if positions[k] > settings[3][k] or positions[k] < settings[4][k]:
                        raise Exception(f'Note either too high, too long, or both. The note is a {sync[j][i][0]}')
            
            # for the extruder, don't use cumulative distance travelled (since in relative mode)
            positions[-1] = lengths[-1][i]

            # calculate the overall feed rate for this move...
            feed_rate = 0
            # ...using all non-extruder axes
            for k in range(channels):
                feed_rate += (feeds[k][i])**2
            feed_rate = np.sqrt(feed_rate)

        else: # otherwise, assume the extruder is the only thing moving:
            positions[-1] = lengths[-1][i] # calculate new position
            feed_rate = feeds[-1][i]
        
        # write out the gcode command
        output.write(f'G1 F{str(np.around(np.abs(feed_rate), 5))}')
        for k in range(len(settings[6][0])):
            output.write(f' {axis_labels[k]}{str(np.around(positions[k], 5))}')
        output.write('\n')

    # disallow cold extrusion
    output.write(f'M302 P0; disallow cold extrusion\n')
    output.write('G4 S1; pause for a second')

    output.close()

    if debugging == True:
        data = open('data.txt', 'w')
        current_width = 0
        column_width = 10
        temp = frequencies
        for i in range(len(temp[0])):
            string = '['
            for j in range(len(temp)):
                string += str(np.around(temp[j][i], 2))
                current_width = len(string) - 1
                if current_width < column_width * (j + 1):
                    for k in range(current_width, column_width * (j + 1)):
                        string += ' '
            string += str(np.around(durations[i]))
            current_width = len(string) - 1
            if current_width < column_width * (j + 2):
                for k in range(current_width, column_width * (j + 2)):
                    string += ' '
            string += ']'
            data.write(string)
            data.write('\n')
        data.close()

    return(0)