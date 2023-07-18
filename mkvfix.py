#!/usr/bin/env python

import subprocess
import json
import langcodes
import sys

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

filename = ''
tracks = []


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
        props = track['properties']
        track_id = props['number']

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

        props['default_track'] = False

        return name


    def handle_audio_track(track):
        props = track['properties']
        codec = track["codec"]
        channels = props['audio_channels']

        # rename audio tracks
        lng = props['language']
        channel_str = channels_to_str(channels)

        # get map of instances of lang for this codec type...
        codec_name = codec + channel_str

        if codec_name in audio_track_type_count:
            audio_tracks = audio_track_type_count[codec_name]
        else:
            audio_tracks = audio_track_type_count[codec_name] = {}

        instances = audio_tracks[lng] + 1 if lng in audio_tracks else 1
        audio_tracks[lng] = instances
        name = langcodes.get(lng).display_name() + channel_str
        if instances > 1:
            name = f'{name} {instances}'

        return name


    if not filename:
        return

    # open file
    data = load(filename)

    tracks = []

    for track in data['tracks']:
        track_type = track['type']

        # handle audio tracks
        if track_type == 'audio':
            track['properties']['new_name'] = handle_audio_track(track)
            tracks.append(track)

        # handle subtitle tracks
        elif track_type == 'subtitles':
            track['properties']['new_name'] = handle_subtitle_track(track)
            tracks.append(track)

    return tracks


def choose_file():
    global entry_filename, filename, tracks

    filename = filedialog.askopenfilename(filetypes=[('mkv files', '.mkv')])

    if filename:
        entry_filename.configure(state=ACTIVE)
        entry_filename.delete(0, END)
        entry_filename.insert(0, filename)
        entry_filename.configure(state=DISABLED)
        tracks = process(filename)
        display_tracks(tracks)


def display_tracks(tracks):
    global treeview_tracks

    # clear any existing data
    treeview_tracks.delete(*treeview_tracks.get_children())

    # load test data into treeview
    for track in tracks:
        track_type = track['type']
        props = track['properties']

        codec_id = track['codec']
        name = props['track_name'] if 'track_name' in props else ''
        new_name = props['new_name'] if 'new_name' in props else ''

        if track_type == 'audio':
            default = '✔︎' if props['default_track'] else ''
            treeview_tracks.insert(parent='', iid=track['id'], index=END, text='', values=(default, 'Audio', codec_id, name, new_name))

        # handle subtitle tracks
        elif track_type == 'subtitles':
            default = '✔︎' if props['forced_track'] else ''
            treeview_tracks.insert(parent='', iid=track['id'], index=END, text='', values=(default, 'Subtitle', codec_id, name, new_name))


def save(filename, tracks):
    args = []

    for track in tracks:
        props = track['properties']
        args.extend(['--edit', f'track:@{props["number"]}'])

        if track['type'] == 'audio':
            args.extend(['--set', f'name=\'{props["new_name"]}\''])
            args.extend(['--set', f'flag-default={props["default_track"]}'])

        elif track['type'] == 'subtitles':
            args.extend(['--set', f'name=\'{props["new_name"]}\''])
            args.extend(['--set', f'flag-default={props["default_track"]}'])
            args.extend(['--set', f'flag-forced={props["forced_track"]}'])

    print(f'Saving file: {filename}...')
    results = subprocess.run(['mkvpropedit'] + args + [filename], capture_output=True)
    print(results.stdout.decode('ascii'))

    return


class ConsoleText(Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state=DISABLED)

    def write(self, message):
        self.configure(state=NORMAL)
        self.insert(END, message)
        self.configure(state=DISABLED)
        self.yview(END)


