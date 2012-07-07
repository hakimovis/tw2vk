#!/usr/bin/env python
# coding: utf-8
from bash_org_ru_parser import BashOrgRuParser
from vk_api import VkontakteApi
import settings
MIN_RATING = 6000
MAX_COUNT = 3

def post_bash_im_to_vk():
    quotes = BashOrgRuParser.new_posts_with_rating_gt(MIN_RATING, MAX_COUNT)
    if not len(quotes):
        print "No new posts"
        return

    api = VkontakteApi( settings.IKITO_VK_LOGIN, settings.IKITO_VK_PASS, debug = False )
    api.app_id = settings.VK_APP_ID
    api.app_secret = settings.VK_APP_SECRET
    posted, failed = 0, 0
    for one in quotes[:MAX_COUNT]:
        post_id = api.wall_post(one.text_with_link, post = True)
        if post_id.__class__ == int or post_id.isdigit(): posted += 1
        else: failed += 1
    print "Posted: %i, failed: %i"%(posted, failed)


if __name__ == '__main__':
    post_bash_im_to_vk()
