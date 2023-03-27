#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
import struct

from socket import socket
from pickle import dumps, loads
from typing import Union, Tuple, List

# PROJECT PACKAGES


# FUNCTIONS
def send(sock: socket, data: Union[str, List[str], None]) -> None:
    """
    Method to send the data through the client socket
    :param sock: Client socket
    :param data: Data
    """

    serialized_data = dumps(data)
    sock.sendall(struct.pack('>I', len(serialized_data)))
    sock.sendall(serialized_data)


def receive(sock: socket) -> Union[str, None]:
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

    return loads(data)