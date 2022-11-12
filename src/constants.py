"""This file contains all the constants used in the bot."""

from enum import Enum

from easy_pil import Font

from db import db

# Bot constants
ACTIVITY_MSG = 'I am up and running!'
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# PronounDB constants
PRONOUNDB_GET_URL = "https://pronoundb.org/api/v1/lookup"
PRONOUNDB_LOGIN_URL = "https://pronoundb.org/login/"
PRONOUNDB_SET_URL = "https://pronoundb.org/me"

# Command constants
BDAY_HELP_MSG = 'Use `/birthday help` for more info'

# MSGS
BAD_TOKEN = 'You have passed an improper or invalid token! Shutting down...'
NO_TOKEN = 'TOKEN file not found in project root! Shutting down...'
NO_CONFIG = 'CRITICAL ERROR: config file is missing! Shutting down...'

# Logging constants
LOGS = 'logs/'
LOG_FILENAME_FORMAT_PREFIX = '%Y-%m-%d %H-%M-%S'
MAX_LOGFILE_AGE_DAYS = 7

# Levelcard constants
BLACK = "#0F0F0F"
WHITE = "#F9F9F9"
DARK_GREY = "#2F2F2F"
LIGHT_GREY = "#9F9F9F"
POPPINS = Font.poppins(size=70)
POPPINS_SMALL = Font.poppins(size=50)

# Messages/Words
ACTIVITY = "/help"
NO_TICKETS_ERR = "This server does not have tickets enabled." \
                 "\nThey can be enabled by purposing a category for " \
                 "tickets if you have the manage channels permission."

