#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN MODULES
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from typing import List

# PROJECT MODULES
from config import HOST, PORT
from communication import send, receive


# CLASSES
class Client:
    """
    Class to represent a client
    """

    def __init__(self) -> None:
        """
        Constructor
        """

        self.client_sock = socket(AF_INET, SOCK_STREAM)
        self.client_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.client_sock.connect((HOST, PORT))

    def send_message(self, msg: str) -> None:
        """
        Method to send the message to the server
        :param msg: Message
        """

        send(self.client_sock, msg)

    def receive_messages(self) -> str:
        """
        Method to receive messages
        :return: Decoded messages
        """

        return receive(self.client_sock)