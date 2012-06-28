#!/usr/bin/env python
# coding: utf-8

import os
from vk_api import VkontakteApi
from tw_api import get_timeline
from utils import http_request, exec_command, expand_urls_in
from datetime import datetime
from time import sleep
import settings

def post_tweets_to_vk(tweets, group_tweets = False, limit = 2, skip_links = True):
    posted, failed = [], []
    if len(tweets):
        api = VkontakteApi( settings.IKITO_VK_LOGIN, settings.IKITO_VK_PASS, debug = False )
        api.app_id = settings.VK_APP_ID
        api.app_secret = settings.VK_APP_SECRET
        if group_tweets:
            ids = sorted(tweets.keys())
            msg = "---\n".join([tweets[tw_id] for tw_id in ids])
            post_id = api.wall_post(msg, post = True)
            try: 
                if int(post_id): posted = ids
            except: 
                failed = ids
        else:
            for tw_id in sorted(tweets.keys()[0:limit]):
                msg = tweets[tw_id]
                msg = expand_urls_in(msg)
                # print "posting to vk: %s"%msg
                msg = msg.replace(" @", " ")
                post_id = api.wall_post(msg, post = True)
                sleep(2)
                if skip_links and 'http::':
                    posted.append(tw_id)
                else:
                    try: 
                        if int(post_id): posted.append(tw_id)
                    except: failed.append(tw_id)

    return posted, failed

def tweets_file_name(user):
    return "%s_tweets.txt"%user

def get_last_tweets(user):
    filename = tweets_file_name(user)
    if not os.path.isfile(filename):
        print "no file %s"%filename
        return []
    command = 'tail -n 30 ./%s'%filename
    lines = exec_command(command, output_as = 'array')
    result = []
    for line in lines:
        line = line.strip()
        if line and ":" in line:
            tweet_id = line.split(":")[0]
            if tweet_id: result.append( int(tweet_id) )
    return result

def save_posted(tweets, filename):
    f = open( filename, 'a')
    for tw_id in sorted(tweets.keys()):
        text = tweets[tw_id].replace("\n", "")
        line = u"{0}: {1}\n".format(tw_id, text)
        f.write(line.encode('utf-8'))
    f.close()

def log_to_file(msg, filename):
    f = open(filename, 'a')
    f.write( "%s: %s"%(datetime.today(), msg) )
    f.close

def tw2vk(user = None):
    user = user or settings.TWITTER_LOGIN

    timeline = get_timeline('hakimovis', prefix = "tw:")
    tweeted_ids = get_last_tweets(user)
    if not tweeted_ids:
        save_posted(timeline, tweets_file_name(user))
        return

    too_old_id = min(tweeted_ids)
    to_post = {}
    for tw_id in sorted(timeline.keys()):
        text = timeline[tw_id]
        if tw_id > too_old_id and (not tw_id in tweeted_ids):
            to_post[tw_id] =text

    posted = {}
    if to_post: 
        posted_ids, failed_ids = post_tweets_to_vk(to_post, group_tweets = False, limit = 10)
        for tw_id in posted_ids:
            posted[tw_id] = timeline[tw_id]
        if failed_ids: 
            log_to_file(failed_ids, '%s_failed_tweets.txt'%user)
    if posted:
        save_posted(posted, tweets_file_name(user))

    print "posted: %s"%posted
    print "NOT posted: %s"%failed_ids


if __name__ == '__main__':
    tw2vk()
