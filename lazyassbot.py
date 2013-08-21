#!/usr/bin/env python

"""
A simple bot that replies with the corresponding Youtube time link when someone 
comments on a specific time in the original video.
"""

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

import praw

# File that holds the 'handled' deque when the bot is stopped. Prevents 
# re-handling of comments that have already been handled before the bot was stopped
HANDLED_FILE = 'recently_read.pkl'

# Bot info
BOT_NAME = u'lazyassbot'
BOT_FAQ = 'http://www.reddit.com/r/lazyassbot/wiki/faq'
BOT_FEEDBACK = 'http://www.reddit.com/r/lazyassbot/submit'

# The footer that is attached to all comment replies
FOOTER = u'''\n
| *Incorrect? Downvote me!* | *Currently in beta* | [*FAQ*]({0}) | 
[*Report Bug/Feedback*]({1}) |'''.format(BOT_FAQ, BOT_FEEDBACK)

JIFFY_REGEX = re.compile(r'^.*?Jiffy!.*$')

# regex used to match against the comment's text
TIME_REGEX = re.compile(r'^.*?(?:[\W ]|^)(\d{0,2}\:\d{2})(?:\W|ish|$)'
                         '(?!.?(?:am|pm|morning|afternoon)\W).*$',
                         re.IGNORECASE|re.MULTILINE)

# Grabs the unique Youtube ID from a Youtube URL
YT_REGEX = re.compile('^(?:https?://)?(?:www\.)?(?:youtu\.be/|youtube\.com'
                 '(?:/embed/|/v/|/watch\?v=|/watch\?.+&v=))([\w-]{11})(?:.+)?$')
# The URL that is used to get data on a specific Youtube ID
YT_GDATA = 'http://gdata.youtube.com/feeds/api/videos/{0}?alt=json'

# Matches any kind of link
# This needs to be fixed to account for more dns names
LINK_REGEX = re.compile('(?:https?://)?(?:www\.)?.*?\.com',
                        re.MULTILINE)

