#!/usr/bin/env python

# Standard library imports
import sys
import os
# Disable system version compatibility mode on macOS to prevent warnings
if sys.platform == 'darwin':
    os.environ['SYSTEM_VERSION_COMPAT'] = '0'

import subprocess
import json
import langcodes  # For language code to display name conversion
import re

# Tkinter imports for GUI
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

# Global variables to store selected file and track information
filename = ''
tracks = []

# predefined audio track names
audio_track_names = ["Director's Commentary", "Commentary", "Isolated Score"]

# codec abbreviations
codec_abbreviations = {"DTS-HD Master Audio": "DTS-HD MA"}


def get_bundled_path(tool_name):
    """
    Retrieves the absolute path to a bundled MKVToolNix binary.

    Falls back to the system's Homebrew installation path if not running within
    a PyInstaller bundle.

    Args:
        tool_name (str): The name of the binary to locate (e.g., 'mkvmerge', 'mkvpropedit').

    Returns:
        str: The full path to the binary.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = sys._MEIPASS
        bundled_path = os.path.join(bundle_dir, 'bin', tool_name)
        if os.path.exists(bundled_path):
            return bundled_path
    # Fall back to homebrew path
    return f'/opt/homebrew/bin/{tool_name}'


def process(filename):
    """
    Analyzes an MKV file to identify tracks and generates standardized names.

    Args:
        filename (str): The full path to the MKV file to process.

    Returns:
        list[dict]: A list of track dictionaries, each containing properties and a 'new_name' field.
    """
    # Track counters for subtitle types (VOBSUB vs text-based)
    S_VOBSUB = {}
    S_TEXT = {}

    # Track counter for audio tracks by codec type and channel configuration
    audio_track_type_count = {}

    def load(filename):
        """
        Loads MKV file metadata as JSON using 'mkvmerge -J'.

        Args:
            filename (str): The path to the MKV file to load.

        Returns:
            dict: The JSON-parsed metadata from mkvmerge.
        """
        print(f'Loading: {filename}...')
        mkvmerge = get_bundled_path('mkvmerge')
        # Use -J flag to get JSON output of file structure
        results = subprocess.run([mkvmerge, "-J", f'{filename}'], capture_output=True)
        data = json.loads(results.stdout)

        return data

    def get_prop(props, item, default=""):
        """
        Safely retrieves a property from a dictionary with a default fallback.

        Args:
            props (dict): The dictionary containing properties.
            item (str): The key to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The property value or the default fallback.
        """
        return props[item] if item in props else default

    def channels_to_str(channels):
        """
        Converts a channel count integer into a human-readable string.

        Args:
            channels (int): The number of audio channels.

        Returns:
            str: A formatted string like " Mono", " Stereo", " 5.1", or an empty string for < 1.
        """
        if channels < 1:
            return ''

        elif channels == 1:
            return ' Mono'

        elif channels == 2:
            return ' Stereo'

        else:
            # Format as X.1 surround (e.g., 5.1, 7.1)
            return f' {channels - 1}.1'

    def handle_subtitle_track(track):
        """
        Generates a standardized name for a subtitle track based on its language and codec.

        Initializes counters for different subtitle types (VOBSUB vs text) and
        increments instance counts per language to handle multiple tracks.

        Args:
            track (dict): The subtitle track dictionary from mkvmerge.

        Returns:
            str: The generated track name (e.g., "English", "English 2").
        """
        props = track['properties']
        track_id = props['number']

        # Determine subtitle type (VOBSUB image-based vs text-based)
        if props['codec_id'] == 'S_VOBSUB':
            subtitle_tracks = S_VOBSUB
        else:
            subtitle_tracks = S_TEXT

        # Generate track name with language and instance count
        lng = props['language']
        instances = subtitle_tracks[lng] + 1 if lng in subtitle_tracks else 1
        subtitle_tracks[lng] = instances
        name = langcodes.get(lng).display_name()
        # Add instance number if there are multiple tracks of same language
        if instances > 1:
            name = f'{name} {instances}'

        # Set default_track to False
        props['default_track'] = False

        return name


    def handle_audio_track(track):
        """
        Generates a standardized name for an audio track based on its metadata.

        Extracts language, codec, and channel configuration to build a uniform
        name. Tracks with "commentary" in their name are left as-is.

        Args:
            track (dict): The audio track dictionary from mkvmerge.

        Returns:
            str: The generated track name (e.g., "English DTS-HD MA 5.1").
        """
        props = track['properties']
        codec = track["codec"]
        channels = props['audio_channels']
        original_name = props['track_name'] if 'track_name' in props else ''

        # Preserve tracks with "commentary" in the name unchanged
        if 'commentary' in original_name.lower():
            return original_name

        # Build standardized name from language, codec, and channel configuration
        lng = props['language']
        channel_str = channels_to_str(channels)

        # Create unique key for tracking instances (codec + channels, e.g., "AC3 Stereo")
        codec_name = codec + channel_str

        # Get or create counter dict for this codec+channel combination
        if codec_name in audio_track_type_count:
            audio_tracks = audio_track_type_count[codec_name]
        else:
            audio_tracks = audio_track_type_count[codec_name] = {}

        # Track instance count for each language
        instances = audio_tracks[lng] + 1 if lng in audio_tracks else 1
        audio_tracks[lng] = instances

        # Use abbreviated name for codec if available
        codec_display = codec_abbreviations.get(codec, codec)

        # Format: "Language Codec Channels [Instance#]"
        name = langcodes.get(lng).display_name() + ' ' + codec_display + channel_str
        if instances > 1:
            name = f'{name} {instances}'

        return name


    if not filename:
        return

    # Load MKV file metadata
    data = load(filename)

    tracks = []

    # Process each track in the file
    for track in data['tracks']:
        track_type = track['type']

        # Generate standardized name for audio tracks
        if track_type == 'audio':
            track['properties']['new_name'] = handle_audio_track(track)
            tracks.append(track)

        # Generate standardized name for subtitle tracks
        elif track_type == 'subtitles':
            track['properties']['new_name'] = handle_subtitle_track(track)
            tracks.append(track)

    return tracks


def choose_file():
    """
    Opens a file dialog, processes the selected MKV, and refreshes the UI.

    Updates the global filename and tracks variables, then populates the track list.
    """
    global entry_filename, filename, tracks

    # Show file picker dialog for MKV files
    filename = filedialog.askopenfilename(filetypes=[('mkv files', '.mkv')])

    if filename:
        # Update filename entry field
        entry_filename.configure(state=ACTIVE)
        entry_filename.delete(0, END)
        entry_filename.insert(0, filename)
        entry_filename.configure(state=DISABLED)

        # Process file and display tracks in UI
        tracks = process(filename)
        display_tracks(tracks)


def display_tracks(tracks):
    """
    Populates the Treeview widget with track information from the provided list.

    Args:
        tracks (list[dict]): A list of track data to display.
    """
    global treeview_tracks

    # Clear any existing data from previous file
    treeview_tracks.delete(*treeview_tracks.get_children())

    # Populate treeview with track data
    for track in tracks:
        track_type = track['type']
        props = track['properties']

        codec_id = track['codec']
        name = props['track_name'] if 'track_name' in props else ''
        new_name = props['new_name'] if 'new_name' in props else ''

        codec_display = codec_abbreviations.get(codec_id, codec_id)

        # Display audio tracks with default_track checkbox
        if track_type == 'audio':
            default = '✔︎' if props['default_track'] else ''
            treeview_tracks.insert(parent='', iid=track['id'], index=END, text='', values=(default, 'Audio', codec_display, name, new_name))

        # Display subtitle tracks with forced_track checkbox
        elif track_type == 'subtitles':
            default = '✔︎' if props['forced_track'] else ''
            treeview_tracks.insert(parent='', iid=track['id'], index=END, text='', values=(default, 'Subtitle', codec_display, name, new_name))


def save(filename, tracks):
    """
    Saves metadata changes back to the MKV file using 'mkvpropedit'.

    Args:
        filename (str): The path to the MKV file to modify.
        tracks (list[dict]): The list of tracks with updated properties.
    """
    args = []

    # Build mkvpropedit command arguments for each track
    for track in tracks:
        props = track['properties']
        args.extend(['--edit', f'track:@{props["number"]}'])

        # Set audio track properties (name, default flag)
        if track['type'] == 'audio':
            args.extend(['--set', f'name={props["new_name"]}'])
            args.extend(['--set', f'flag-default={props["default_track"]}'])

        # Set subtitle track properties (name, default flag, forced flag)
        elif track['type'] == 'subtitles':
            args.extend(['--set', f'name={props["new_name"]}'])
            args.extend(['--set', f'flag-default={props["default_track"]}'])
            args.extend(['--set', f'flag-forced={props["forced_track"]}'])

    # Execute mkvpropedit to update file metadata
    print(f'Saving file: {filename}...')
    mkvpropedit = get_bundled_path('mkvpropedit')
    results = subprocess.run([mkvpropedit] + args + [filename], capture_output=True)
    print(results.stdout.decode('ascii'))

    return


class ConsoleText(Text):
    """
    A specialized Text widget for console-like output.

    The ConsoleText class is designed to emulate a console by serving as a
    read-only widget with functions to append messages and automatically
    scroll to the bottom. This is beneficial for applications needing
    logging or status updates within a GUI.
    """

    def __init__(self, master, **kwargs):
        """
        Initializes a ConsoleText instance with default configurations.

        Args:
            master (Tk): The parent widget for this ConsoleText instance.
            kwargs: Additional keyword arguments for Text widget configuration.
        """
        super().__init__(master, **kwargs)
        self.configure(state=DISABLED)

    def write(self, message):
        """
        Writes a message to the text widget while ensuring it remains non-editable
        and auto-scrolls to the most recent entry.

        Args:
            message (str): The message to be inserted into the text widget.
        """
        self.configure(state=NORMAL)
        self.insert(END, message)
        self.configure(state=DISABLED)
        self.yview(END)


class TrackView(Treeview):
    """
    Custom Treeview widget for displaying and editing track information.

    Supports single-click to toggle default/forced flags and double-click to edit track names.
    """

    def __init__(self, master, **kwargs):
        """Initialize TrackView with event bindings."""
        super().__init__(master, **kwargs)
        self.bind('<Double-Button-1>', self.on_double_click)
        self.bind('<Button-1>', self.on_click)

    def on_click(self, event):
        """
        Handles single-click events to toggle default/forced track flags.

        Args:
            event: Click event containing position information
        """
        global tracks

        region = self.identify_region(event.x, event.y)
        if region == 'cell':
            entry_iid = self.identify_row(event.y)
            row = int(entry_iid) - 1
            col = int(self.identify_column(event.x)[1:]) - 1

            # Column 0 toggles default (audio) or forced (subtitles) flag
            if col == 0:
                track = tracks[row]

                # Toggle default flag for audio tracks
                if track['type'] == 'audio':
                    track['properties']['default_track'] = False if track['properties']['default_track'] else True

                # Toggle forced flag for subtitle tracks
                if track['type'] == 'subtitles':
                    # Initialize forced_track property if missing
                    if 'forced_track' not in track['properties']:
                        track['properties'].forced_track = False

                    track['properties']['forced_track'] = False if track['properties']['forced_track'] else True

                # Update visual checkbox in treeview
                values = self.item(entry_iid).get('values')
                values[0] = '✔︎' if values[0] == '' else ''
                self.item(entry_iid, values=values)


    def on_double_click(self, event):
        """
        Handles double-click events to enable inline editing of track names.

        Args:
            event: Click event containing position information
        """
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

            # Only allow editing column 4 (new_name)
            if col_index == 4:
                track = tracks[row_index]
                if track['type'] == 'subtitles':
                    # Create inline ttk.Entry widget for subtitles
                    overlay = Entry(self)
                    overlay.insert(0, value)
                else:
                    # Create inline ttk.Combobox widget for other tracks (e.g. audio)
                    overlay = Combobox(self, values=audio_track_names)
                    overlay.set(value)

                overlay.selection_range(0, END)
                overlay.focus()

                # Bind events to save on focus loss or Enter key
                overlay.bind('<FocusOut>', self.save_value)
                overlay.bind('<Return>', self.save_value)

                # Store target location for save operation
                overlay.target_iid = row
                overlay.target_col = col_index
                overlay.target_row = row_index

                # Position overlay on top of cell
                overlay.place(x=x, y=y, width=w, height=h)

                # Store active overlay and bind global click tracker to save when clicking outside
                self.active_overlay = overlay
                self.root_click_id = self.winfo_toplevel().bind_all('<Button-1>', self.check_save_on_click, add="+")

    def check_save_on_click(self, event):
        """Checks if a click occurred outside the active editor and saves if so."""
        if not hasattr(self, 'active_overlay') or not self.active_overlay or not self.active_overlay.winfo_exists():
            return

        w = event.widget
        # Check if click is inside the overlay or its children
        if w == self.active_overlay or str(w).startswith(str(self.active_overlay) + "."):
            return

        # Check for combobox popdown
        try:
            popdown = self.active_overlay.tk.call('ttk::combobox::PopdownWindow', str(self.active_overlay))
            if w == popdown or str(w).startswith(str(popdown) + "."):
                return
        except:
            pass

        # If we reach here, the click was outside. Save and close.
        self.save_value(event)

    def save_value(self, event):
        """
        Saves edited track name value back to data structure and UI.

        Args:
            event: Event from Entry widget containing edited value
        """
        global tracks
        
        # Use active_overlay if available, otherwise use event.widget
        widget = getattr(self, 'active_overlay', None)
        if not widget:
            widget = event.widget
            
        if not widget or not widget.winfo_exists():
            return

        # Get edited value and target location
        value = widget.get()
        iid = widget.target_iid
        col = widget.target_col
        row = widget.target_row

        # Update treeview display
        values = self.item(iid).get('values')
        values[col] = value
        self.item(iid, values=values)

        # Update underlying data structure
        tracks[row]['properties']['new_name'] = value

        # Remove overlay widget
        widget.destroy()
        self.active_overlay = None

        # Unbind global click tracker
        if hasattr(self, 'root_click_id'):
            self.winfo_toplevel().unbind_all('<Button-1>')
            del self.root_click_id


# ==============================================================================
# UI Setup and Event Loop
# ==============================================================================

# Create root window
root = Tk()
root.title('MKV Tool')
root.minsize(800, 475)
root.geometry('800x475+350+150')
root.config(bg='lightgrey')
root.resizable(True, True)

# Configure visual theme and styles
style = Style(root)
style.theme_use('classic')
style.configure('TFrame', background='lightgrey')
style.configure('TLabel', font=('TkDefaultFont', 12))
style.configure('TButton', font=('TkDefaultFont', 12), background='#007bff', foreground='white', highlightthickness=0)
style.map('TButton', background=[('active', '#0056b3')], highlightbackground=[('active', '#0056b3')])
style.configure('Treeview', font=('TkDefaultFont', 10), rowheight=20)
style.configure('Treeview.Heading', font=('TkDefaultFont', 12, 'bold'))
style.configure('TEntry', font=('TkDefaultFont', 11), insertcolor='black')
style.map('TEntry', foreground=[('disabled', 'black')], insertcolor=[('focus', 'black')])
style.configure('TCombobox', font=('TkDefaultFont', 11), insertcolor='black')
style.map('TCombobox', insertcolor=[('focus', 'black')])

# Create layout frames
frame_top = Frame(root)
frame_top.pack(expand=False, anchor=N, fill=X, padx=3, pady=3)

frame_bottom = Frame(root)
frame_bottom.pack(expand=False, anchor=S, fill=X, padx=3, pady=3, side=BOTTOM)

# Center paned window with resizable sections
frame_center = Panedwindow(root, orient=VERTICAL)
frame_center.pack(expand=True, fill=BOTH)

# Console log frame
frame_log = Frame(frame_center, borderwidth=5, relief=RIDGE)
frame_center.add(frame_log)

# Track list frame
frame_tracks = Frame(frame_center, borderwidth=2, relief=RIDGE)
frame_center.add(frame_tracks)

# File selector widgets
file_label = Label(frame_top, text='Target file:')
file_label.pack(side=LEFT)

entry_filename = Entry(frame_top)
entry_filename.insert(0, 'Select a file...')
entry_filename.configure(state=DISABLED)
entry_filename.pack(expand=True, side=LEFT, fill=X)

btn_choose = Button(frame_top, text='Choose', command=choose_file)
btn_choose.pack(side=RIGHT)

# Console output widget for status messages
txt_output = ConsoleText(frame_log, font="Courier 14", height=8, bg='white', fg='black', borderwidth=0, highlightthickness=0)
txt_output.pack(expand=True, fill=BOTH)

# Tracks treeview with columns for track information
treeview_tracks = TrackView(frame_tracks, columns=('forced', 'type', 'codec', 'orig_name', 'new_name'), selectmode=BROWSE)

# Configure treeview columns
treeview_tracks.column('#0', width=0, stretch=False)
treeview_tracks.column('forced', width=30, stretch=False, anchor=CENTER)
treeview_tracks.column('type', width=100, stretch=False, anchor=W)
treeview_tracks.column('codec', width=150, stretch=False, anchor=W)
treeview_tracks.column('orig_name', width=100, stretch=True, anchor=W)
treeview_tracks.column('new_name', width=100, stretch=True, anchor=W)

# Configure treeview column headings
treeview_tracks.heading('#0', text='?', anchor=W)
treeview_tracks.heading('forced', text='*', anchor=CENTER)
treeview_tracks.heading('type', text='Type', anchor=CENTER)
treeview_tracks.heading('codec', text='Codec / Format', anchor=W)
treeview_tracks.heading('orig_name', text='Original Name', anchor=W)
treeview_tracks.heading('new_name', text='New Name', anchor=W)

treeview_tracks.pack(expand=True, fill=BOTH)

# Update button to save changes
btn_process = Button(frame_bottom, text='Update', command=lambda: save(filename, tracks))
btn_process.pack(side=RIGHT)

# Redirect stdout/stderr to console widget
sys.stdout = txt_output
sys.stderr = txt_output

# Start GUI event loop
root.mainloop()
