#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

# todo
# Extant,S02E00
# TheNightShift,S02E00
# Tyrant,S02E00
# DaVinci,S03E00
# InsideNo9,S02E00
# GameOfThrones,S05E00
# HouseOfCards,S03E00
# Helix,S02E00
# Hostages,S01E08
# Vikings,S01E09
# Hunted,S02E00
# BlackMirror,S03E00
# Sinbad,S02E00


# Need to install pywin32: http://sourceforge.net/projects/pywin32

import json
from HTMLParser import HTMLParser
import urllib2
import re
import os
from httplib import BadStatusLine
import time
import sys
import socket
import multiprocessing
from multiprocessing import Pool
import win32clipboard
import collections

RESOURCES_INDEX_URL = 0
RESOURCES_INDEX_PATTERN = 1

UPDATE_INDEX_SEASONEPISODE = 0
UPDATE_INDEX_LINK = 1

LINK_INDEX_EPISODE = 0
LINK_INDEX_LINK = 1
# multi-processing
mp = True

host_name = socket.gethostname()
file_history = ''


class Parser(HTMLParser):
    def __init__(self, pattern, episode):
        HTMLParser.__init__(self)
        self.pattern = pattern
        self.episode = episode
        self.is_a = False
        self.matched = False
        self.href = ''
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.is_a = True
            for (name, value) in attrs:
                if name == 'href':
                    self.href = value
                    break

    def handle_endtag(self, tag):
        if tag == 'a':
            self.is_a = False

    def handle_data(self, data):
        if self.is_a:
            match = re.search(self.pattern, data)
            # all the good links are continuous. Exit using an exception as close() seems not work.
            if self.matched and not match:
                raise
            if match:
                self.matched = True
                episode_tmp = int(match.group(1))
                if episode_tmp > self.episode:
                    self.links.append([episode_tmp, self.href])


def setup():
    global file_history

    if host_name == 'gyagp_parent':
        file_history = 'history-parent.txt'
    else:
        file_history = 'history.txt'


def get_time():
    return time.strftime('%Y-%m-%d %X', time.localtime(time.time()))


def copy_text_to_clipboard(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()


def check_update():
    # check each movie
    f = file('config.json', 'r+')
    config = json.load(f, object_pairs_hook=collections.OrderedDict)
    sites = config['sites']
    movies = config['movies']
    count_movie = len(movies)
    count_process = min(multiprocessing.cpu_count(), count_movie)
    pool = Pool(processes=count_process)
    outputs = []
    for movie in movies:
        print 'Checking ' + movie
        if mp:
            outputs.append(pool.apply_async(check_update_one, (sites, movies, movie,)))
        else:
            check_update_one(sites, movies, movie)

    if mp:
        pool.close()
        pool.join()

    # set updates
    updates = {}
    for output in outputs:
        output_tmp = output.get()
        movie = output_tmp.keys()[0]
        updates_one = output_tmp[movie]
        if len(updates_one) == 0:
            print movie + ' has no update'
        else:
            print movie + ' has an update'
            updates[movie] = updates_one

    # set lines for history.txt and links for clipboard
    lines = []
    links = []
    if not len(updates):
        print '== Overall there is no update =='
        lines.append('== There is no update at ' + get_time() + ' ==')
    else:
        print '== Overall there is an update =='
        lines.append('== There is an update at ' + get_time() + ' ==')
        for movie in updates:
            movies[movie]['episode'] = int(updates[movie][-1][UPDATE_INDEX_SEASONEPISODE][-2:])
            for update_tmp in updates[movie]:
                lines.append(movie + ',' + update_tmp[UPDATE_INDEX_SEASONEPISODE] + ',' + update_tmp[UPDATE_INDEX_LINK])
                links.append(update_tmp[UPDATE_INDEX_LINK])

    # update config
    if len(updates):
        f.seek(0)
        json.dump(config, f, indent=4)
    f.close()

    # update history
    os.chdir(sys.path[0])
    f = open(file_history, 'a')
    for line in lines:
        f.write(line + '\n')
    f.close()

    raw_input('Press <enter>')
    copy_text_to_clipboard('\n'.join(links))


def check_update_one(sites, movies, movie):
    updates_one = []
    if movies[movie]['state'] == 'active':
        season = movies[movie]['season']
        episode = movies[movie]['episode']
        resources = movies[movie]['resources']
        for site in resources:
            url = sites[site] + '/' + resources[site][RESOURCES_INDEX_URL]

            try:
                u = urllib2.urlopen(url)
            except BadStatusLine:
                print 'Check failed'
                continue
            # ignore the malformed codec
            html = u.read().decode('utf-8', 'ignore')
            parser = Parser(resources[site][RESOURCES_INDEX_PATTERN], episode)
            # may result in malformed start tag
            try:
                parser.feed(html)
            except:
                pass
            for link in parser.links:
                updates_one.append(['S%02dE%02d' % (season, link[LINK_INDEX_EPISODE]), link[LINK_INDEX_LINK]])
    return {movie: updates_one}


if __name__ == '__main__':
    setup()
    check_update()
