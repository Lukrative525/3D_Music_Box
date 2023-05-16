import numpy as np

# for calculating variable-length quantities from midi files
def vlq(data, j):

    seeking = True
    vlq_value = 0
    vlq_length = 1
    while seeking:
        if data[j] >= 2**7:
            vlq_value = ((data[j] - 2**7) + vlq_value)*2**7
            j += 1
            vlq_length += 1
        else:
            vlq_value += data[j]
            seeking = False
        vlq = np.array([vlq_value, vlq_length])

    return(vlq)

# for determining order of channels
def order_channels(data):

    skips = 1
    mode = 'none'
    channel_number = None
    look_for_start = True
    channel_order = []

    for i in range(len(data)):

        # if we're looking for the start of a track
        if look_for_start is True:
            
            # starting from the beginning of the track (MTrk)
            if data[i] == 77 and data[i + 1] == 84 and data[i + 2] == 114 and data[i + 3] == 107:
                skips = 8
                mode = 'delta_next'
                look_for_start = False
        
        # if we're no longer looking for the start of a track
        elif look_for_start is False:

            # do nothing while i increases past bytes containing vlq or other info
            if skips > 1:
                skips -= 1

            # next byte(s) contain delta t information
            elif mode == 'delta_next':
                vlq_result = vlq(data, i)
                skips = vlq_result[1]
                mode = 'standby'
                        
            # determine what action to take
            elif mode == 'standby':

                # ------------
                # meta events:
                # ------------

                # sequence/track name FF 03
                if data[i] == 255 and data[i + 1] == 3 and mode == 'standby':
                    vlq_result = vlq(data, (i + 2))
                    chunk_length = vlq_result[0]
                    vlq_length = vlq_result[1]
                    skips = 2 + vlq_length + chunk_length
                    mode = 'delta_next'

                # midi port FF 21 01
                elif data[i] == 255 and data[i + 1] == 33 and data[i + 2] == 1 and mode == 'standby':
                    skips = 4
                    mode = 'delta_next'

                # end track FF 2F 00
                elif data[i] == 255 and data[i + 1] == 47 and data[i + 2] == 0 and mode == 'standby':
                    skips = 3
                    mode = 'delta_next'

                # tempo marking FF 51 03
                elif data[i] == 255 and data[i + 1] == 81 and data[i + 2] == 3 and mode == 'standby':
                    skips = 6
                    mode = 'delta_next'

                # time signature FF 58 04
                elif data[i] == 255 and data[i + 1] == 88 and data[i + 2] == 4 and mode == 'standby':
                    skips = 7
                    mode = 'delta_next'

                # key signature FF 59 02
                elif data[i] == 255 and data[i + 1] == 89 and data[i + 2] == 2 and mode == 'standby':
                    skips = 5
                    mode = 'delta_next'

                # -----------------------
                # channel voice messages:
                # -----------------------

                # channel end note 1000nnnn
                elif data[i] >= 128 and data[i] <= 143 and mode == 'standby':
                    channel_number = data[i] - 128
                    channel_order.append(channel_number)
                    skips = 3
                    mode = 'delta_next'
                    look_for_start = True

                # channel start note 1001nnnn
                elif data[i] >= 144 and data[i] <= 159 and mode == 'standby':
                    channel_number = data[i] - 144
                    channel_order.append(channel_number)
                    skips = 3
                    mode = 'delta_next'
                    look_for_start = True

                # channel control change 1011nnnn
                elif data[i] >= 176 and data[i] <= 191 and mode == 'standby':
                    channel_number = data[i] - 176
                    channel_order.append(channel_number)
                    skips = 3
                    mode = 'delta_next'
                    look_for_start = True

                # channel program change 1100nnnn
                elif data[i] >= 192 and data[i] <= 207 and mode == 'standby':
                    channel_number = data[i] - 192
                    channel_order.append(channel_number)
                    skips = 2
                    mode = 'delta_next'
                    look_for_start = True

                # -------------------------
                # midi controller messages:
                # -------------------------

                # midi pan 00001010
                elif data[i] == 10 and mode == 'standby':
                    skips = 2
                    mode = 'delta_next'

                # midi effects 1 depth 01011011
                elif data[i] == 91 and mode == 'standby':
                    skips = 2
                    mode = 'delta_next'

                # midi effects 2 depth 01011100 
                elif data[i] == 92 and mode == 'standby':
                    skips = 2
                    mode = 'delta_next'

                # midi effects 3 depth 01011101 
                elif data[i] == 93 and mode == 'standby':
                    skips = 2
                    mode = 'delta_next'

    return(channel_order)

