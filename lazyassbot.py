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
import requests
import json
import HTMLParser
import pickle
from collections import deque
from urllib2 import HTTPError, URLError
from pprint import pprint as pprint

import praw

# Constants
READ_RECORD = 'recently_read.pkl'
BOT_NAME = u'lazyassbot'
BOT_FAQ = 'http://www.reddit.com/r/btsebots/wiki/faq'
BOT_FEEDBACK = 'http://www.reddit.com/r/btsebots/submit'
FOOTER = u'''\n
| *Incorrect? Downvote me!* | *Currently in beta* | [*FAQ*]({0}) | 
[*Report Bug/Feedback*]({1}) |'''.format(BOT_FAQ, BOT_FEEDBACK)

TIME_REGEX = re.compile(r'^.*?(?:[\W ]|^)(\d{0,2}\:\d{2})(?:\W|ish|$)'
                         '(?!.?(?:am|pm|morning|afternoon)\W).*$',
                         re.IGNORECASE|re.MULTILINE)
START_TIME = time.time()

# Youtube constants
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

def get_youtube_id(url):
    """
    Returns the youtube id for a given url or None if it is not a youtube link
    or improperly formatted
    """
    return YT_REGEX.match(url).group(1) if YT_REGEX.match(url) else None

def get_duration(yt_id):
    """
    Returns the duration for a given
    """
    r = requests.get(YT_GDATA.format(yt_id))
    return r.json()['entry']['media$group']['yt$duration']['seconds']

def time_to_seconds(time):
    """
    Takes a string in the form of "%M:%S" and returns the time in seconds
    """
    m,s = [int(x) if x != '' else 0 for x in time.split(':')]
    return 60*m + s

def build_response(time, new_url):
    """
    Constructs and returns the response
    """
    response = u'[{0}]({1})'.format(time, new_url) + FOOTER
    return response

def handle_comment(comment):
    """
    Parses through the comment object's text to see if it contains the
    regex we are looking for. If it does, then handles all of the work for it,
    else does nothing at all.

    Eek this function is kind of ugly
    """
    if (not TIME_REGEX.match(comment.body)):
        return 

    log_comment(comment)
    url = HTMLParser.HTMLParser().unescape(comment.submission.url)
    youtube_id = get_youtube_id(url)
    time = TIME_REGEX.match(comment.body).group(1)

    if not youtube_id:
        return 

    comment_secs = time_to_seconds(time)
    video_secs = get_duration(youtube_id)

    if int(comment_secs) >= int(video_secs):
        return 
    elif comment_secs < 2:
        comment_secs = 0
    else:
        comment_secs -= 2

    LOGGER.info("Comment seconds: %s" % comment_secs)
    LOGGER.info("Video seconds: %s" % video_secs)

    new_url = "{0}&t={1}".format(url, comment_secs)
    LOGGER.info("New url: %s" % new_url)
    response = build_response(time, new_url)
    comment.reply(response)
    print "Got one!"

def log_comment(comment):
    submission = comment.submission

    LOGGER.info("")
    LOGGER.info("Matched ==> %s" % TIME_REGEX.match(comment.body).group(1))
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

def main():
    print "Started"
    LOGGER.info("lazyassbot has started!")
    login()

    read = deque(maxlen=200)
    try:
        with open(READ_RECORD, 'rb') as f:
            print "Unpickle!"
            read = pickle.load(f)
    except IOError as e:
        LOGGER.info("Pickle file does not exist yet")

    print "Running"

    while True:
        try:
            comments = get_comments()
            for comment in comments:
                if comment.id not in read and comment.author.name != BOT_NAME:
                    handle_comment(comment)
                    read.append(comment.id)
            time.sleep(30)
        except (HTTPError, URLError, requests.ConnectionError) as e:
            LOGGER.info("!!!!! HTTP/URL Error was raised: %s" % e.strerror)
            print "Connection error!"
            time.sleep(180) # wait 3 minutes on error
        except KeyboardInterrupt as e:
            LOGGER.info("lazyassbot has been interrupted")
            break
    with open(READ_RECORD, 'wb') as f:
        print "Pickle!"
        pickle.dump(read, f)
    print "Stopped"

if __name__ == '__main__':
    sys.exit(main())