# Configure some basic logging
logging.basicConfig(filename='logs/lazyassbot-{0}.log'.format(time.ctime().replace(' ', '-')),
                    format='%(asctime)s :: %(levelname)s :: %(module)s :: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filemode='w',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Initialize the Reddit object we will be using throughout
USER_AGENT = ("A bot that posts the youtube time link when a user comments "
              "about a specific time in the video. Responds via " 
              "/u/lazyassbot. Written by /u/btse")
REDDIT = praw.Reddit(user_agent=USER_AGENT)



def login(user=None, password=None, filename='login.txt'):
    """ Logs in to Reddit using the user/password provided by login.txt """
    if user is None and password is None:
        with open(filename, 'rb') as f:
            user = f.readline().strip()
            password = f.readline().strip()
    # TODO There needs to be more proper checks here
    REDDIT.login(user, password)

def get_comments(subreddit_='videos', limit_=100):
    """ Reddit object's get_comments() wrapper """
    return REDDIT.get_comments(subreddit=subreddit_, limit=limit_)

def get_youtube_id(url):
    """
    Returns the youtube id for a given url or None if it is not a youtube link
    or is improperly formatted. 
    """
    return YT_REGEX.match(url).group(1) if YT_REGEX.match(url) else None

def get_video_info(yt_id):
    """ Returns the video duration, url for the provided youtube id. """
    r = requests.get(YT_GDATA.format(yt_id))
    duration = r.json()['entry']['media$group']['yt$duration']['seconds']
    url = r.json()['entry']['link'][0]['href']
    return duration, url

def time_to_seconds(time):
    """
    Takes a string in the form of "%M:%S" and returns the total seconds.
    Can also handle cases where only ":%S" is provided.
    """
    m,s = [int(x) if x != '' else 0 for x in time.split(':')]
    return 60*m + s

def build_reply(time, new_url):
    """
    Constructs and returns the full reply that will be posted to Reddit
    """
    return u'[{0}]({1})'.format(time, new_url) + FOOTER

def is_unique(comment):
    """
    Checks to see if the bot has already posted in the current comment's subtree

    The main purpose of this is so that no one messes with the bot.
    Returns True if the bot has not posted yet, False otherwise.
    """
    if comment.is_root is False:
        current = REDDIT.get_info(thing_id=comment.parent_id)
        while current.is_root is False:
            if current.author.name == BOT_NAME:
                return False
            current = REDDIT.get_info(thing_id=current.parent_id)
    return True

def handle_comment(comment):
    """
    Parses through the comment object's text to see if it contains the
    regex we are looking for. If it does, then handles all of the work for it
    and then replies.

    Returns the newly created comment if it replied, else returns None.

    Eek this function is kind of ugly
    """
    if comment.author.name == BOT_NAME:
        return 

    if TIME_REGEX.match(comment.body) is None:
        return 
    time = TIME_REGEX.match(comment.body).group(1)

    log_comment(comment)

    if JIFFY_REGEX.search(comment.body):
        print "Damn you jiffy!"
        LOGGER.info("Jiffy comment...skipping!")
        return

    # This is not the best way to do it, but should do for now
    if LINK_REGEX.search(comment.body):
        print "How dare you take my job!"
        LOGGER.info("Already contains a link...skipping!")
        return

    if is_unique(comment) is False:
        print "Stop messing with lazybot!"
        LOGGER.info("Bot already posted in this subtree...skipping!")
        return

    orig_url = HTMLParser.HTMLParser().unescape(comment.submission.url)
    youtube_id = get_youtube_id(orig_url)
    if youtube_id is None:
        LOGGER.info("Not a valid youtube link...skipping!")
        return 

    comment_secs = time_to_seconds(time)
    duration, new_url = get_video_info(youtube_id)
    LOGGER.info("Comment seconds: %s" % comment_secs)
    LOGGER.info("Video seconds: %s" % duration)
    if int(comment_secs) >= int(duration):
        LOGGER.info("Comment seconds was greater...skipping!")
        return 
    elif comment_secs < 2:
        comment_secs = 0
    else:
        comment_secs -= 2

    final_url = "{0}&t={1}".format(new_url, comment_secs)
    LOGGER.info("Final url: %s" % final_url)

    reply = build_reply(time, final_url)
    new_comment = comment.reply(reply)

    print "Successfully replied to %s" % comment.permalink
    LOGGER.info("New comment link: %s" % new_comment.permalink)
    LOGGER.info("SUCCESSFULLY REPLIED!")

    return new_comment

def log_comment(comment):
    """ Logging helper """
    submission = comment.submission

    LOGGER.info("")
    LOGGER.info("")
    LOGGER.info("Matched ==> %s" % TIME_REGEX.match(comment.body).group(1))
    LOGGER.info("Comment body: %s" % comment.body)
    LOGGER.info("Comment author: %s" % comment.author.name)
    LOGGER.info("Comment upvotes: %s" % comment.ups)
    LOGGER.info("Comment id: %s" % comment.id)
    LOGGER.info("Comment permalink: %s" % comment.permalink)
    LOGGER.info("Comment created: %s" % time.ctime(comment.created_utc))
    LOGGER.info("Comment is Root: %s" % comment.is_root)
    LOGGER.info("Submission id: %s" % submission.id)
    LOGGER.info("Submission title: %s" % submission.title)
    LOGGER.info("Submission created: %s" %  time.ctime(submission.created_utc))
    LOGGER.info("Original url: %s" % submission.url)

def get_handled():
    """ Either returns a new deque or the one from disk if it exists """
    try:
        with open(HANDLED_FILE, 'rb') as f:
            print "Unpickle!"
            return pickle.load(f)
    except IOError as e:
        LOGGER.info("Pickle file does not exist yet")
        return deque(maxlen=200)

# Add in better argument handling
def main():
    print "Started"
    LOGGER.info("lazyassbot has started!")
    login()
    handled = get_handled() 
    print "Running"
    while True:
        try:
            comments = get_comments(subreddit_=sys.argv[1])
            for comment in comments:
                if comment.id not in handled:
                    handled.append(comment.id)
                    handle_comment(comment)
            time.sleep(30)
        except praw.errors.RateLimitExceeded as e:
            print "RateLimiteExceeded...sleeping for %s" % e.sleep_time
            LOGGER.info("RateLimitExceeded...sleeping for %s" % e.sleep_time)
            time.sleep(e.sleep_time)
        except (requests.ConnectionError, requests.HTTPError) as e:
            LOGGER.info("")
            LOGGER.info("!!!!! requests connection/Http Error was raised")
            print "requests network error...going to sleep for 3 minutes"
            time.sleep(180) # wait 3 minutes on error
        except (HTTPError, URLError) as e:
            LOGGER.info("")
            LOGGER.info("!!!!! urllib2 HTTP/URL Error was raised")
            print "urllib2 network error...going to sleep for 3 minutes"
            time.sleep(180) # wait 3 minutes on error
        except KeyboardInterrupt as e:
            LOGGER.info("")
            LOGGER.info("!!!!! lazyassbot has been interrupted")
            break

    # Save the current deque
    with open(HANDLED_FILE, 'wb') as f:
        print "Pickle!"
        pickle.dump(handled, f)

    print "Stopped"

if __name__ == '__main__':
    sys.exit(main())