class TrackView(Treeview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Double-Button-1>', self.on_double_click)
        self.bind('<Button-1>', self.on_click)

    def on_click(self, event):
        global tracks

        region = self.identify_region(event.x, event.y)
        if region == 'cell':
            entry_iid = self.identify_row(event.y)
            row = int(entry_iid) - 1
            col = int(self.identify_column(event.x)[1:]) - 1

            if col == 0:
                # toggle default / forced
                track = tracks[row]
                if track['type'] == 'audio':
                    track['properties']['default_track'] = False if track['properties']['default_track'] else True

                if track['type'] == 'subtitles':
                    # might have to add forced track!
                    if 'forced_track' not in track['properties']:
                        track['properties'].forced_track = False

                    track['properties']['forced_track'] = False if track['properties']['forced_track'] else True

                values = self.item(entry_iid).get('values')
                values[0] = '✔︎' if values[0] == '' else ''
                self.item(entry_iid, values=values)


    def on_double_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region == 'cell':
            row = self.identify_row(event.y)
            col = self.identify_column(event.x)
            x, y, w, h = self.bbox(row, column=col)
            col_index = int(col[1:]) - 1
            row_index = int(row) - 1
            cell = self.item(row)
            values = cell.get('values')
            value = values[col_index]

            if col_index == 4:
                overlay = Entry(self)
                overlay.insert(0, value)
                overlay.select_range(0, END)
                overlay.focus()

                overlay.bind('<FocusOut>', self.on_focus_out_name)
                overlay.bind('<Return>', self.on_return_name)

                overlay.target_iid = row
                overlay.target_col = col_index
                overlay.target_row = row_index

                overlay.place(x=x, y=y, width=w, height=h)

    def on_focus_out_name(self, event):
        event.widget.destroy()

    def on_return_name(self, event):
        global tracks
        widget = event.widget

        value = widget.get()
        iid = widget.target_iid
        col = widget.target_col
        row = widget.target_row

        values = self.item(iid).get('values')
        values[col] = value
        self.item(iid, values=values)

        tracks[row]['properties']['new_name'] = value

        event.widget.destroy()


#------------------------------------
#          Set up UI...
#------------------------------------

# root window
root = Tk()
root.title('MKV Tool')
root.minsize(800, 475)
root.geometry('800x475+350+150')
root.config(bg='lightgrey')
root.resizable(True, True)

# frames
frame_top = Frame(root)
frame_top.pack(expand=False, anchor=N, fill=BOTH, padx=3, pady=3)

frame_center = Panedwindow(root, orient=VERTICAL)
frame_center.pack(expand=True, fill=BOTH)

frame_log = Frame(frame_center, borderwidth=5, relief=RIDGE)
frame_center.add(frame_log)
# frame_log.pack(expand=True, anchor=N, fill=BOTH)

frame_tracks = Frame(frame_center, borderwidth=2, relief=RIDGE)
frame_center.add(frame_tracks)
# frame_tracks.pack(expand=True, anchor=N, fill=BOTH, side=TOP, padx=4, pady=1)

frame_bottom = Frame(root)
frame_bottom.pack(expand=False, anchor=N, fill=BOTH, padx=3, pady=3)

# file selector
file_label = Label(frame_top, text='Target file:')
file_label.pack(side=LEFT)

entry_filename = Entry(frame_top)
entry_filename.insert(0, 'Select a file...')
entry_filename.configure(state=DISABLED)
entry_filename.pack(expand=True, side=LEFT, fill=X)

btn_choose = Button(frame_top, text='Choose', command=choose_file)
btn_choose.pack(side=RIGHT)

# console output
txt_output = ConsoleText(frame_log, font="Courier 14", height=12)
txt_output.pack(expand=True, fill=BOTH)

# Tracks treeview
treeview_tracks = TrackView(frame_tracks, columns=('forced', 'type', 'codec', 'orig_name', 'new_name'), selectmode=BROWSE)

# format treeview
treeview_tracks.column('#0', width=0, stretch=False)
treeview_tracks.column('forced', width=30, stretch=False, anchor=CENTER)
treeview_tracks.column('type', width=100, stretch=False, anchor=W)
treeview_tracks.column('codec', width=150, stretch=False, anchor=W)
treeview_tracks.column('orig_name', width=100, stretch=True, anchor=W)
treeview_tracks.column('new_name', width=100, stretch=True, anchor=W)

treeview_tracks.heading('#0', text='?', anchor=W)
treeview_tracks.heading('forced', text='*', anchor=CENTER)
treeview_tracks.heading('type', text='Type', anchor=CENTER)
treeview_tracks.heading('codec', text='Codec', anchor=W)
treeview_tracks.heading('orig_name', text='Original Name', anchor=W)
treeview_tracks.heading('new_name', text='New Name', anchor=W)

treeview_tracks.pack(expand=True, fill=BOTH)

# Process button
btn_process = Button(frame_bottom, text='Update', command=lambda: save(filename, tracks))
btn_process.pack(side=RIGHT)

sys.stdout = txt_output
sys.stderr = txt_output

root.mainloop()
