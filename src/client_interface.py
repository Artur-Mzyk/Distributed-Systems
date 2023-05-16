#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import time
import tkinter as tk
import tkinter.ttk as ttk

from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from typing import Optional, List

# PROJECT PACKAGES
from config import *
from communication import send
from client import Client
from artificial_client import ArtificialClient


# CLASSES
class MainApp(tk.Tk):
    """
    Class to represent the client interface
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor
        """

        # Main window
        tk.Tk.__init__(self, *args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.bind("<Escape>", lambda event: self.quit())
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.title(TITLE)

        # Client socket
        self.client = Client()
        self.artificial_client = ArtificialClient()

        # Main frame
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Lobby window frame
        frame = Window(container, self)
        frame.pack()
        frame.tkraise()


class Window(tk.Frame):
    """
    Class to represent the lobby window
    """

    def __init__(self, parent: ttk.Frame, root: MainApp) -> None:
        """
        Constructor
        :param parent: Parent frame
        :param root: Root
        """

        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.root = root

        self.grid_rowconfigure(1)
        self.grid_columnconfigure(1, weight=1)

        self.tabs = ttk.Notebook(self.parent)
        self.tabs.pack()

        self.lobby_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.lobby_tab, text="Lobby")
        self.localization_entries = [ttk.Entry(self.lobby_tab) for _ in range(2)]

        for i, entry in enumerate(self.localization_entries):
            entry.grid(row=0, column=i, padx=5)

        self.localization_button = ttk.Button(self.lobby_tab, text="Enter localization", command=self.join)
        self.localization_button.grid(row=0, column=2)
        self.localization = None

        self.localization_warning_label = tk.StringVar(value="")
        tk.Label(self.lobby_tab, textvariable=self.localization_warning_label, font=("Garamond", 16, "bold")).grid(row=1, column=0, columnspan=3)

        self.chat_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.chat_tab, text="Chat")

        self.chat_area = ScrolledText(self.chat_tab, width=70, height=22, font=("Garamond", 12))
        self.chat_area.grid(row=0, column=0, columnspan=4, padx=10, pady=(30, 10))

        self.chat_entry = ttk.Entry(self.chat_tab, width=70)
        self.chat_entry.grid(row=1, column=0, columnspan=3, pady=(0, 30))

        ttk.Button(self.chat_tab, text="Send", command=self.send_message).grid(row=1, column=3, pady=(0, 30))

        self.name_label_text = tk.StringVar(value="")
        tk.Label(self.chat_tab, textvariable=self.name_label_text, font=("Garamond", 16, "bold")).grid(row=2, column=0)

        self.tabs.hide(1)

        Thread(target=self.receive_messages).start()
        Thread(target=self.artificial_receive_messages).start()

    def join(self) -> None:
        self.localization_button["state"] = "disabled"
        self.localization = f"({self.localization_entries[0].get()}, {self.localization_entries[1].get()})"
        self.root.client.send_message(msg=f"[LOC] {self.localization}")
        self.tabs.hide(0)
        self.tabs.select(1)
        self.name_label_text.set(f"Your localization: {self.localization}")

    def send_message(self, msg: Optional[str] = None) -> None:
        """
        Method to send the message
        :param msg: Message
        """

        if msg is None:
            msg = f"{self.localization}: {self.chat_entry.get()}\n"

        else:
            msg = self.chat_entry.get()

        self.root.client.send_message(msg)
        self.chat_entry.delete('0', 'end')

    def receive_messages(self) -> None:
        """
        Method to receive messages
        """

        while True:
            messages = self.root.client.receive_messages()

            if messages == "Not connected":
                self.localization_button["state"] = "normal"
                self.tabs.select(0)
                self.tabs.hide(1)
                self.localization_warning_label.set("Improper")

            else:
                self.chat_area.delete('1.0', 'end')

                for msg in messages:
                    self.chat_area.insert('end', msg)

    def artificial_receive_messages(self) -> None:
        """
        Method to receive messages
        """

        while True:
            messages = self.root.artificial_client.receive_messages()

            if messages == "Not connected":
                self.localization_button["state"] = "normal"
                self.tabs.select(0)
                self.tabs.hide(1)
                self.localization_warning_label.set("Improper")

            else:
                self.chat_area.delete('1.0', 'end')

                for msg in messages:
                    self.chat_area.insert('end', msg)


client_app = MainApp()
client_app.mainloop()