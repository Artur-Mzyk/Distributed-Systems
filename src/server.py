#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import time
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib.pyplot as plt
import datetime
import random
import pandas as pd
import seaborn as sns

from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from typing import Optional, List, Tuple
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
from sqlalchemy import create_engine
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread

# PROJECT MODULES
from config import *
from communication import send, receive, Data
from database.database_architecture import create_architecture
from database.database_upload import upload_data
from database.database_queries import DatabaseQueries
from utils import draw_map


# CLASSES
class ServerApp(tk.Tk):
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

        # Server socket
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_sock.bind(('', PORT))
        self.server_sock.listen(MAX_CLIENTS)

        engine = create_engine(DB_STRING)
        create_architecture(engine=engine)
        upload_data(engine=engine)

        Thread(target=self.accept_clients, args=(N_SPECTATORS,)).start()
        print("[SERVER STARTED]")
        self.locations = []
        self.client_socks = []
        self.messages = []
        self.anomalies = []
        self.prev_anomalies = []
        self.DQ = DatabaseQueries(engine=engine)

        # Main frame
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tabs = ttk.Notebook(container)
        self.tabs.pack()

        self.local_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.local_map_tab, text="Local map")

        self.global_map_tab = tk.Frame(self.tabs, highlightbackground=HIGHLIGHT, highlightthickness=BORDER)
        self.tabs.add(self.global_map_tab, text="Global map")

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
        self.global_canvas = FigureCanvasTkAgg(fig, self.global_map_tab)
        self.global_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tabs.select(0)

    def handle_client(self, client_sock: socket) -> None:
        """
        Method to handle the client
        :param client_sock: Client socket
        """

        while True:
            try:
                alert, content = receive(client_sock)

                if alert == "LOCATION":
                    (x, y), rng = content
                    x1, y1, x2, y2 = SPACE_RANGE

                    if x < x1 or x > x2 or y < y1 or y > y2:
                        send(client_sock, Data("NOT CONNECTED", "Out of range"))

                    elif content in self.locations:
                        send(client_sock, Data("NOT CONNECTED", "Duplicated"))

                    else:
                        self.locations.append(content)
                        send(client_sock, Data("CONNECTED", ""))

                elif alert == "LOCAL MAP":
                    local_map = content

                    if len(local_map) > 0:
                        self.DQ.add_server_read_positions_info(local_map.to_dict(orient='records'))
                        self.DQ.grouped_information_of_objects_localization(time_window=pd.DateOffset(seconds=REFRESH_TIME))

                        # Anomalies detection:
                        self.anomalies = self.DQ.detecting_anomaly()

                        if self.anomalies != self.prev_anomalies:
                            detected_anomaly = list(set(self.anomalies) - set(self.prev_anomalies))

                            if detected_anomaly:
                                print("\n Detect anomaly: {0} at {1}".format(detected_anomaly, datetime.datetime.now()))
                                anomaly_point = self.DQ.get_anomaly_detection_point(detected_anomaly[0], datetime.datetime.now())
                                print(anomaly_point)

                            self.prev_anomalies = self.anomalies

                        draw_map(self.local_ax, self.local_canvas, local_map, locations=self.locations)

                        global_map = self.DQ.get_result()

                        if len(global_map) > 0:
                            draw_map(self.global_ax, self.global_canvas, global_map, locations=self.locations, anomalies=self.anomalies)

                elif alert == "GLOBAL MAP":
                    map = [self.DQ.get_result(), self.locations]
                    send(client_sock, Data("GLOBAL MAP", map))

            except Exception as e:
                print(f"[SERVER ERROR] {e}")
                break

    def accept_clients(self, n_clients: int) -> None:
        """
        Method to accept the chat clients
        :param n_clients: Number of clients
        """

        for _ in range(n_clients):
            client_sock, _ = self.server_sock.accept()
            self.client_socks.append(client_sock)
            Thread(target=self.handle_client, args=(client_sock,)).start()


server_app = ServerApp()
server_app.mainloop()