# for parsing midi files into easy to use arrays of notes.
# file_name is a string containing the name of the midi file to read.
# verbose is true or false, depending on if you want to log parsing data
def parse(file_name, verbose):

    # log data?
    if verbose == True:
        debug = open('debug.txt', 'w')

    # open MIDI file
    input = open(file_name, 'rb')
    data = input.read()
    input.close
    length = len(data)

    # establish that this is a midi file
    is_midi = ''
    for i in range(4):
        is_midi += str(chr(data[i]))

    if is_midi != 'MThd':
        raise Exception('source file is not a midi file')

    # extract channel data from header
    channel_type = data[9]
    if channel_type == 0:
        channels = 1
    elif channel_type == 1:
        channels = data[10]*(2**8) + data[11]
    elif channel_type == 2:
        channels = data[10]*(2**8) + data[11]
    if verbose == True:
        debug.write(f'channel type: {channel_type}\n')
        debug.write(f'number of channels: {channels}\n')
    
    # create list of channels in order
    channel_order = order_channels(data)

    # create list to store note values
    notes = np.zeros((channels, length, 3), dtype = object)
    for i in range(channels):
        notes[i][0][0] = f'channel {i}'

    #  extract ticks per beat from header:
    if data[12] < 128: # check to see if leading bit is 0
        ticks_b = data[12]*(2**8) + data[13]
        if verbose == True:
            debug.write(f'ticks per beat: {ticks_b}\n')
    else:
        raise Exception('don\'t know how to handle this time format')

    # start parsing track chunks
    skips = 0
    mode = 'none'
    new_note = np.zeros(3, dtype = object)
    new_note[0] = -1
    channel_index = 0
    channel_number = channel_order[channel_index]
    status = 'none'
    position = 1

    for i in range(14, length):

        # do nothing while i increases past bytes containing vlq or other info
        if skips > 1:
            skips -= 1

        # starting from the beginning of the track (MTrk)
        elif data[i] == 77 and data[i + 1] == 84 and data[i + 2] == 114 and data[i + 3] == 107:
            if verbose == True:
                debug.write('starting next track\n')
            new_note[0] = 'new'
            skips = 8
            mode = 'delta_next'

        # next byte(s) contain delta t information
        elif mode == 'delta_next':
            vlq_result = vlq(data, i)
            delta = vlq_result[0]
            if verbose == True:
                debug.write(f'delta t: {delta}\n')
            # write new_note into notes
            new_note[2] = delta
            for j in range(3):
                notes[channel_number][position][j] = new_note[j]
            position += 1
            new_note = [-1, 0, 0]
            skips = vlq_result[1]
            mode = 'standby'
                    
        # determine what action to take
        elif mode == 'standby':

            # ------------
            # meta events:
            # ------------

            # sequence/track name FF 03
            if data[i] == 255 and data[i + 1] == 3 and mode == 'standby':
                vlq_result = vlq(data, (i + 2))
                chunk_length = vlq_result[0]
                vlq_length = vlq_result[1]
                name = ''
                for k in range(chunk_length):
                    name += chr(data[i + 2 + vlq_length + k])
                if '\x00' in name:
                    name = name.replace('\x00', '')
                if verbose == True:
                    debug.write(f'track name: {name}\n')
                new_note[0] = 'name'
                skips = 2 + vlq_length + chunk_length
                mode = 'delta_next'

            # midi port FF 21 01
            elif data[i] == 255 and data[i + 1] == 33 and data[i + 2] == 1 and mode == 'standby':
                port = data[i + 3]
                if verbose == True:
                    debug.write(f'port: {port}\n')
                new_note[0] = 'port'
                skips = 4
                mode = 'delta_next'

            # end track FF 2F 00
            elif data[i] == 255 and data[i + 1] == 47 and data[i + 2] == 0 and mode == 'standby':
                if verbose == True:
                    debug.write('end track\n')
                new_note[0] = 'end'
                for j in range(3):
                    notes[channel_number][position][j] = new_note[j]
                    # reset new_note
                for j in range(1,3):
                    new_note[j] = 0
                new_note[0] = -1
                skips = 3
                mode = 'delta_next'
                status = 'none'
                position = 1
                if channel_index < channels - 1:
                    channel_index += 1
                    channel_number = channel_order[channel_index]

            # tempo marking FF 51 03
            elif data[i] == 255 and data[i + 1] == 81 and data[i + 2] == 3 and mode == 'standby':
                mspb = data[i + 3]*2**16 + data[i + 4]*2**8 + data[i + 5]
                if verbose == True:
                    debug.write(f'microseconds per beat: {mspb}\n')
                # write to new_note
                new_note[0] = 'tempo'
                new_note[1] = mspb
                skips = 6
                mode = 'delta_next'

            # time signature FF 58 04
            elif data[i] == 255 and data[i + 1] == 88 and data[i + 2] == 4 and mode == 'standby':
                numerator = data[i + 3]
                denominator = 2**data[i + 4]
                if verbose == True:
                    debug.write(f'time signature: {numerator}/{denominator}\n')
                new_note[0] = 'time'
                skips = 7
                mode = 'delta_next'

            # key signature FF 59 02
            elif data[i] == 255 and data[i + 1] == 89 and data[i + 2] == 2 and mode == 'standby':
                if verbose == True:
                    debug.write('key signature\n')
                new_note[0] = 'key'
                skips = 5
                mode = 'delta_next'

            # -----------------------
            # channel voice messages:
            # -----------------------

            # channel end note 1000nnnn
            elif data[i] >= 128 and data[i] <= 143 and mode == 'standby':
                channel_number = data[i] - 128
                note = data[i + 1]
                volume = data[i + 2]
                if verbose == True:
                    debug.write(f'channel number: {channel_number}\n')
                    debug.write(f'note number: {note}\n')
                    debug.write(f'note volume: {volume}\n')
                # write to new_note
                new_note[0] = note
                new_note[1] = volume
                skips = 3
                mode = 'delta_next'
                status = 'end note'

            # channel start note 1001nnnn
            elif data[i] >= 144 and data[i] <= 159 and mode == 'standby':
                channel_number = data[i] - 144
                note = data[i + 1]
                volume = data[i + 2]
                if verbose == True:
                    debug.write(f'channel number: {channel_number}\n')
                    debug.write(f'note number: {note}\n')
                    debug.write(f'note volume: {volume}\n')
                # write to new_note
                new_note[0] = note
                new_note[1] = volume
                skips = 3
                mode = 'delta_next'
                status = 'start note'

            # channel control change 1011nnnn
            elif data[i] >= 176 and data[i] <= 191 and mode == 'standby':
                channel_number = data[i] - 176
                control_number = data[i + 1]
                assigned_value = data[i + 2]
                if verbose == True:
                    debug.write(f'channel number: {channel_number}\n')
                    debug.write(f'control number: {control_number}\n')
                    debug.write(f'assigned value: {assigned_value}\n')
                new_note[0] = 'control'
                skips = 3
                mode = 'delta_next'
                status = 'control change'

            # channel program change 1100nnnn
            elif data[i] >= 192 and data[i] <= 207 and mode == 'standby':
                channel_number = data[i] - 192
                program_number = data[i + 1]
                if verbose == True:
                    debug.write(f'channel number: {channel_number}\n')
                    debug.write(f'program number: {program_number}\n')
                new_note[0] = 'program'
                skips = 2
                mode = 'delta_next'
                status = 'program change'

            # --------------------------------------
            # running status channel voice messages:
            # --------------------------------------
            
            # channel end note 1000nnnn (running status)
            elif status == 'end note' and mode == 'standby':
                note = data[i]
                volume = data[i + 1]
                if verbose == True:
                    debug.write(f'implied channel number: {channel_number}\n')
                    debug.write(f'note number: {note}\n')
                    debug.write(f'note volume: {volume}\n')
                # write to new_note
                new_note[0] = note
                new_note[1] = volume
                skips = 2
                mode = 'delta_next'

            # channel start note 1001nnnn (running status)
            elif status == 'start note' and mode == 'standby':
                note = data[i]
                volume = data[i + 1]
                if verbose == True:
                    debug.write(f'implied channel number: {channel_number}\n')
                    debug.write(f'note number: {note}\n')
                    debug.write(f'note volume: {volume}\n')
                # write to new_note
                new_note[0] = note
                new_note[1] = volume
                skips = 2
                mode = 'delta_next'

            # channel control change 1011nnnn (running status)
            elif status == 'control change' and mode == 'standby':
                control_number = data[i]
                assigned_value = data[i + 1]
                if verbose == True:
                    debug.write(f'implied channel number: {channel_number}\n')
                    debug.write(f'control number: {control_number}\n')
                    debug.write(f'assigned value: {assigned_value}\n')
                new_note[0] = 'control'
                skips = 2
                mode = 'delta_next'

            # channel program change 1100nnnn (running status)
            elif status == 'program change' and mode == 'standby':
                program_number = data[i]
                if verbose == True:
                    debug.write(f'implied channel number: {channel_number}\n')
                    debug.write(f'program number: {program_number}\n')
                new_note[0] = 'program'
                skips = 1
                mode = 'delta_next'

            # -------------------------
            # midi controller messages:
            # -------------------------

            # midi pan 00001010
            elif data[i] == 10 and mode == 'standby':
                pan = data[i + 1]
                if verbose == True:
                    debug.write(f'pan: {pan}\n')
                new_note[0] = 'pan'
                skips = 2
                mode = 'delta_next'

            # midi effects 1 depth 01011011
            elif data[i] == 91 and mode == 'standby':
                depth = data[i + 1]
                if verbose == True:
                    debug.write(f'effects 1 depth: {depth}\n')
                new_note[0] = 'effects'
                skips = 2
                mode = 'delta_next'

            # midi effects 2 depth 01011100 
            elif data[i] == 92 and mode == 'standby':
                depth = data[i + 1]
                if verbose == True:
                    debug.write(f'effects 2 depth: {depth}\n')
                new_note[0] = 'effects'
                skips = 2
                mode = 'delta_next'

            # midi effects 3 depth 01011101 
            elif data[i] == 93 and mode == 'standby':
                depth = data[i + 1]
                if verbose == True:
                    debug.write(f'effects 3 depth: {depth}\n')
                new_note[0] = 'effects'
                skips = 2
                mode = 'delta_next'

        if verbose == True:
            debug.write(f'data[{i}] is {data[i]}\n')

    # create an array to store 'start' indices
    starts = np.zeros(len(notes), dtype = np.int64)
    # populate starts with indices of first note or tempo marking
    for j in range(len(notes)):
        for i in range(len(notes[j])):
            if notes[j][i][0] == 'tempo' or type(notes[j][i][0]) != str:
                starts[j] = i
                break

    # create an array to store 'end' indices
    ends = np.zeros(len(notes), dtype = np.int64)
    # populate ends with indices where 'end' is found:
    for j in range(len(notes)):
        for i in range(len(notes[j])):
            if notes[j][i][0] == 'end':
                ends[j] = i
                break

    # group delta t's with notes and tempo changes
    for j in range(len(notes)):
        # start at the end, go backward to element 1
        for i in range(ends[j], starts[j], -1):
            # if this event is not a note or tempo change
            if type(notes[j][i][0]) == str and notes[j][i - 1][0] != 'tempo':
                notes[j][i - 1][2] += notes[j][i][2]
                notes[j][i][2] = 0

    # switch from delta time to elapsed time
    for j in range(len(notes)):
        for i in range(2, ends[j]):
            notes[j][i][2] += notes[j][i - 1][2]

    # switch from end times to start times
    for j in range(len(notes)):
        for i in range(ends[j], starts[j] - 1, -1):
            notes[j][i][2] = notes[j][i - 1][2]

    # change volume to on/off
    for j in range(len(notes)):
        for i in range(1, ends[j]):
            if notes[j][i][1] != 0 and isinstance(notes[j][i][0], str) == False:
                notes[j][i][1] = 1

    # print out notes
    if verbose == True:
        debug.write('\nnotes\n')
        for j in range(len(notes)):
            debug.write('\n')
            for i in range(ends[j] + 1):
                debug.write(str(notes[j][i]) + '\n')

    # create list for filling with synchronized notes
    sync = np.zeros((channels + 1, length, 3), dtype = object)

    # create list containing time stamps to step through as we sync notes
    times = [0]
    for j in range(len(notes)):
        for i in range(1, ends[j] + 1):
            times.append(notes[j][i][2])

    # remove duplicates and sort
    times = sorted(list(set(times)))

    # populating sync
    position = -1
    starting_a_row = -1
    pick_up_from = np.ones(channels, dtype = np.int64)

    # check at every possible time stamp
    for i in times:

        # check each channel
        for j in range(len(notes)):

            # check each row in the channel
            for k in range(pick_up_from[j], ends[j] + 1):

                # if the time in notes matches i, and it's a note
                if notes[j][k][2] == i and type(notes[j][k][0]) != str:
                    
                    # if we've just gotten to this time stamp, make sure that we're beginning a new row in sync
                    if starting_a_row != i:
                        starting_a_row = i
                        position += 1
                        # make sure time info is correct in all columns
                        for m in range(len(sync)):
                            sync[m][position][2] = i

                    # copy notes over to sync
                    sync[j][position] = notes[j][k]

                # if the time in notes matches i, and it is a tempo change
                elif notes[j][k][2] == i and notes[j][k][0] == 'tempo':

                    # if we've just gotten to this time stamp, make sure that we're beginning a new row in sync
                    if starting_a_row != i:
                        starting_a_row = i
                        position += 1
                        # make sure time info is correct in all columns
                        for m in range(len(sync)):
                            sync[m][position][2] = i

                    # copy notes over to sync
                    sync[-1][position] = notes[j][k]
                
                # if this is the end of a track
                elif notes[j][k][2] == i and notes[j][k][0] == 'end':

                    # if we've just gotten to this time stamp, make sure that we're beginning a new row in sync
                    if starting_a_row != i:
                        starting_a_row = i
                        position += 1
                        # make sure time info is correct in all columns
                        for m in range(len(sync)):
                            sync[m][position][2] = i
                        
                    # copy notes over to sync
                    sync[j][position] = notes[j][k]
                
                # if the time stamp is greater than i, then we've gone too far and should stop
                elif notes[j][k][2] > i:
                    # record where to pick up from on the next go through (to save time)
                    pick_up_from[j] = k
                    break

    # # determine the last significant row of sync
    ends_found = 0
    for i in range(length):
        for j in range(channels):
            if sync[j][i][0] == 'end':
                sync_last = i
                ends_found += 1
                if ends_found == channels:
                    break

    sync = sync[:len(sync), :sync_last]

    # print out sync with time stamps
    if verbose == True:
        current_width = 0
        column_width = 20
        debug.write('\nsync with time stamps\n')
        for i in range(len(sync[0])):
            debug.write('\n')
            for j in range(len(sync)):
                current_width = len(str(sync[j][i]))
                debug.write(str(sync[j][i]))
                if current_width < column_width:
                    for k in range(current_width, column_width):
                        debug.write(' ')
        debug.write('\n')

    # switch times to durations
    # for each column:
    for j in range(len(sync)):
        # for each triple
        for i in range(sync_last - 1):
            # each time entry equals the next time minus the current one
            sync[j][i][2] = sync[j][i + 1][2] - sync[j][i][2]
    # change the last durations to 0
    for j in range(len(sync)):
        sync[j][-1][2] = 0

    current_mspb = sync[-1][0][1]
    # convert durations to milliseconds
    # for each column:
    for j in range(len(sync) - 1):
        # for each triple
        for i in range(sync_last):
            # check to see if the tempo has changed
            if sync[-1][i][0] == 'tempo':
                current_mspb = sync[-1][i][1]
            # 1000 for milliseconds
            temp = ticks_b * 1000
            temp = current_mspb / temp
            temp = temp * sync[j][i][2]
            temp = np.float64(temp)
            sync[j][i][2] = temp

    # print out sync with durations
    if verbose == True:
        current_width = 0
        column_width = 20
        debug.write('\nsync with durations\n')
        for i in range(len(sync[0])):
            debug.write('\n')
            for j in range(len(sync)):
                string = f'[{sync[j][i][0]} {sync[j][i][1]} {np.around(sync[j][i][2], 2)}]'
                debug.write(string)
                current_width = len(string)
                if current_width < column_width:
                    for k in range(current_width, column_width):
                        debug.write(' ')

    # close debug file
    if verbose == True:
        debug.close

    return(sync)