#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import tkinter as tk
import tkinter.ttk as ttk
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import time

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from typing import Optional, List, Dict
from sqlalchemy import create_engine
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

# PROJECT PACKAGES
from config import *
from communication import send, receive, Data
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
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        self.client_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.client_sock.connect((HOST, PORT))

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

        self.engine = None
        self.DQ = None

        self.tabs = ttk.Notebook(self.parent)
        self.tabs.pack()

        self.info_panel_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.info_panel_tab, text="Info panel")

        ttk.Label(self.info_panel_tab, text="Location").grid(row=0, column=0, columnspan=2)
        self.location_entries = [ttk.Entry(self.info_panel_tab) for _ in range(2)]
        _ = [entry.grid(row=1, column=i, padx=5) for i, entry in enumerate(self.location_entries)]

        ttk.Label(self.info_panel_tab, text="Range").grid(row=0, column=2)
        self.range_entry = ttk.Entry(self.info_panel_tab)
        self.range_entry.grid(row=1, column=2, padx=5)

        self.join_button = ttk.Button(self.info_panel_tab, text="Join", command=self.join)
        self.join_button.grid(row=0, column=3, rowspan=2)

        self.location: Optional[Location] = None
        self.range: Optional[int] = None

        self.location_label = tk.StringVar(value="")
        tk.Label(self.info_panel_tab, textvariable=self.location_label, font=FONT).grid(row=3, column=0, columnspan=4)

        self.local_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.local_map_tab, text="Local map")

        self.global_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.global_map_tab, text="Global map")

        self.request_button = ttk.Button(self.global_map_tab, text="Get global map", command=self.get_global_map)
        self.request_button.grid(row=0, column=0)

        self.global_map_frame = ttk.Frame(self.global_map_tab)
        self.global_map_frame.grid(row=1, column=0)

        x1, y1, x2, y2 = SPACE_RANGE

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        self.local_ax = fig.add_subplot(1, 1, 1)
        self.local_ax.grid()
        self.local_ax.set_title("x"), self.local_ax.set_ylabel("y")
        self.local_ax.set_xlim([x1, x2]), self.local_ax.set_ylim([y1, y2])
        self.local_canvas = FigureCanvasTkAgg(fig, self.local_map_tab)
        self.local_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        self.global_ax = fig.add_subplot(1, 1, 1)
        self.global_ax.grid()
        self.global_ax.set_title("x"), self.global_ax.set_ylabel("y")
        self.global_ax.set_xlim([x1, x2]), self.global_ax.set_ylim([y1, y2])
        self.global_canvas = FigureCanvasTkAgg(fig, self.global_map_frame)
        self.global_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tabs.hide(1), self.tabs.hide(2)

        Thread(target=self.receive_data).start()

    def join(self) -> None:
        if self.location_entries[0].get() == "" or self.location_entries[1].get() == "" or self.range_entry.get() == "":
            self.location_label.set("Enter all values")

        else:
            self.join_button["state"] = "disabled"

            for entry in self.location_entries:
                entry["state"] = "disabled"

            self.range_entry["state"] = "disabled"

            self.location_label.set("")
            self.location = [int(self.location_entries[0].get()), int(self.location_entries[1].get())]
            self.range = int(self.range_entry.get())
            send(self.root.client_sock, Data("LOCATION", (self.location, self.range)))

    def receive_data(self) -> None:
        """
        Method to receive data
        """

        while True:
            alert, content = receive(self.root.client_sock)

            if alert == "NOT CONNECTED":
                self.join_button["state"] = "normal"

                for entry in self.location_entries:
                    entry["state"] = "normal"

                self.range_entry["state"] = "normal"

                self.tabs.select(0)
                self.tabs.hide(1), self.tabs.hide(2)
                self.location_label.set(content)

            elif alert == "GLOBAL MAP":
                print(content)
                self.global_ax.clear()
                sns.scatterplot(data=content, x='x_localization', y='y_localization', hue='object_id', ax=self.global_ax)
                x, y = self.location
                self.global_ax.scatter([x], [y], marker="*")
                self.global_ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                self.global_ax.grid()
                x1, y1, x2, y2 = SPACE_RANGE
                a = max(x - self.range, x1)
                b = max(y - self.range, y1)
                w = 2 * self.range - max(0, a + 2 * self.range - x2)
                h = 2 * self.range - max(0, b + 2 * self.range - y2)
                rect = Rectangle((a, b), w, h, fill=False)
                self.global_ax.add_patch(rect)
                self.global_canvas.draw()

            elif alert == "CONNECTED":
                self.tabs.select(2), self.tabs.select(1)
                self.engine = create_engine(DB_STRING)
                self.DQ = DatabaseQueries(engine=self.engine)
                self.root.after(int(1000 * REFRESH_TIME), self.read_data)

    def read_data(self, i: int = 0):
        if i > 10:
            return None

        self.local_ax.clear()
        data_to_upload = self.DQ.get_space_data_in_client_range(client_range=self.range, client_location=self.location,
                                                                time_window=pd.DateOffset(seconds=REFRESH_TIME))
        sns.scatterplot(data=data_to_upload, x='x_localization', y='y_localization', hue='object_id', ax=self.local_ax)
        x, y = self.location
        self.local_ax.scatter([x], [y], marker="*")
        self.local_ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.local_ax.grid()
        x1, y1, x2, y2 = SPACE_RANGE
        a = max(x - self.range, x1)
        b = max(y - self.range, y1)
        w = 2 * self.range - max(0, a + 2 * self.range - x2)
        h = 2 * self.range - max(0, b + 2 * self.range - y2)
        rect = Rectangle((a, b), w, h, fill=False)
        self.local_ax.add_patch(rect)
        self.local_canvas.draw()
        send(self.root.client_sock, Data("LOCAL MAP", data_to_upload))
        print(i)
        self.root.after(int(1000 * REFRESH_TIME), lambda: self.read_data(i=i + 1))

    def get_global_map(self):
        """

        """
        send(self.root.client_sock, Data("GLOBAL MAP", ""))


client_app = MainApp()
client_app.mainloop()
