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
        self.ax = None
        self.canvas = None

        self.tabs = ttk.Notebook(self.parent)
        self.tabs.pack()

        self.lobby_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.lobby_tab, text="Lobby")

        ttk.Label(self.lobby_tab, text="Localization").grid(row=0, column=0, columnspan=2)
        self.location_entries = [ttk.Entry(self.lobby_tab) for _ in range(2)]
        _ = [entry.grid(row=1, column=i, padx=5) for i, entry in enumerate(self.location_entries)]

        ttk.Label(self.lobby_tab, text="Range").grid(row=2, column=0, columnspan=2)
        self.range_entry = ttk.Entry(self.lobby_tab)
        self.range_entry.grid(row=3, column=0, padx=5)

        self.join_button = ttk.Button(self.lobby_tab, text="Join", command=self.join)
        self.join_button.grid(row=0, column=2, rowspan=5)

        self.location: Optional[Location] = None
        self.range: Optional[int] = None

        self.location_label = tk.StringVar(value="")
        tk.Label(self.lobby_tab, textvariable=self.location_label, font=FONT).grid(row=4, column=0, columnspan=3)

        self.local_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.local_map_tab, text="Local map")

        self.global_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.global_map_tab, text="Global map")

        self.request_button = ttk.Button(self.global_map_tab, text="Get global map", command=self.ask)
        self.request_button.grid(row=0, column=2)

        self.tabs.hide(1), self.tabs.hide(2)

        Thread(target=self.receive_data).start()

    def join(self) -> None:
        if self.location_entries[0].get() == "" or self.location_entries[1].get() == "" or self.range_entry.get() == "":
            self.location_label.set("Enter all values")

        else:
            self.join_button["state"] = "disabled"
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
                self.tabs.select(0), self.tabs.hide(1), self.tabs.hide(2)
                self.location_label.set(content)

            elif alert == "GLOBAL":
                for widget in self.global_map_tab.winfo_children():
                    widget.destroy()

                x1, y1, x2, y2 = SPACE_RANGE
                fig = plt.Figure(figsize=(10, 10), dpi=100)
                ax = fig.add_subplot(1, 1, 1)
                ax.grid()
                ax.set_title("x"), ax.set_ylabel("y")
                ax.set_xlim([x1, x2]), ax.set_ylim([y1, y2])

                sns.scatterplot(data=content, x='x_localization', y='y_localization', hue='object_id', ax=ax)
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

                canvas = FigureCanvasTkAgg(fig, self.global_map_tab)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            elif alert == "CONNECTED":
                self.tabs.hide(0), self.tabs.select(2), self.tabs.select(1)

                self.engine = create_engine(DB_STRING)
                self.DQ = DatabaseQueries(engine=self.engine)

                for widget in self.local_map_tab.winfo_children():
                    widget.destroy()

                fig = plt.Figure(figsize=(10, 10), dpi=100)
                self.ax = fig.add_subplot(1, 1, 1)
                x1, y1, x2, y2 = SPACE_RANGE
                self.ax.grid()
                self.ax.set_title("x"), self.ax.set_ylabel("y")
                self.ax.set_xlim([x1, x2]), self.ax.set_ylim([y1, y2])
                self.canvas = FigureCanvasTkAgg(fig, self.local_map_tab)
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                self.root.after(int(1000 * REFRESH_TIME), self.read_data)

    def read_data(self, iter: int = 0):
        if iter > 10:
            return None

        self.ax.clear()
        data_to_upload = self.DQ.get_space_data_in_client_range(client_range=self.range, client_location=self.location,
                                                                time_window=pd.DateOffset(seconds=REFRESH_TIME))
        data_to_upload = self.inference(data_to_upload)
        sns.scatterplot(data=data_to_upload, x='x_localization', y='y_localization', hue='object_id', ax=self.ax)
        x, y = self.location
        self.ax.scatter([x], [y], marker="*")
        self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.ax.grid()
        x1, y1, x2, y2 = SPACE_RANGE
        a = max(x - self.range, x1)
        b = max(y - self.range, y1)
        w = 2 * self.range - max(0, a + 2 * self.range - x2)
        h = 2 * self.range - max(0, b + 2 * self.range - y2)
        rect = Rectangle((a, b), w, h, fill=False)
        self.ax.add_patch(rect)
        self.canvas.draw()
        send(self.root.client_sock, Data("MAP", data_to_upload))
        self.root.after(int(1000 * REFRESH_TIME), lambda: self.read_data(iter=iter + 1))

    def inference(self, data: pd.DataFrame) -> pd.DataFrame:
        data['x_localization'] = data['x_localization'] + random.randint(MIN_NOISE_VAL, MAX_NOISE_VAL)
        data['y_localization'] = data['y_localization'] + random.randint(MIN_NOISE_VAL, MAX_NOISE_VAL)

        return data

    def ask(self):
        send(self.root.client_sock, Data("REQUEST", ""))


client_app = MainApp()
client_app.mainloop()