#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN MODULES
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread

# PROJECT MODULES
from config import MAIN_PORT, MAX_CLIENTS, SPACE_RANGE
from communication import send, receive


# CLASSES
class ArtificialServer:
    """
    Class to represent the server
    """

    def __init__(self) -> None:
        """
        Constructor
        """

        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_sock.bind(('', MAIN_PORT))
        self.server_sock.listen(MAX_CLIENTS)