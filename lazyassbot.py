#!/usr/bin/env python

"""
Parses through the comments looking for any mention of a time, and then uses
this time to post a reply to the parent comment containing a link for video
but for the specific time that they mention.
"""

import praw
import os
import sys
import logging
import time
import re
from collections import deque

# Constants
LIMIT = 25
#TIME_REGEX = re.compile(r'^.*\d{2}

# Configure some basic logging
logging.basicConfig(filename="lazyassbot.log", 
                    format='%(asctime)s :: %(levelname)s :: %(module)s :: %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filemode='w',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Initialize the reddit object we will be using
USER_AGENT = ("A bot that posts the youtube time link when a user comments \
               about a specific time in the video. Responds via \
               /u/lazyassbot. Written by /u/btse")
REDDIT = praw.Reddit(user_agent=USER_AGENT)

def login(user=None, password=None, filename='login.txt'):
    """ Simple login helper """
    if user is None and password is None:
        with open(filename, 'rb') as f:
            user = f.readline().strip()
            password = f.readline().strip()
    elif user is not None or password is not None:
        raise Exception("Must provide both a username and password")
    REDDIT.login(user, password)

def get_comments(subreddit='videos', limit=0):
    """ reddit object's get_comments wrapper """
    return REDDIT.get_comments(subreddit, limit)

def parse_comment(comment):
    print(comment.id + " |||| " + time.ctime(comment.created_utc)
          + " |||| " + comment.body)

def main():
    LOGGER.info('lazyassbot has started!')
    login()
    read = deque(maxlen=25)
    while True:
        comments = get_comments()
        for comment in comments:
            if comment.id not in read:
                parse_comment(comment)
                read.append(comment.id)

        print "\n====================================================\n"
        time.sleep(5)

if __name__ == '__main__':
    sys.exit(main())
