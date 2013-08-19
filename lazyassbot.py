#!/usr/bin/env python

"""
Parses through the comments looking for any mention of a time, and then uses
this time to post a reply to the parent comment containing a link for video
but for the specific time that they mention.
"""

import os
import sys
import logging
import time
import re
from collections import deque

import praw

# Constants
TIME_REGEX = re.compile(r'^.*?(\d{0,2}\:\d{2}).*$')
START_TIME = time.time()

# Configure some basic logging
logging.basicConfig(filename='lazyassbot.log',
                    format='%(asctime)s :: %(levelname)s :: %(module)s :: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filemode='w',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Initialize the Reddit object we will be using
USER_AGENT = ("A bot that posts the youtube time link when a user comments \
               about a specific time in the video. Responds via \
               /u/lazyassbot. Written by /u/btse")
REDDIT = praw.Reddit(user_agent=USER_AGENT)


def login(user=None, password=None, filename='login.txt'):
    """ Logins in to Reddit using the user/password provided by login.txt """
    if user is None and password is None:
        with open(filename, 'rb') as f:
            user = f.readline().strip()
            password = f.readline().strip()
    REDDIT.login(user, password)

def get_comments(subreddit_='videos', limit_=100):
    """ Reddit object's get_comments() wrapper """
    return REDDIT.get_comments(subreddit=subreddit_, limit=limit_)

def passes_filter(comment):
    """
    Parses through the comment object's html body to see if it contains the
    regex we are looking for. Also does some additional checks to improve
    accuracy since a simple regex is not enough.

    Returns true if the comment passes, else false
    """
    if (not TIME_REGEX.match(comment.body)):
        return False


    return True

def get_submission(comment):
    """
    Returns a submission object for the provided comment object
    """


def main():
    print "Started"
    LOGGER.info("lazyassbot has started!")
    login()
    read = deque(maxlen=200)
    print "Running"
    while True:
        try:
            comments = get_comments()
            for comment in comments:
                if comment.id not in read and passes_filter(comment):
                    read.append(comment.id)
            print "read size: " + str(len(read))
            print "==========================================================="
            time.sleep(30)
        except (HTTPError, URLError) as e:
            time.sleep(180) # wait 3 minutes on error
        except KeyboardInterrupt as e:
            LOGGER.info("lazyassbot has been interrupted")
    print "Stopped"

if __name__ == '__main__':
    sys.exit(main())
