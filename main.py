import logging
import operator
import os
import sqlite3 as db
from sqlite3 import OperationalError
from socket import timeout
import sys
from time import sleep
from praw.exceptions import *
from requests.exceptions import HTTPError
from analyzer import Analyzer
from exceptions import *


if __name__ == "__main__":
    analyzer = Analyzer()
    analyzer.start_analysis()

