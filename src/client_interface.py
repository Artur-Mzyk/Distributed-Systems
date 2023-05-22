#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import time
import tkinter as tk
import tkinter.ttk as ttk
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
from typing import List, Dict

from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from typing import Optional, List
from sqlalchemy import create_engine
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# PROJECT PACKAGES
from config import *
from communication import send
from client import Client
from database.database_architecture import create_architecture
from database.database_upload import upload_data
from database.database_queries import DatabaseQueries


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

        # Main frame
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Lobby window frame
        frame = Window(container, self)
        frame.pack()
        frame.tkraise()


def make_signal_noise(localizations: List[Dict], min_noise_val: int, max_noise_val: int) -> List[Dict]:
    for localization in localizations:
        localization['x_localization'] = localization['x_localization'] + random.randint(min_noise_val, max_noise_val)
        localization['y_localization'] = localization['y_localization'] + random.randint(min_noise_val, max_noise_val)
    return localizations


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
        _ = [entry.grid(row=0, column=i, padx=5) for i, entry in enumerate(self.localization_entries)]

        self.localization_button = ttk.Button(self.lobby_tab, text="Enter localization", command=self.join)
        self.localization_button.grid(row=0, column=2)
        self.localization = None

        self.localization_warning_label = tk.StringVar(value="")
        tk.Label(self.lobby_tab, textvariable=self.localization_warning_label, font=("Garamond", 16, "bold")).grid(row=1, column=0, columnspan=3)

        self.logs_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.logs_tab, text="Logs")

        self.logs_area = ScrolledText(self.logs_tab, width=70, height=22, font=("Garamond", 12))
        self.logs_area.grid(row=0, column=0, columnspan=4, padx=10, pady=(30, 10))

        self.name_label_text = tk.StringVar(value="")
        tk.Label(self.logs_tab, textvariable=self.name_label_text, font=("Garamond", 16, "bold")).grid(row=2, column=0)

        self.map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.map_tab, text="Map")

        self.tabs.hide(1)
        self.tabs.hide(2)

        Thread(target=self.receive_messages).start()

    def join(self) -> None:
        self.localization_button["state"] = "disabled"
        self.localization = f"({self.localization_entries[0].get()}, {self.localization_entries[1].get()})"
        self.root.client.send_message(msg=f"[LOCALIZATION] {self.localization}")
        self.tabs.hide(0), self.tabs.select(1), self.tabs.select(2)
        self.name_label_text.set(f"Research unit's localization: {self.localization}")

        engine = create_engine(DB_STRING)
        DQ = DatabaseQueries(engine=engine)
        data_to_upload = DQ.get_grouped_information_of_objects_localization(time_window=pd.DateOffset(seconds=0.5))
        data_to_upload_noised = make_signal_noise(data_to_upload, 0, 10)
        DQ.add_server_read_positions_info(data_to_upload_noised)

        for widget in self.map_tab.winfo_children():
            widget.destroy()

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(1, 1, 1)
        ax.grid()
        ax.set_title("x"), ax.set_ylabel("y")

        df = DQ.get_result()
        sns.scatterplot(data=df, x='x_localization', y='y_localization', hue='object_id', ax=ax)
        # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        # ax.xlim(-1000, 1000)
        # ax.ylim(-1000, 1000)
        # plt.show()
        # plt.clf()

        canvas = FigureCanvasTkAgg(fig, self.map_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def receive_messages(self) -> None:
        """
        Method to receive messages
        """

        while True:
            messages = self.root.client.receive_messages()
            alert, content = messages.split("]")[0][1:], messages.split("]")[1]

            if content == "[NOT CONNECTED]":
                self.localization_button["state"] = "normal"
                self.tabs.select(0)
                self.tabs.hide(1)
                self.tabs.hide(2)
                self.localization_warning_label.set("Improper")

            else:
                self.logs_area.delete('1.0', 'end')

                for msg in messages.split("\n"):
                    self.logs_area.insert('end', msg)


client_app = MainApp()
client_app.mainloop()