#!/usr/bin/env python

import sys
import os
import subprocess
import json
import langcodes
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

# Disable system version compatibility mode on macOS to prevent warnings
if sys.platform == 'darwin':
    os.environ['SYSTEM_VERSION_COMPAT'] = '0'

# ==============================================================================
# Constants and Configuration
# ==============================================================================

TRACK_NAMES = [
    "Director's Commentary",
    "Writer's Commentary",
    "Composer's Commentary",
    "Producer's Commentary",
    "Additional Commentary",
    "Commentary",
    "Isolated Score",
    "Descriptive Audio",
]

CODEC_ABBREVIATIONS = {
    "DTS-HD Master Audio": "DTS-HD MA",
    "AC-3": "",
    "AC-3 Dolby Surround EX": "DD EX"
}

# ==============================================================================
# Helper Functions
# ==============================================================================

def get_bundled_path(tool_name):
    """Retrieves the absolute path to a bundled MKVToolNix binary."""
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        bundled_path = os.path.join(bundle_dir, 'bin', tool_name)
        if os.path.exists(bundled_path):
            return bundled_path
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'binaries', tool_name))

def channels_to_str(channels):
    """Converts a channel count integer into a human-readable string."""
    if channels < 1:
        return ''
    elif channels == 1:
        return ' Mono'
    elif channels == 2:
        return ' Stereo'
    else:
        return f' {channels - 1}.1'

# ==============================================================================
# Custom Widgets
# ==============================================================================

