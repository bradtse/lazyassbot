#!/usr/bin/env python

"""
Simple script that extracts the youtube id's from my log files to be used for
testing purposes.

If you don't need this, then ignore this script.
"""

import os
import re
import HTMLParser

URL_REGEX = re.compile(r'^.*?url: (.*)$', re.IGNORECASE)
YT_REGEX = re.compile('^(?:https?://)?(?:www\.)?(?:youtu\.be/|youtube\.com'
                 '(?:/embed/|/v/|/watch\?v=|/watch\?.+&v=))([\w-]{11})(?:.+)?$')
LOGS_DIR = '../logs/'

unique = []

id_file = open('youtube_id_list.txt', 'wb')

for log in os.listdir(LOGS_DIR):
    file_name = os.path.join(LOGS_DIR, log)
    with open(file_name, 'r') as f:
        for line in f:
            match = URL_REGEX.match(line)
            if match:
                url = HTMLParser.HTMLParser().unescape(match.group(1))
                yt_match = YT_REGEX.match(url)
                if yt_match:
                    id = yt_match.group(1)
                    if id not in unique:
                        unique.append(id)
                        id_file.write(id + "\n")
id_file.close()
