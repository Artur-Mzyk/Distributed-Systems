#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import time
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib.pyplot as plt
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
        self.map = None
        self.DQ = DatabaseQueries(engine=engine)

        # Main frame
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frame = tk.Frame(container)
        self.frame.grid(row=0, column=0)

        fig = plt.Figure(figsize=(10, 10), dpi=100)
        self.ax = fig.add_subplot(1, 1, 1)
        x1, y1, x2, y2 = SPACE_RANGE
        self.ax.grid()
        self.ax.set_title("x"), self.ax.set_ylabel("y")
        self.ax.set_xlim([x1, x2]), self.ax.set_ylim([y1, y2])
        self.canvas = FigureCanvasTkAgg(fig, self.frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

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
                        # self.draw_map()

                elif alert == "LOCAL MAP":
                    self.map = content
                    if len(self.map) > 0:
                        self.DQ.add_server_read_positions_info(self.map.to_dict(orient='records'))
                    self.draw_map()

                elif alert == "GLOBAL MAP":
                    map = self.DQ.get_result()
                    print(map)
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

    def draw_map(self) -> None:
        self.ax.clear()
        sns.scatterplot(data=self.map, x='x_localization', y='y_localization', hue='object_id', ax=self.ax)
        x1, y1, x2, y2 = SPACE_RANGE

        for loc in self.locations:
            (x, y), rng = loc
            self.ax.scatter([x], [y], marker="*")
            a = max(x - rng, x1)
            b = max(y - rng, y1)
            w = 2 * rng - max(0, a + 2 * rng - x2)
            h = 2 * rng - max(0, b + 2 * rng - y2)
            rect = Rectangle((a, b), w, h, fill=False)
            self.ax.add_patch(rect)
            self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            self.ax.grid()
            self.canvas.draw()

        # DQ.add_server_read_positions_info(data_to_upload)
        # df = DQ.get_result()


server_app = MainApp()
server_app.mainloop()