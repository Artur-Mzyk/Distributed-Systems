#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN MODULES
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread

# PROJECT MODULES
from config import PORT, MAX_CLIENTS
from communication import send, receive


# CLASSES
class Server:
    """
    Class to represent the server
    """

    def __init__(self) -> None:
        """
        Constructor
        """

        self.client_socks = []
        self.messages = []

        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_sock.bind(('', PORT))
        self.server_sock.listen(MAX_CLIENTS)

    def handle_client(self, client_sock: socket) -> None:
        """
        Method to handle the client
        :param client_sock: Client socket
        """

        while True:
            try:
                msg = receive(client_sock)
                self.messages.append(msg)

                for c in self.client_socks:
                    send(c, self.messages)

            except:
                print("[SERVER ERROR] Message not received. Connection lost")
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