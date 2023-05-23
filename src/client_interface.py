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

from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from typing import Optional, List, Dict
from sqlalchemy import create_engine
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# PROJECT PACKAGES
from config import *
from communication import send, Data
from client import Client
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

        self.map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.map_tab, text="Map")

        self.tabs.hide(1)

        Thread(target=self.receive_messages).start()

    def join(self) -> None:
        self.localization_button["state"] = "disabled"
        self.localization = f"({self.localization_entries[0].get()}, {self.localization_entries[1].get()})"
        self.root.client.send_message(Data(self.localization, alert="LOCALIZATION"))
        self.tabs.hide(0), self.tabs.select(1)

        engine = create_engine(DB_STRING)
        DQ = DatabaseQueries(engine=engine)

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        ax = fig.add_subplot(1, 1, 1)
        x1, y1, x2, y2 = SPACE_RANGE
        ax.grid()
        ax.set_title("x"), ax.set_ylabel("y")
        ax.set_xlim([x1, x2]), ax.set_ylim([y1, y2])

        for i in range(2):
            plt.pause(REFRESH_TIME)
            # ax.cla()
            data_to_upload = DQ.get_grouped_information_of_objects_localization(time_window=pd.DateOffset(seconds=REFRESH_TIME))
            data_to_upload = self.make_signal_noise(data_to_upload, 0, 10)
            DQ.add_server_read_positions_info(data_to_upload)
            df = DQ.get_result()
            sns.scatterplot(data=df, x='x_localization', y='y_localization', hue='object_id', ax=ax)
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

            canvas = FigureCanvasTkAgg(fig, self.map_tab)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            self.root.client.send_message(Data(df, alert="MAP"))

    def receive_messages(self) -> None:
        """
        Method to receive messages
        """

        while True:
            data = self.root.client.receive_messages()
            alert, content = data.alert, data.content

            if alert is not None and alert == "NOT CONNECTED":
                self.localization_button["state"] = "normal"
                self.tabs.select(0)
                self.tabs.hide(1)
                self.tabs.hide(2)
                self.localization_warning_label.set(content)

    def make_signal_noise(self, localizations_data: List[Dict], min_noise_val: int, max_noise_val: int) -> List[Dict]:
        for loc in localizations_data:
            loc['x_localization'] = loc['x_localization'] + random.randint(min_noise_val, max_noise_val)
            loc['y_localization'] = loc['y_localization'] + random.randint(min_noise_val, max_noise_val)

        return localizations_data


client_app = MainApp()
client_app.mainloop()