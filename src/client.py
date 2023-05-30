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
from utils import draw_map


# CLASSES
class ClientApp(tk.Tk):
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

    def __init__(self, parent: ttk.Frame, root: ClientApp) -> None:
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

        self.space_range = SPACE_RANGE
        x1, y1, x2, y2 = SPACE_RANGE

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        self.local_ax = fig.add_subplot(1, 1, 1)
        self.local_ax.grid()
        self.local_ax.set(xlim=(SPACE_RANGE[0], SPACE_RANGE[2]), ylim=(SPACE_RANGE[1], SPACE_RANGE[3]),
                          xlabel="x", ylabel="y")
        self.local_canvas = FigureCanvasTkAgg(fig, self.local_map_tab)
        self.local_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        self.global_ax = fig.add_subplot(1, 1, 1)
        self.global_ax.grid()
        self.global_ax.set(xlim=(SPACE_RANGE[0], SPACE_RANGE[2]), ylim=(SPACE_RANGE[1], SPACE_RANGE[3]),
                           xlabel="x", ylabel="y")
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
                map, locations = content
                draw_map(self.global_ax, self.global_canvas, map, locations=locations)

            elif alert == "CONNECTED":
                self.tabs.select(2), self.tabs.select(1)
                self.engine = create_engine(DB_STRING)
                self.DQ = DatabaseQueries(engine=self.engine)
                self.root.after(int(1000 * REFRESH_TIME), self.read_data)

    def read_data(self, i: int = 0):
        if i > 1000:
            return None

        data_to_upload = self.DQ.get_space_data_in_client_range(client_range=self.range,
                                                                client_location=self.location,
                                                                time_window=pd.DateOffset(seconds=REFRESH_TIME))
        if not data_to_upload.empty:
            print('\n', data_to_upload, '\n')  # TODO delete prints

            draw_map(self.local_ax, self.local_canvas, data_to_upload, locations=[(self.location, self.range)])
            send(self.root.client_sock, Data("LOCAL MAP", data_to_upload))
        else:
            print(i, 'searching...') # TODO delete prints
            pass
        self.root.after(int(1000 * REFRESH_TIME), lambda: self.read_data(i=i + 1))

    def get_global_map(self):
        """
        Method to get map with all received signals
        self.global_content ~ [locations of stations, ranges of stations]
        """
        send(self.root.client_sock, Data("GLOBAL MAP", ""))


client_app = ClientApp()
client_app.mainloop()
