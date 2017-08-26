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
from crawler import SubredditAnalysis
from exceptions import *


def login(botname, user_agent):
    """
    Try to log in 3 times.

    Return True on success.
    """
    for i in range(0, 3):

            if myBot.login(botname="bot1",
                           user_agent="'my_bot by /u/atomar94"):
                return True
            
            else:
                # wait and try again
                sleep(5)
                continue

    return False


def check_subreddits(subredditList):
    """
    Checks on the listed subreddits to make sure that they are 
    valid subreddits and that there's no typos and whatnot. This 
    function removes the bad subreddits from the list so the bot 
    can carry on with its task. Feed it the list of subreddits.
    """

    for i in range(0, 3):
        try:
            for subreddit in subredditList:
                if(subreddit in ["quit", ".quit", 'q']):
                    continue

                print("Verifying /r/{0}...".format(subreddit))
                

                try:
                    # make sure the subreddit is valid
                    testSubmission = myBot.client.get_subreddit(subreddit).get_new(limit=1)
                    for submission in testSubmission:
                        "".join(submission.title)

                except (InvalidSubreddit, RedirectException) as e:
                    myBot.add_msg(e)
                    logging.error("Invalid subreddit. Removing from list." + str(e) + "\n\n")
                    subredditList.remove(subreddit)
                    raise SkipThis("Skipping invalid subreddit...")

                except (ConnectionResetError, HTTPError, timeout) as e:
                    myBot.add_msg(e)
                    logging.error(str(subreddit) + ' ' + str(e) + "\n\n")

                    # private subreddits return a 403 error
                    if "403" in str(e):
                        myBot.add_msg("/r/{0} is private. Removing from list...".format(subreddit))
                        subredditList.remove(subreddit)
                        continue

                    # banned subreddits return a 404 error
                    if "404" in str(e):
                        myBot.add_msg("/r/{0} banned. Removing from list...".format(subreddit))
                        subredditList.remove(subreddit)
                        continue

                    myBot.add_msg("Waiting a minute to try again...")   
                    sleep(60)
                    raise SkipThis("Trying again...")

                except (APIException, ClientException, Exception) as e:
                    myBot.add_msg(e)
                    logging.error(str(e) + "\n\n")
                    raise SkipThis("Something went wrong. Skipping...")

            break

        except SkipThis:
            if i == 2:
                sys.exit(1)

            else:
                continue

    try:
        # keeps this message from being displayed when
        # the only item is a quit command
        if subredditList[0] not in ["quit", ".quit", 'q']:
            print("Subreddit verification completed.")

    except IndexError:
        print("Subreddit List empty.")
        

def submit_to_reddit(subreddit, content):
    """
    Given a subreddit and content, submit a post. The subreddit passed in is
    not the subreddit that this is posted to. It's used to format the title
    of the post before sending it to a predetermined sub, specified in myBot.
    """
    post = None

    while True:
        try:
            # submit the post for Reddit
            post = myBot.submit_post(subreddit, content)
            break

        except (ConnectionResetError, HTTPError, timeout) as e:
            myBot.add_msg(e)
            logging.error(str(e) + "\n\n")
            myBot.add_msg("Waiting to try again...")
            sleep(60)
            continue

        except (APIException, ClientException, Exception) as e:
            myBot.add_msg(e)
            logging.error(str(e) + "\n\n")
            myBot.log_post(subreddit, content)
            break

    if(post):
        try:
            print("Setting post's flair...")
            
            myBot.give_flair(post, subreddit)

        except ModeratorRequired as e:
            myBot.add_msg(e)
            logging.error("Failed to set flair. " + str(e) + '\n' + str(post.permalink) + "\n\n")

        except (APIException, ClientException, Exception) as e:
            myBot.add_msg(e)
            logging.error(str(e) + "\n\n")


def scrape_users(subreddit):
    """
    Given a subreddit, grab the list of users from Reddit.

    Returns userList on success.
    Returns False on fail.
    """
    userList = []
    while True:
        # get the list of users
        try:
            userList = myBot.get_users(subreddit)
            myBot.userList = []
            break

        except (InvalidSubreddit, RedirectException) as e:
            myBot.add_msg(e)
            logging.error("Invalid subreddit." + str(e) + "\n\n")
            return False

        except (APIException, ClientException, Exception) as e:
            myBot.add_msg(e)
            logging.error(str(e) + "\n\n")
            return False

    for user in userList:
        myBot.log_info(user + ',')
    myBot.log_info("\n\n")

    return userList


def store_as_db(subreddit, userList):
    """
    Given a subreddit and userList, run the analysis and store
    the data in a database.

    Returns True on success.
    """
    while True:
        try:
            # get the list of subreddits
            subredditList = myBot.get_subs(userList)
            myBot.subredditList = []
            break

        except (APIException, ClientException, OperationalError) as e:
            myBot.add_msg(e)
            logging.error(str(e) + "\n\n")
            return False

    for sub in subredditList:
        myBot.log_info(sub + ',')
    myBot.log_info("\n\n")


    try:
        # get the list of tuples
        subredditTuple = myBot.create_tuples(subreddit, subredditList)

        for item in subredditTuple:
            myBot.log_info(item)
            myBot.log_info(',')

        myBot.log_info("\n\n")

    except Exception as e:
        myBot.add_msg(e)
        logging.error("Failed to create tuples. " + str(e) + "\n\n")
        return False

    try:
        myBot.add_db(subreddit, subredditTuple, len(userList))

    except Exception as e:
        myBot.add_msg(e)
        logging.error("Failed to add to database. " + str(e) + "\n\n")
        return False

    return True



def fetch_from_db(subreddit):
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

def main():
    
    user_agent = myBot.config['misc']['user-agent']

    print("Welcome to Reddit Analysis Bot.")
    print("Type \"quit\", \".quit\", or \'q\' to exit the program.")
    
    if not login(botname="bot1", user_agent=user_agent):
        print("Failed to log in.")
        sys.exit(1)

    while True:
        try:
            # list of subreddits you want to analyze
            drilldownList = raw_input("Enter the subreddits you wish to target.~/> ").split()

        except NameError:
            # python 3 support
            drilldownList = input("Enter the subreddits you wish to target.~/> ").split()

        # check to make sure each subreddit is valid
        check_subreddits(drilldownList)

        # iterate through the drilldownList to get data
        for subreddit in drilldownList:

            if(subreddit in ["quit", ".quit", 'q']):
                print("Quitting...")
                
                sys.exit(0)

            # check to see if a drilldown for this subreddit
            # was already done
            userList = fetch_from_db(subreddit)
            if not userList:
                    userList = scrape_users(subreddit)
                    store_as_db(subreddit, userList)

            # format the data for Reddit
            original_content = myBot.format_post(subreddit, userList)

            submit_to_reddit(subreddit, original_content)


if __name__ == "__main__":
    myBot = SubredditAnalysis()

    if(myBot.errorLogging):
        logging.basicConfig(
            filename="SubredditAnalysis_logerr.log", 
            filemode='a', format="%(asctime)s\nIn "
            "%(filename)s (%(funcName)s:%(lineno)s): "
            "%(message)s", datefmt="%Y-%m-%d %H:%M:%S", 
            level=logging.ERROR
        )

    main()
