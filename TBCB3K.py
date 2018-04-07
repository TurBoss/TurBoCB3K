#!/usr/bin/env python

import os
import sys
import traceback

import logging

from tkinter import Tk, Frame, Button, Label, PhotoImage, Text, END
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror

from jinja2 import FileSystemLoader

from latex import build_pdf
from latex.jinja2 import make_env

log = logging.getLogger("TBCB3K")
log.setLevel(logging.DEBUG)

# Add console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

log.addHandler(ch)


class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(END, f"{msg}\r\n")
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class TurBoCB3K:

    def __init__(self):

        self.log = log

        self.pdf = None
        self.tpl = None

        self.tex_path = None
        self.dir_path = None
        self.bg_path = None
        self.title_path = None

        self.root_path = None
        self.root_name = None
        self.file_tree = None

        self.models = dict()

        self.tile_format = None

        self.square = 0.20
        self.rectangular = 0.30

    def scan(self):

        self.root_path = self.dir_path
        self.root_name = os.path.basename(self.root_path)

        self.file_tree = os.walk(self.root_path, topdown=False)

        self.log.debug(self.root_name)
        self.models[self.root_name] = dict()

        self.log.debug(f'{self.title_path}\n{self.bg_path}')

        for dirName, subdirList, fileList in self.file_tree:

            model = os.path.basename(dirName)

            if model != self.root_name:

                self.log.debug(f" ")
                self.log.debug(f"Model = {model}")

                tile_format = model.rsplit('_')[1]
                size = tile_format.rsplit("x")

                self.log.debug(size)

                if size[0] == size[1]:
                    self.tile_format = self.square
                elif size[0] != size[1]:
                    self.tile_format = self.rectangular

                model = self.scape_string(model)

                self.models[self.root_name][model] = dict()

                self.log.debug(f"\t{model}")

                for fname in fileList:
                    picture_kind = None
                    if fname.endswith("M.png"):
                        picture_kind = "montage"
                    elif fname.endswith(".png"):
                        picture_kind = "model"

                    self.log.debug(f'\t\t{fname} {picture_kind} {self.tile_format}')

                    self.models[self.root_name][model][picture_kind] = os.path.join(dirName, fname).replace("\\", "/")
                    self.models[self.root_name][model]["size"] = self.tile_format

        # self.log.debug(self.models[self.root_name])

    def create_pdf(self, path):

        bg_image = self.bg_path.replace("\\", "/")
        logo = self.title_path.replace("\\", "/")

        models = sorted(self.models[self.root_name].items())

        env = make_env(loader=FileSystemLoader(os.path.dirname(self.tex_path)))
        self.tpl = env.get_template(os.path.basename(self.tex_path))

        self.pdf = build_pdf(
            self.tpl.render(logo=logo,
                            bg_image=bg_image,
                            models=models)
        )

        self.pdf.save_to(path)

    @staticmethod
    def scape_string(string):

        escaped = string.translate(str.maketrans({"_": r"-"}))
        return escaped


class Application(Frame):

    def __init__(self, guest=None, master=None):

        super().__init__(master)

        self.guest = guest
        self.master = master

        self.master.title("TurBoCB3K")
        self.master.geometry("800x600")
        self.master.resizable(0, 0)
        self.master.report_callback_exception = self.excepthook

        self.text_log = Text(self.master, height=60, width=80)
        self.text_log.configure(state='disabled')

        self.text_logger = TextHandler(self.text_log)
        self.log = logging.getLogger()
        self.log.addHandler(self.text_logger)

        self.pack(fill="both", expand=True)

        self.path = None

        # self.image = PhotoImage(file="images/cat.png")

        # self.image_label = Label(image=self.image)

        self.tex_path_label = Label(self, text="None")
        self.dir_path_label = Label(self, text="None")
        self.bg_path_label = Label(self, text="None")
        self.title_path_label = Label(self, text="None")

        self.open_tex_button = Button(self,
                                      text="Open Latex",
                                      width="50",
                                      command=self.load_tex)

        self.open_title_button = Button(self,
                                        text="Open Title",
                                        width="50",
                                        command=self.load_title)

        self.open_bg_button = Button(self,
                                     text="Open Background",
                                     width="50",
                                     command=self.load_bg)

        self.open_dir_button = Button(self,
                                      text="Open Directory",
                                      width="50",
                                      command=self.load_dir)

        self.run_button = Button(self,
                                 text="Build PDF",
                                 width="50",
                                 fg="green",
                                 state="disabled",
                                 command=self.gen_pdf)

        self.quit_button = Button(self,
                                  text="Quit",
                                  width="50",
                                  fg="red",
                                  command=self.master.destroy)

        self.open_tex_button.pack()
        self.tex_path_label.pack()

        self.open_title_button.pack()
        self.title_path_label.pack()

        self.open_bg_button.pack()
        self.bg_path_label.pack()

        self.open_dir_button.pack()
        self.dir_path_label.pack()

        self.run_button.pack()
        self.quit_button.pack()

        # self.image_label.pack()

        self.text_log.pack()

    def load_tex(self):
        self.load("tex")

    def load_title(self):
        self.load("title")

    def load_bg(self):
        self.load("bg")

    def load_dir(self):
        self.load("dir")

    def load(self, thing):

        if thing == "tex":
            path = askopenfilename(filetypes=(("latex files", "*.tex"), ("all files", "*.*")))
            if path != "":
                self.guest.tex_path = path
                self.tex_path_label["text"] = path
            else:
                self.guest.tex_path = None
                self.tex_path_label["text"] = "None"

        if thing == "title":
            path = askopenfilename(filetypes=(("png images", "*.png"), ("all files", "*.*")))
            if path != "":
                self.guest.title_path = path
                self.title_path_label["text"] = path
            else:
                self.guest.title_path = None
                self.title_path_label["text"] = "None"

        if thing == "bg":
            path = askopenfilename(filetypes=(("png files", "*.png"), ("all files", "*.*")))
            if path != "":
                self.guest.bg_path = path
                self.bg_path_label["text"] = path
            else:
                self.guest.bg_path = None
                self.bg_path_label["text"] = "None"

        elif thing == "dir":
            path = askdirectory()
            if path != tuple():
                self.guest.dir_path = path
                self.dir_path_label["text"] = path
            else:
                self.guest.dir_path = None
                self.dir_path_label["text"] = "None"

        if self.guest.tex_path and self.guest.title_path and self.guest.bg_path and self.guest.dir_path:
            self.guest.scan()
            self.run_button["state"] = "normal"
        else:
            self.run_button["state"] = "disabled"

    def gen_pdf(self):
        path = asksaveasfilename(defaultextension=".pdf", filetypes=(("PDF files", "*.pdf"),("All Files", "*.*")))
        self.guest.create_pdf(path)

    @staticmethod
    def excepthook(exc_type, exc_value, exc_traceback):
        message = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msg = "".join(message)
        log.error(msg)
        showerror(title="Troll error", message="Total Troll ERROR:\n NO VAS!")


def main():
    root = Tk()
    app_tcb = TurBoCB3K()

    app = Application(app_tcb, master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
