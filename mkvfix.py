#!/usr/bin/env python

import subprocess
import json
import langcodes
import sys

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

filename = ''


def process(filename):
    S_VOBSUB = {}
    S_TEXT = {}

    audio_types = {}
    audio_type_pref = ['DTS-HD Master Audio', 'DTS', 'AAC', 'AC-3']
    audio_lang_pref = 'eng'
    audio_track_type_count = {}

    mkvpropedit_options = []

    needs_review = False
    debug = False

    def load(filename):
        print(f'Loading: {filename}...')
        results = subprocess.run(["mkvmerge", "-J", f'{filename}'], capture_output=True)
        data = json.loads(results.stdout)

        return data

    def get_prop(props, item, default=""):
        return props[item] if item in props else default

    def channels_to_str(channels):
        if channels < 1:
            return ''

        elif channels == 1:
            return ' Mono'

        elif channels == 2:
            return ' Stereo'

        else:
            return f' {channels - 1}.1'

    def handle_subtitle_track(track):
        global needs_review
        props = track['properties']
        track_id = props['number']
        flag = '* ' if props['default_track'] else '  '

        # find subtitle type
        if props['codec_id'] == 'S_VOBSUB':
            subtitle_tracks = S_VOBSUB
        else:
            subtitle_tracks = S_TEXT

        # determine subtitle track 'name'
        lng = props['language']
        instances = subtitle_tracks[lng] + 1 if lng in subtitle_tracks else 1
        subtitle_tracks[lng] = instances
        name = langcodes.get(lng).display_name()
        if instances > 1:
            name = f'{name} {instances}'
            needs_review = True

        if debug: print(f'{flag}Subtitle track language: {name}')
        mkvpropedit_options.append(f'--edit')
        mkvpropedit_options.append(f'track:@{track_id}')
        mkvpropedit_options.append(f'--set')
        mkvpropedit_options.append(f'name=\'{name}\'')

        if props['default_track']:
            mkvpropedit_options.append(f'--set')
            mkvpropedit_options.append(f'flag-default=0')

    def handle_audio_track(track):
        global needs_review
        props = track['properties']
        track_id = props['number']
        flag = '* ' if props['default_track'] else '  '
        codec = track["codec"]
        channels = props['audio_channels']

        rank = audio_type_pref.index(codec) + 1 if codec in audio_type_pref else 0

        if rank == 0:
            print(f'unknown audio codec: {codec}')

        # rename audio tracks
        lng = props['language']

        # get map of instances of lang for this codec type...
        if codec in audio_track_type_count:
            audio_tracks = audio_track_type_count[codec]
        else:
            audio_tracks = audio_track_type_count[codec] = {}

        instances = audio_tracks[lng] + 1 if lng in audio_tracks else 1
        audio_tracks[lng] = instances
        name = langcodes.get(lng).display_name() + channels_to_str(channels)
        if instances > 1:
            name = f'{name} {instances}'
            needs_review = True

        if debug:
            print(f'{flag}Audio track language: {name}')
            print(f'    codec: {codec} ({props["codec_id"]}), rank: {rank}, instances: {instances}, channels: {channels}, {get_prop(props, "audio_bits_per_sample", "16")}/{get_prop(props, "audio_sampling_frequency")}')

        mkvpropedit_options.append(f'--edit')
        mkvpropedit_options.append(f'track:@{track_id}')
        mkvpropedit_options.append(f'--set')
        mkvpropedit_options.append(f'name=\'{name}\'')

        # set preferred track (DTS > DD)
        # duplicate english track may be commentary

    if not filename:
        return

    # open file
    data = load(filename)

    for track in data['tracks']:
        track_type = track['type']

        # handle audio tracks
        if track_type == 'audio':
            handle_audio_track(track)

        # handle subtitle tracks
        elif track_type == 'subtitles':
            handle_subtitle_track(track)

        else:
            if debug:
                print(f'skipping track: {track_type}')

    results = subprocess.run(['mkvpropedit'] + mkvpropedit_options + [filename], capture_output=True)
    print(results.stdout.decode('ascii'))

    if needs_review:
        print('Needs review!')


def choose_file():
    global filename, file_name
    filename = filedialog.askopenfilename()
    file_name.configure(state=ACTIVE)
    file_name.delete(0, END)
    file_name.insert(0, filename)
    file_name.configure(state=DISABLED)


class ConsoleText(Text):
    def write(self, message):
        self.configure(state=NORMAL)
        self.insert(END, message)
        self.configure(state=DISABLED)
        self.yview(END)


root = Tk()
root.title('MKV Tool')
root.minsize(800, 450)
root.geometry('1000x600+350+150')
root.config(bg='lightgrey')
root.resizable(True, True)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

frame_top = Frame(root)
frame_top.pack(expand=False, anchor=W, fill=BOTH, padx=3, pady=3)

frame_mid = Frame(root, borderwidth=3, relief=RIDGE)
frame_mid.pack(expand=True, anchor=S, fill=BOTH, padx=4, pady=1)

frame_bottom = Frame(root)
frame_bottom.pack(expand=False, anchor=S, fill=BOTH, padx=3, pady=3)

file_label = Label(frame_top, text='Target file:')
file_label.pack(side=LEFT)

file_name = Entry(frame_top)
file_name.insert(0, 'Select a file...')
file_name.configure(state=DISABLED)
file_name.pack(expand=True, side=LEFT, fill=X)

btn_choose = Button(frame_top, text='Choose', command=choose_file)
btn_choose.pack(side=RIGHT)

txt_output = ConsoleText(frame_mid, font="Courier 14")
txt_output.pack(expand=True, fill=BOTH)

btn_process = Button(frame_bottom, text='Process', command=lambda: process(filename))
btn_process.pack(side=RIGHT)

sys.stdout = txt_output
sys.stderr = txt_output

root.mainloop()