class ConsoleText(Text):
    """A specialized Text widget for console-like output."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(state=DISABLED)

    def write(self, message):
        self.configure(state=NORMAL)
        self.insert(END, message)
        self.configure(state=DISABLED)
        self.yview(END)

class TrackView(Treeview):
    """Custom Treeview widget for displaying and editing track information."""
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.active_overlay = None
        self.root_click_id = None
        self.bind('<Double-Button-1>', self.on_double_click)
        self.bind('<Button-1>', self.on_click)

    def on_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region == 'cell':
            entry_iid = self.identify_row(event.y)
            row_idx = int(entry_iid) - 1
            col_idx = int(self.identify_column(event.x)[1:]) - 1

            if col_idx == 0:
                track = self.app.tracks[row_idx]
                if track['type'] == 'audio':
                    track['properties']['default_track'] = not track['properties'].get('default_track', False)
                elif track['type'] == 'subtitles':
                    track['properties']['forced_track'] = not track['properties'].get('forced_track', False)

                values = list(self.item(entry_iid).get('values'))
                values[0] = '✔︎' if values[0] == '' else ''
                self.item(entry_iid, values=values)

    def on_double_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region == 'cell':
            row_iid = self.identify_row(event.y)
            col = self.identify_column(event.x)
            col_idx = int(col[1:]) - 1
            row_idx = int(row_iid) - 1
            values = self.item(row_iid).get('values')
            value = values[col_idx]

            if col_idx == 4:  # New Name column
                x, y, w, h = self.bbox(row_iid, column=col)
                overlay = Combobox(self, values=TRACK_NAMES)
                overlay.set(value)
                overlay.selection_range(0, END)
                overlay.icursor(END)
                overlay.focus()

                overlay.bind('<FocusOut>', self.save_value)
                overlay.bind('<Return>', self.save_value)

                overlay.target_iid = row_iid
                overlay.target_col = col_idx
                overlay.target_row = row_idx

                overlay.place(x=x, y=y, width=w, height=h)
                self.active_overlay = overlay
                self.root_click_id = self.winfo_toplevel().bind_all('<Button-1>', self.check_save_on_click, add="+")

            elif col_idx == 3:  # Original Name column
                self.app.tracks[row_idx]['properties']['new_name'] = value
                new_values = list(values)
                new_values[4] = value
                self.item(row_iid, values=new_values)

    def check_save_on_click(self, event):
        if not self.active_overlay or not self.active_overlay.winfo_exists():
            return

        w = event.widget
        if w == self.active_overlay or str(w).startswith(str(self.active_overlay) + "."):
            return

        try:
            popdown = self.active_overlay.tk.call('ttk::combobox::PopdownWindow', str(self.active_overlay))
            if w == popdown or str(w).startswith(str(popdown) + "."):
                return
        except:
            pass

        self.save_value(event)

    def save_value(self, event):
        widget = self.active_overlay if self.active_overlay else event.widget
        if not widget or not widget.winfo_exists():
            return

        value = widget.get()
        iid = widget.target_iid
        col = widget.target_col
        row = widget.target_row

        values = list(self.item(iid).get('values'))
        values[col] = value
        self.item(iid, values=values)

        self.app.tracks[row]['properties']['new_name'] = value

        widget.destroy()
        self.active_overlay = None
        if self.root_click_id:
            self.winfo_toplevel().unbind_all('<Button-1>')
            self.root_click_id = None

# ==============================================================================
# Main Application Class
# ==============================================================================

class MKVFixApp:
    def __init__(self, root):
        self.root = root
        self.filename = ''
        self.tracks = []
        
        self.setup_ui()
        self.setup_styles()

    def setup_styles(self):
        self.style = Style(self.root)
        self.style.theme_use('classic')
        self.style.configure('TFrame', background='lightgrey')
        self.style.configure('TLabel', font=('TkDefaultFont', 12))
        self.style.configure('TButton', font=('TkDefaultFont', 12), background='#007bff', foreground='white', highlightthickness=0)
        self.style.map('TButton', background=[('active', '#0056b3')], highlightbackground=[('active', '#0056b3')])
        self.style.configure('Treeview', font=('TkDefaultFont', 10), rowheight=20)
        self.style.configure('Treeview.Heading', font=('TkDefaultFont', 12, 'bold'))
        self.style.configure('TEntry', font=('TkDefaultFont', 11), insertcolor='black')
        self.style.map('TEntry', foreground=[('disabled', 'black')], insertcolor=[('focus', 'black')])
        self.style.configure('TCombobox', font=('TkDefaultFont', 11), insertcolor='black')
        self.style.map('TCombobox', insertcolor=[('focus', 'black')])

    def setup_ui(self):
        self.root.title('MKV Fix')
        self.root.minsize(800, 475)
        self.root.geometry('800x475+350+150')
        self.root.config(bg='lightgrey')

        # Top Frame: File selection
        frame_top = Frame(self.root)
        frame_top.pack(fill=X, padx=3, pady=3)

        Label(frame_top, text='Target file:').pack(side=LEFT)
        self.entry_filename = Entry(frame_top)
        self.entry_filename.insert(0, 'Select a file...')
        self.entry_filename.configure(state=DISABLED)
        self.entry_filename.pack(expand=True, side=LEFT, fill=X)

        Button(frame_top, text='Choose', command=self.choose_file).pack(side=RIGHT)

        # Bottom Frame: Actions
        frame_bottom = Frame(self.root)
        frame_bottom.pack(fill=X, padx=3, pady=3, side=BOTTOM)
        Button(frame_bottom, text='Update', command=self.save_metadata).pack(side=RIGHT)

        # Center PanedWindow
        self.paned = Panedwindow(self.root, orient=VERTICAL)
        self.paned.pack(expand=True, fill=BOTH)

        # Log Frame
        frame_log = Frame(self.paned, borderwidth=5, relief=RIDGE)
        self.paned.add(frame_log)
        self.txt_output = ConsoleText(frame_log, font="Courier 14", height=8, bg='white', fg='black', borderwidth=0, highlightthickness=0)
        self.txt_output.pack(expand=True, fill=BOTH)

        # Redirect stdout/stderr
        sys.stdout = self.txt_output
        sys.stderr = self.txt_output

        # Tracks Frame
        frame_tracks = Frame(self.paned, borderwidth=2, relief=RIDGE)
        self.paned.add(frame_tracks)
        self.treeview = TrackView(frame_tracks, self, columns=('forced', 'type', 'codec', 'orig_name', 'new_name'), selectmode=BROWSE)
        self.setup_treeview()
        self.treeview.pack(expand=True, fill=BOTH)

    def setup_treeview(self):
        self.treeview.column('#0', width=0, stretch=False)
        self.treeview.column('forced', width=30, stretch=False, anchor=CENTER)
        self.treeview.column('type', width=100, stretch=False, anchor=W)
        self.treeview.column('codec', width=150, stretch=False, anchor=W)
        self.treeview.column('orig_name', width=100, stretch=True, anchor=W)
        self.treeview.column('new_name', width=100, stretch=True, anchor=W)

        self.treeview.heading('forced', text='*', anchor=CENTER)
        self.treeview.heading('type', text='Type', anchor=CENTER)
        self.treeview.heading('codec', text='Codec / Format', anchor=W)
        self.treeview.heading('orig_name', text='Original Name', anchor=W)
        self.treeview.heading('new_name', text='New Name', anchor=W)

    def choose_file(self):
        path = filedialog.askopenfilename(filetypes=[('mkv files', '.mkv')])
        if path:
            self.load_file(path)

    def load_file(self, path):
        self.filename = path
        self.entry_filename.configure(state=NORMAL)
        self.entry_filename.delete(0, END)
        self.entry_filename.insert(0, path)
        self.entry_filename.configure(state=DISABLED)

        self.tracks = self.process_mkv(path)
        self.display_tracks()

    def process_mkv(self, path):
        print(f'Loading: {path}...')
        mkvmerge = get_bundled_path('mkvmerge')
        try:
            results = subprocess.run([mkvmerge, "-J", path], capture_output=True, check=True)
            data = json.loads(results.stdout)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            return []

        processed_tracks = []
        subtitle_counts = {'S_VOBSUB': {}, 'S_TEXT': {}}
        audio_counts = {}

        for track in data.get('tracks', []):
            t_type = track['type']
            if t_type == 'audio':
                track['properties']['new_name'] = self.handle_audio_track(track, audio_counts)
                processed_tracks.append(track)
            elif t_type == 'subtitles':
                track['properties']['new_name'] = self.handle_subtitle_track(track, subtitle_counts)
                processed_tracks.append(track)
        
        return processed_tracks

    def handle_subtitle_track(self, track, counts):
        props = track['properties']
        stype = 'S_VOBSUB' if props.get('codec_id') == 'S_VOBSUB' else 'S_TEXT'
        lang = props.get('language', 'und')
        
        instance = counts[stype].get(lang, 0) + 1
        counts[stype][lang] = instance
        
        name = langcodes.get(lang).display_name()
        if instance > 1:
            name = f'{name} {instance}'
        
        props['default_track'] = False
        return name

    def handle_audio_track(self, track, counts):
        props = track['properties']
        codec = track.get('codec', '')
        channels = props.get('audio_channels', 0)
        orig_name = props.get('track_name', '')
        lang = props.get('language', 'und')

        if 'commentary' in orig_name.lower():
            return orig_name

        chan_str = channels_to_str(channels)
        codec_key = f"{codec}{chan_str}"
        
        if codec_key not in counts:
            counts[codec_key] = {}
        instance = counts[codec_key].get(lang, 0) + 1
        counts[codec_key][lang] = instance

        codec_display = CODEC_ABBREVIATIONS.get(codec, codec)
        name = f"{langcodes.get(lang).display_name()} {codec_display}{chan_str}".strip()
        if instance > 1:
            name = f"{name} {instance}"
        
        return name

    def display_tracks(self):
        self.treeview.delete(*self.treeview.get_children())
        for track in self.tracks:
            t_type = track['type']
            props = track['properties']
            codec = track.get('codec', '')
            orig_name = props.get('track_name', '')
            new_name = props.get('new_name', '')
            
            codec_display = CODEC_ABBREVIATIONS.get(codec, codec)
            if codec == 'AC-3':
                codec_display = 'AC-3'

            if t_type == 'audio':
                flag = '✔︎' if props.get('default_track') else ''
                self.treeview.insert('', END, iid=track['id'], values=(flag, 'Audio', codec_display, orig_name, new_name))
            elif t_type == 'subtitles':
                flag = '✔︎' if props.get('forced_track') else ''
                self.treeview.insert('', END, iid=track['id'], values=(flag, 'Subtitle', codec_display, orig_name, new_name))

    def save_metadata(self):
        if not self.filename:
            return

        args = []
        for track in self.tracks:
            num = track['properties']['number']
            args.extend(['--edit', f'track:@{num}'])
            args.extend(['--set', f'name={track["properties"]["new_name"]}'])
            args.extend(['--set', f'flag-default={int(track["properties"].get("default_track", False))}'])
            
            if track['type'] == 'subtitles':
                args.extend(['--set', f'flag-forced={int(track["properties"].get("forced_track", False))}'])

        print(f'Saving file: {self.filename}...')
        mkvpropedit = get_bundled_path('mkvpropedit')
        try:
            results = subprocess.run([mkvpropedit] + args + [self.filename], capture_output=True, check=True)
            print(results.stdout.decode('ascii'))
        except Exception as e:
            print(f"Error saving metadata: {e}")

if __name__ == "__main__":
    root = Tk()
    app = MKVFixApp(root)
    
    if len(sys.argv) > 1:
        initial_path = sys.argv[1]
        if os.path.exists(initial_path):
            app.load_file(initial_path)
        else:
            print(f"Error: File '{initial_path}' not found.")
            
    root.mainloop()
