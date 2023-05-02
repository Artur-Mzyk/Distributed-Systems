#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import time
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib.pyplot as plt

from threading import Thread
from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from typing import Optional, List
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle

# PROJECT MODULES
from config import *
from server import Server
from communication import send, receive


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
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_sock.bind(('', PORT))
        self.server_sock.listen(MAX_CLIENTS)

        Thread(target=self.accept_clients, args=(N_SPECTATORS,)).start()
        print("[SERVER STARTED]")
        self.localizations = []
        self.client_socks = []
        self.messages = []

        # Main frame
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frame = tk.Frame(container)
        self.frame.grid(row=0, column=0)

    def handle_client(self, client_sock: socket) -> None:
        """
        Method to handle the client
        :param client_sock: Client socket
        """

        while True:
            try:
                msg = receive(client_sock)

                if "[LOC]" in msg:
                    loc = msg[6:]
                    x = int(loc[1:-1].split(", ")[0])
                    y = int(loc[1:-1].split(", ")[1])
                    x1, y1, x2, y2 = SPACE_RANGE

                    if loc in self.localizations or x < x1 or x > x2 or y < y1 or y > y2:
                        send(client_sock, "Not connected")
                        continue

                    else:
                        self.localizations.append(loc)
                        msg = f"[SERVER] There is a new research unit at localization {loc}\n"

                        for widget in self.frame.winfo_children():
                            widget.destroy()

                        fig = plt.Figure(figsize=(10, 10), dpi=100)
                        ax = fig.add_subplot(1, 1, 1)
                        ax.grid()
                        ax.set_title("x")
                        ax.set_ylabel("y")
                        ax.set_xlim([x1, x2])
                        ax.set_ylim([y1, y2])

                        for loc in self.localizations:
                            x = int(loc[1:-1].split(", ")[0])
                            y = int(loc[1:-1].split(", ")[1])
                            ax.scatter([x], [y])
                            ax.add_patch(Rectangle((x - 75, y - 75), 150, 150, fill=False))

                        canvas = FigureCanvasTkAgg(fig, self.frame)
                        canvas.draw()
                        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

                self.messages.append(msg)

                for c in self.client_socks:
                    send(c, self.messages)

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


server_app = MainApp()
server_app.mainloop()