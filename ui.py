import sys

from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog

filename = ''


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


def test():
    txt_output.write("Some line of output...\n")


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

btn_process = Button(frame_bottom, text='Process', command=test)
btn_process.pack(side=RIGHT)

sys.stdout = txt_output
sys.stderr = txt_output

root.mainloop()
