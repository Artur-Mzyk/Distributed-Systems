#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
from typing import Tuple


# GLOBAL CONSTANTS
HOST: str = "localhost"
PORT: int = 2121
MAX_CLIENTS: int = 15
N_SPECTATORS: int = 3
HIGHLIGHT: str = "black"
BORDER: int = 2
TITLE: str = "Extraterrestrial intelligence detection"
SPACE_RANGE: Tuple[int, int, int, int] = (-1000, -1000, 1000, 1000)
DB_STRING: str = "postgresql://postgres:postgres@localhost:5432/postgres"
REFRESH_TIME: float = 0.5
MIN_NOISE_VAL: int = 0
MAX_NOISE_VAL: int = 1