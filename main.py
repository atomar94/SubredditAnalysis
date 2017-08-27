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
from polls import Poll


if __name__ == "__main__":
    mypoll = Poll("10915164")
    analyzer = Analyzer()
    #for sub in mypoll.top():
    #    analyzer.start_analysis(sub)
    for sub in ["learnpython", "asoiaf"]:
        analyzer.start_analysis(sub)
