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
from urllib2 import HTTPError, URLError

import praw

# Constants
TIME_REGEX = re.compile(r'^.*?(?:[\W ]|^)(\d{0,2}\:\d{2})(?:\W|ish|$)'
                         '(?!.?(?:am|pm|morning|afternoon)\W).*$',
                         re.IGNORECASE|re.MULTILINE)
START_TIME = time.time()

YT_REGEX = re.compile('^(?:https?://)?(?:www\.)?(?:youtu\.be/|youtube\.com'
            '(?:/embed/|/v/|/watch\?v=|/watch\?.+&v=))([\w-]{11})(?:.+)?$')
YT_GDATA = 'http://gdata.youtube.com/feeds/api/videos/{0}?alt=json'

MATCH_ALL = re.compile(r'^.*?(\d{0,2}\:\d{2}).*$', re.IGNORECASE|re.MULTILINE)

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
    Parses through the comment object's text to see if it contains the
    regex we are looking for. Also does some additional checks to improve
    accuracy since a simple regex is not enough.

    Returns true if the comment passes, else false
    """
    if (MATCH_ALL.match(comment.body)):
        print "weak find!"
        log_comment(comment, match=MATCH_ALL.match(comment.body).group(1), extra="#######WEAK#######")

    if (not TIME_REGEX.match(comment.body)):
        return False

    time = TIME_REGEX.match(comment.body).group(1)

    print "strong find!"
    log_comment(comment, match=time)
    return True

def log_comment(comment, match=None, extra=None):
    submission = comment.submission

    LOGGER.info("")
    if extra:
        LOGGER.info(extra)
    LOGGER.info("Matched ==> %s" % match)
    LOGGER.info("Comment id: %s" % comment.id)
    LOGGER.info("Time created: %s" % time.ctime(comment.created_utc))
    LOGGER.info("Root: %s" % comment.is_root)
    LOGGER.info("Likes: %s" % comment.likes)
    LOGGER.info("Submission id: %s" % submission.id)
    LOGGER.info("Submission title: %s" % submission.title)
    LOGGER.info("Submission created: %s" %  time.ctime(submission.created_utc))
    LOGGER.info("Submission domain: %s" % submission.domain)
    LOGGER.info("Submission url: %s" % submission.url)
    LOGGER.info("Comment body: %s" % comment.body)
    LOGGER.info("")

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
    total_time = 0
    while True:
        try:
            uniques = 0
            comments = get_comments()
            for comment in comments:
                if comment.id not in read:
                    uniques += 1
                    read.append(comment.id)
                    passes_filter(comment)
            if uniques >= 25:
                print "Uniques surpassed 25: %d" % uniques
            time.sleep(30)
        except (HTTPError, URLError) as e:
            LOGGER.info("!!!!! HTTP/URL Error was raised: %s" % e.strerror)
            time.sleep(180) # wait 3 minutes on error
        except KeyboardInterrupt as e:
            LOGGER.info("lazyassbot has been interrupted")
        if (((time.time() - START_TIME) / 60) > (total_time + 10)):
            total_time += 10
            print "Time passed: %d minutes" % total_time

    print "Stopped"

if __name__ == '__main__':
    sys.exit(main())
