#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
from threading import Thread

# PROJECT MODULES
from config import N_SPECTATORS
from server import Server


# MAIN
if __name__ == "__main__":
    server = Server()
    Thread(target=server.accept_clients, args=(N_SPECTATORS,)).start()
    print("[SERVER STARTED]")