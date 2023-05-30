#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import struct

from socket import socket
from pickle import dumps, loads
from typing import Union, Tuple, List, Optional, Any

# PROJECT PACKAGES

# CLASSES
class Data:
    """
    Class to represent the data sent during the communication
    """

    def __init__(self, alert: str, content: Any) -> None:
        """
        Constructor
        :param alert: Data alert
        :param content: Data content
        """

        self.alert = alert
        self.content = content


# FUNCTIONS
def send(sock: socket, data: Data) -> None:
    """
    Method to send the data through the client socket
    :param sock: Client socket
    :param data: Data
    """

    serialized_data = dumps(data)
    sock.sendall(struct.pack('>I', len(serialized_data)))
    sock.sendall(serialized_data)


def receive(sock: socket):
    """
    Method to receive the data through the client socket
    :param sock: Client socket
    :return: Data
    """

    size = struct.unpack('>I', sock.recv(4))[0]
    data = b""
    remaining_size = size

    while remaining_size != 0:
        data += sock.recv(remaining_size)
        remaining_size = size - len(data)

    data = loads(data)

    return data.alert, data.content