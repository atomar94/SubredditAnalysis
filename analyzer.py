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
from crawler import Crawler
from exceptions import *


class Analyzer(object):

    def login(self, botname, user_agent):
        """
        Try to log in 3 times.

        Return True on success.
        """
        for i in range(0, 3):

                if self.myBot.login(botname="bot1",
                               user_agent="'my_bot by /u/atomar94"):
                    return True
                
                else:
                    # wait and try again
                    sleep(5)
                    continue

        return False


    def check_subreddit(self, subreddit):
        """
        Checks on the listed subreddits to make sure that they are 
        valid subreddits and that there's no typos and whatnot. This 
        function removes the bad subreddits from the list so the bot 
        can carry on with its task. Feed it the list of subreddits.
        """

        for i in range(0, 3):
            print("Verifying /r/{0}...".format(subreddit))
            
            try:
                # make sure the subreddit is valid
                testSubmission = self.myBot.client.subreddit(subreddit).new(limit=1)
                print("Subreddit verified!")
                return True 

            except (InvalidSubreddit, RedirectException) as e:
                self.myBot.add_msg(e)
                logging.error("Invalid subreddit." + str(e) + "\n\n")

            except (ConnectionResetError, HTTPError, timeout) as e:
                self.myBot.add_msg(e)
                logging.error(str(subreddit) + ' ' + str(e) + "\n\n")

                # private subreddits return a 403 error
                if "403" in str(e):
                    self.myBot.add_msg("/r/{0} is private.".format(subreddit))

                # banned subreddits return a 404 error
                if "404" in str(e):
                    self.myBot.add_msg("/r/{0} banned.".format(subreddit))


                self.myBot.add_msg("Waiting a minute to try again...")   
                sleep(60)

            except (APIException, ClientException, Exception) as e:
                self.myBot.add_msg(e)
                logging.error(str(e) + "\n\n")

        print("Subreddit verification failed.")
        return False

            

    def submit_to_reddit(self, subreddit, content):
        """
        Given a subreddit and content, submit a post. The subreddit passed in is
        not the subreddit that this is posted to. It's used to format the title
        of the post before sending it to a predetermined sub, specified in self.myBot.
        """
        post = None

        while True:
            try:
                # submit the post for Reddit
                post = self.myBot.submit_post(subreddit, content)
                break

            except (ConnectionResetError, HTTPError, timeout) as e:
                self.myBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                self.myBot.add_msg("Waiting to try again...")
                sleep(60)
                continue

            except (APIException, ClientException) as e:
                self.myBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                self.myBot.log_post(subreddit, content)
                break


    def scrape_users(self, subreddit):
        """
        Given a subreddit, grab the list of users from Reddit.

        Returns userList on success.
        Returns False on fail.
        """
        userList = []
        while True:
            # get the list of users
            try:
                userList = self.myBot.get_users(subreddit)
                self.myBot.userList = []
                break

            except (InvalidSubreddit, RedirectException) as e:
                self.myBot.add_msg(e)
                logging.error("Invalid subreddit." + str(e) + "\n\n")
                return False

            except (APIException, ClientException, Exception) as e:
                self.myBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                return False

        for user in userList:
            self.myBot.log_info(user + ',')
        self.myBot.log_info("\n\n")

        return userList


    def store_as_db(self, subreddit, userList):
        """
        Given a subreddit and userList, run the analysis and store
        the data in a database.

        Returns True on success.
        """
        while True:
            try:
                # get the list of subreddits
                subredditList = self.myBot.get_subs(userList)
                self.myBot.subredditList = []
                break

            except (APIException, ClientException, OperationalError) as e:
                self.myBot.add_msg(e)
                logging.error(str(e) + "\n\n")
                return False

        for sub in subredditList:
            self.myBot.log_info(sub + ',')
        self.myBot.log_info("\n\n")


        try:
            # get the list of tuples
            subredditTuple = self.myBot.create_tuples(subreddit, subredditList)

            for item in subredditTuple:
                self.myBot.log_info(item)
                self.myBot.log_info(',')

            self.myBot.log_info("\n\n")

        except Exception as e:
            self.myBot.add_msg(e)
            logging.error("Failed to create tuples. " + str(e) + "\n\n")
            return False

        try:
            self.myBot.add_db(subreddit, subredditTuple, len(userList))

        except Exception as e:
            self.myBot.add_msg(e)
            logging.error("Failed to add to database. " + str(e) + "\n\n")
            return False

        return True


    def fetch_from_db(self, subreddit):
        """
        Grab the data from the database, if it exists.

        Return userList on success, else none.
        """
        dbFile = "{0}.db".format(subreddit)

        if not os.path.isfile("subreddits/{0}".format(dbFile)):
            return None

        con = db.connect("subreddits/{0}".format(dbFile))
        cur = con.cursor()

        sub = (subreddit,)

        cur.execute("SELECT users FROM drilldown WHERE overlaps=?", sub)

        for element in cur:
            userList = operator.getitem(element, 0)

        con.close()

        return userList


    def start_analysis(self, subreddit):
        
        self.myBot = Crawler()

        if(self.myBot.errorLogging):
            logging.basicConfig(
                filename="SubredditAnalysis_logerr.log", 
                filemode='a', format="%(asctime)s\nIn "
                "%(filename)s (%(funcName)s:%(lineno)s): "
                "%(message)s", datefmt="%Y-%m-%d %H:%M:%S", 
                level=logging.ERROR)

        user_agent = self.myBot.config['misc']['user-agent']
        
        if not self.login(botname="bot1", user_agent=user_agent):
            print("Failed to log in.")
            sys.exit(1)

        # check to make sure each subreddit is valid
        if not self.check_subreddit(subreddit):
            return False

        # check to see if a drilldown for this subreddit
        # was already done
        userList = self.fetch_from_db(subreddit)
        if not userList:
                userList = self.scrape_users(subreddit)
                self.store_as_db(subreddit, userList)

        # format the data for Reddit
        original_content = self.myBot.format_post(subreddit, userList)

        self.submit_to_reddit(subreddit, original_content)

