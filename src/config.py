#!/usr/bin/python
# -*- coding: utf-8 -*-

# BUILT-IN PACKAGES
from typing import Tuple, List

# ALIASES
Location = List[int]

# GLOBAL CONSTANTS
HOST: str = "localhost"
PORT: int = 2121
MAX_CLIENTS: int = 15
N_SPECTATORS: int = 3
HIGHLIGHT: str = "black"
BORDER: int = 2
TITLE: str = "Extraterrestrial intelligence detection"
FONT: Tuple[str, int, str] = ("Garamond", 16, "bold")
SPACE_RANGE: Tuple[int, int, int, int] = (-1000, -1000, 1000, 1000)

# TIMING AND NOISE PARAMETERS
REFRESH_TIME: float = 0.5
MIN_NOISE_VAL: int = 0
MAX_NOISE_VAL: int = 10
PLOT_EXPIRATION_MINUTES: int = 2

# DATABASE PARAMETERS
DB_STRING: str = "postgresql://postgres:postgres@localhost:5432/postgres"
GENERATED_OBJECTS_NUMBER: int = 20
MIN_NUMBER_OF_SAMPLES: int = 50
MAX_NUMBER_OF_SAMPLES: int = 100
MAX_START_TRAJECTORY_OFFSET_SECONDS: int = 180
