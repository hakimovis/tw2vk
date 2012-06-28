#!/usr/bin/env python
# coding: utf-8

from utils import http_request
import simplejson as json

def get_timeline(user, no_replies = True, prefix = None):
    format = "json"
    url = 'https://api.twitter.com/1/statuses/user_timeline.%s?screen_name=%s&include_rts=1'%(format, user);
    response = http_request(url)
    
    try:
        full_timeline = json.loads(response)
    except json.decoder.JSONDecodeError:
        print "Json error for: %s"%response
        return

    tweets = {}
    for one in full_timeline:
        tw_id = one['id']
        text = one['text'].strip()

        if no_replies:
            if one['in_reply_to_user_id']: continue
            if '@' in text[0:2]: continue

        if one.get('retweeted_status', None):
            retweeted = one['retweeted_status']
            text = u"RT @{0}: {1}".format(retweeted['user']['screen_name'], retweeted['text'])
        
        if prefix: text = "%s %s"%(prefix, text)

        tweets[tw_id] = text

    return tweets
