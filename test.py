from mido import MidiFile
from pydub import AudioSegment
from collections import defaultdict
from pydub.generators import Sine

def note_to_freq(note, concert_A=440.0):
    '''
    from wikipedia: http://en.wikipedia.org/wiki/MIDI_Tuning_Standard#Frequency_values
    '''
    return (2.0 ** ((note - 69) / 12.0)) * concert_A

song_name = "Hallelujah"
mid = MidiFile(f"midi/{song_name}.mid")
output = AudioSegment.silent(mid.length * 1000.0)

tempo = 100  # bpm


def ticks_to_ms(ticks):
    tick_ms = (60000.0 / tempo) / mid.ticks_per_beat
    return ticks * tick_ms

def note_to_wav(note,wave,start,end):
    duration = end - start

    if duration <= 50:
        return wave

    signal_generator = Sine(note_to_freq(note))
    rendered = signal_generator.to_audio_segment(duration=duration - 50, volume=-20).fade_out(100).fade_in(30)

    return wave.overlay(rendered, start)


for track in mid.tracks:
    # position of rendering in ms
    current_pos = 0.0

    current_notes = defaultdict(dict)
    held_notes = defaultdict(dict)

    # current_notes = {
    #   channel: {
    #     note: (start_time, message)
    #   }
    # }
    hold = defaultdict(lambda: False)

    for msg in track:
        current_pos += ticks_to_ms(msg.time)
        print(msg)
        if msg.type == "control_change" and msg.control==64 :
            held = hold[msg.channel]= msg.value >= 64
            if not held:
                notes_to_play = held_notes[msg.channel]
                for note, (start_pos,start_msg) in notes_to_play.items():
                    output = note_to_wav(note,output,start_pos,current_pos)

                held_notes[msg.channel] = dict()

        if msg.type == 'note_on' and msg.velocity > 0:
            current_notes[msg.channel][msg.note] = (current_pos, msg)

        if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            try:
                start_pos, start_msg = current_notes[msg.channel].pop(msg.note)
                # old_notes
                if hold[msg.channel]:
                    held_notes[msg.channel][msg.note] = (start_pos,start_msg)
                else:

                    output = note_to_wav(msg.note,output,start_pos,current_pos)
            except KeyError as e:
                #print(msg,e)
                pass

output.export(f"output/{song_name}.wav", format="wav")
