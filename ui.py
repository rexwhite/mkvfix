import sys

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

filename = ''


def choose_file():
    global filename, entry_filename
    filename = filedialog.askopenfilename()
    if filename:
        entry_filename.configure(state=ACTIVE)
        entry_filename.delete(0, END)
        entry_filename.insert(0, filename)
        entry_filename.configure(state=DISABLED)


class ConsoleText(Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

    def write(self, message):
        self.configure(state=NORMAL)
        self.insert(END, message)
        self.configure(state=DISABLED)
        self.yview(END)


def test():
    txt_output.write("Some line of output...\n")


# root window
root = Tk()
root.title('MKV Tool')
root.minsize(800, 450)
root.geometry('1000x600+350+150')
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
treeview_tracks = Treeview(frame_tracks)
treeview_tracks.pack(expand=True, fill=BOTH)

# Process button
btn_process = Button(frame_bottom, text='Process', command=test)
btn_process.pack(side=RIGHT)

sys.stdout = txt_output
sys.stderr = txt_output

root.mainloop()
