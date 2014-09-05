#!/usr/bin/env python
# encoding:utf8

"""
    DragonPy - Dragon 32 emulator in Python
    =======================================

    Some code borrowed from Python IDLE

    :created: 2014 by Jens Diemer - www.jensdiemer.de
    :copyleft: 2014 by the DragonPy team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from __future__ import absolute_import, division, print_function

import os
import string
import sys

from basic_editor.editor_base import BaseExtension
from basic_editor.highlighting import TkTextHighlighting
from dragonlib.utils.auto_shift import invert_shift
from dragonlib.utils.logging_utils import log, pformat_program_dump


try:
    # Python 3
    import tkinter
    from tkinter import filedialog
    from tkinter import messagebox
    from tkinter import scrolledtext
except ImportError:
    # Python 2
    import Tkinter as tkinter
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import ScrolledText as scrolledtext


class MultiStatusBar(tkinter.Frame):
    """
    code from idlelib.MultiStatusBar.MultiStatusBar
    """
    def __init__(self, master, **kw):
        tkinter.Frame.__init__(self, master, **kw)
        self.labels = {}

    def set_label(self, name, text='', side=tkinter.LEFT):
        if name not in self.labels:
            label = tkinter.Label(self, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)
            label.pack(side=side)
            self.labels[name] = label
        else:
            label = self.labels[name]
        label.config(text=text)


class TkTextHighlightCurrentLine(BaseExtension):
    after_id = None
    TAG_CURRENT_LINE = "current_line"
    def __init__(self, editor):
        super(TkTextHighlightCurrentLine, self).__init__(editor)

        self.text.tag_config(self.TAG_CURRENT_LINE, background="#e8f2fe")

        self.current_line = None
        self.__update_interval()

    def update(self, force=False):
        """ highlight the current line """
        line_no = self.text.index(tkinter.INSERT).split('.')[0]

        if not force:
            if line_no == self.current_line:
#                 log.critical("no highlight line needed.")
                return

#         log.critical("highlight line: %s" % line_no)
        self.current_line = line_no

        self.text.tag_remove(self.TAG_CURRENT_LINE, "1.0", "end")
        self.text.tag_add(self.TAG_CURRENT_LINE, "%s.0" % line_no, "%s.0+1lines" % line_no)

    def __update_interval(self):
        """ highlight the current line """
        self.update()
        self.after_id = self.text.after(10, self.__update_interval)


class ScrolledText2(scrolledtext.ScrolledText):
    def save_position(self):
        # save text cursor position:
        self.old_text_pos = self.index(tkinter.INSERT)
        # save scroll position:
        self.old_first, self.old_last = self.yview()

    def restore_position(self):
        # restore text cursor position:
        self.mark_set(tkinter.INSERT, self.old_text_pos)
        # restore scroll position:
        self.yview_moveto(self.old_first)


class EditorWindow(object):
    FILETYPES = [ # For filedialog
        ("BASIC Listings", "*.bas", "TEXT"),
        ("Text files", "*.txt", "TEXT"),
        ("All files", "*"),
    ]
    DEFAULTEXTENSION = "*.bas"

    def __init__(self, cfg, gui=None):
        self.cfg = cfg
        if gui is None:
            self.standalone_run = True
        else:
            self.gui = gui
            self.standalone_run = False

        self.machine_api = self.cfg.machine_api

        if self.standalone_run:
            self.root = tkinter.Tk(className="EDITOR")
        else:
            # As sub window in DragonPy Emulator
            self.root = tkinter.Toplevel(self.gui.root)
            self.root.geometry("+%d+%d" % (
                self.gui.root.winfo_rootx() + self.gui.root.winfo_width(),
                self.gui.root.winfo_y() # FIXME: Different on linux.
            ))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.title("%s - BASIC Editor" % self.cfg.MACHINE_NAME)

        self.text = ScrolledText2(
            master=self.root, height=30, width=80
        )
        self.text.config(
            background="#ffffff", foreground="#000000",
            highlightthickness=0,
            font=('courier', 11),
        )
        self.text.grid(row=0, column=0, sticky=tkinter.NSEW)

        self.highlighting = TkTextHighlighting(self)
        self.highlight_currentline = TkTextHighlightCurrentLine(self)

        #self.auto_shift = True # use invert shift for letters?

        menubar = tkinter.Menu(self.root)

        filemenu = tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load", command=self.command_load_file)
        filemenu.add_command(label="Save", command=self.command_save_file)
        if self.standalone_run:
            filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        if not self.standalone_run: # As sub window in DragonPy Emulator
            editmenu = tkinter.Menu(menubar, tearoff=0)
            editmenu.add_command(label="load from DragonPy", command=self.command_load_from_DragonPy)
            editmenu.add_command(label="inject into DragonPy", command=self.command_inject_into_DragonPy)
            editmenu.add_command(label="inject + RUN into DragonPy", command=self.command_inject_and_run_into_DragonPy)
            menubar.add_cascade(label="DragonPy", menu=editmenu)

        editmenu = tkinter.Menu(menubar, tearoff=0)
        editmenu.add_command(label="renum", command=self.renumber_listing)
        editmenu.add_command(label="display tokens", command=self.debug_display_tokens)
        menubar.add_cascade(label="tools", menu=editmenu)

        # help menu
        helpmenu = tkinter.Menu(menubar, tearoff=0)
#        helpmenu.add_command(label="help", command=self.menu_event_help)
#        helpmenu.add_command(label="about", command=self.menu_event_about)
        menubar.add_cascade(label="help", menu=helpmenu)

        self.set_status_bar() # Create widget, add bindings and after_idle() update

        self.text.bind("<Key>", self.event_text_key)
#         self.text.bind("<space>", self.event_syntax_check)

        # display the menu
        self.root.config(menu=menubar)
        self.root.update()

    ###########################################################################
    # Status bar

    def set_status_bar(self):
        self.status_bar = MultiStatusBar(self.root)
        if sys.platform == "darwin":
            # Insert some padding to avoid obscuring some of the statusbar
            # by the resize widget.
            self.status_bar.set_label('_padding1', '    ', side=tkinter.RIGHT)
        self.status_bar.grid(row=1, column=0)

        self.text.bind("<<set-line-and-column>>", self.set_line_and_column)
        self.text.event_add("<<set-line-and-column>>",
                            "<KeyRelease>", "<ButtonRelease>")
        self.text.after_idle(self.set_line_and_column)

    def set_line_and_column(self, event=None):
        line, column = self.text.index(tkinter.INSERT).split('.')
        self.status_bar.set_label('column', 'Column: %s' % column)
        self.status_bar.set_label('line', 'Line: %s' % line)

    ###########################################################################

    def event_text_key(self, event):
        """
        So a "invert shift" for user inputs:
        Convert all lowercase letters to uppercase and vice versa.
        """
        char = event.char
        if not char or char not in string.ascii_letters:
            # ignore all non letter inputs
            return

        converted_char = invert_shift(char)
        log.debug("convert keycode %s - char %s to %s", event.keycode, repr(char), converted_char)
#         self.text.delete(Tkinter.INSERT + "-1c") # Delete last input char
        self.text.insert(tkinter.INSERT, converted_char) # Insert converted char
        return "break"

#     def event_syntax_check(self, event):
#         index = self.text.search(r'\s', "insert", backwards=True, regexp=True)
#         if index == "":
#             index ="1.0"
#         else:
#             index = self.text.index("%s+1c" % index)
#         word = self.text.get(index, "insert")
#         log.critical("inserted word: %r", word)
#         print self.machine_api.parse_ascii_listing(word)

    def command_load_file(self):
        infile = filedialog.askopenfile(
            parent=self.root,
            mode="r",
            title="Select a BASIC file to load",
            filetypes=self.FILETYPES,
        )
        if infile is not None:
            content = infile.read()
            infile.close()
            content = content.strip()
            listing_ascii = content.splitlines()
            self.set_content(listing_ascii)

    def command_save_file(self):
        outfile = filedialog.asksaveasfile(
            parent=self.root,
            mode="w",
            filetypes=self.FILETYPES,
            defaultextension=self.DEFAULTEXTENSION,
        )
        if outfile is not None:
            content = self.get_content()
            outfile.write(content)
            outfile.close()

    ###########################################################################
    # For DragonPy Emulator:

    def command_load_from_DragonPy(self):
        self.gui.add_user_input_and_wait("'SAVE TO EDITOR")
        listing_ascii = self.gui.machine.get_basic_program()
        self.set_content(listing_ascii)
        self.gui.add_user_input_and_wait("\r")

    def command_inject_into_DragonPy(self):
        self.gui.add_user_input_and_wait("'LOAD FROM EDITOR")
        content = self.get_content()
        result = self.gui.machine.inject_basic_program(content)
        log.critical("program loaded: %s", result)
        self.gui.add_user_input_and_wait("\r")

    def command_inject_and_run_into_DragonPy(self):
        self.command_inject_into_DragonPy()
        self.gui.add_user_input_and_wait("\r") # FIXME: Sometimes this input will be "ignored"
        self.gui.add_user_input_and_wait("RUN\r")

    ###########################################################################

    def debug_display_tokens(self):
        content = self.get_content()
        program_dump = self.machine_api.ascii_listing2program_dump(content)
        msg = pformat_program_dump(program_dump)
        messagebox.showinfo("Program Dump:", msg, parent=self.root)

    def renumber_listing(self):
        # save text cursor and scroll position
        self.text.save_position()

        # renumer the content
        content = self.get_content()
        content = self.machine_api.renum_ascii_listing(content)
        self.set_content(content)

        # restore text cursor and scroll position
        self.text.restore_position()

    def get_content(self):
        content = self.text.get("1.0", tkinter.END)
        content = content.strip()
        return content

    def set_content(self, listing_ascii):
#        self.text.config(state=Tkinter.NORMAL)
        self.text.delete("1.0", tkinter.END)
        log.critical("insert listing:")
        if isinstance(listing_ascii, str):
            listing_ascii = listing_ascii.splitlines()

        for line in listing_ascii:
            line = "%s\n" % line # use os.sep ?!?
            log.critical("\t%s", repr(line))
            self.text.insert(tkinter.END, line)
#        self.text.config(state=Tkinter.DISABLED)
        self.text.mark_set(tkinter.INSERT, '1.0') # Set cursor at start
        self.text.focus()
        self.highlight_currentline.update(force=True)
        self.highlighting.update(force=True)

    def mainloop(self):
        """ for standalone usage """
        self.root.mainloop()


def run_basic_editor(cfg, default_content=None):
    editor = EditorWindow(cfg)
    if default_content is not None:
        editor.set_content(default_content)
    editor.mainloop()


def test():
    CFG_DICT = {
        "verbosity": None,
        "display_cycle": False,
        "trace": None,
        "max_ops": None,
        "bus_socket_host": None,
        "bus_socket_port": None,
        "ram": None,
        "rom": None,
        "use_bus": False,
    }
    from dragonpy.Dragon32.config import Dragon32Cfg
    cfg = Dragon32Cfg(CFG_DICT)



    filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)),
        "..", "BASIC examples",
        "hex_view01.bas"
    )

    with open(filepath, "r") as f:
        listing_ascii = f.read()

    run_basic_editor(cfg, default_content=listing_ascii)


if __name__ == "__main__":
    test()
