#!/usr/bin/env python
# coding: utf-8
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
from html2text import html2text
from utils import exec_command
import os

BASE_URL = 'http://bash.im'
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
POSTED_IDS_PATH = os.path.join(ABS_PATH, 'bash_im_posted.txt')

class BashOrgRuParser():
    def __init__(self):
        self.page = self.load_page()
        self.quotes = []
        self.max_id = 0

    def load_page(self):
        return urlopen(BASE_URL).read()

    def get_posts(self):
        print "Loading page %s"%BASE_URL
        page = self.load_page()
        print "Parsing quotes"
        soup = BeautifulSoup(page)
        raw_quotes = soup.findAll('div', {'class': 'quote'})
        self.quotes = []
        for one in raw_quotes:
            quote = self.parse_quote(one)
            if quote: self.quotes.append(quote)
        print "Parsed %i quotes"%(len(self.quotes))
        return self.quotes

    def parse_quote(self, quote_html):
        post_dict = {}

        text_block = quote_html.find('div', {'class': 'text'})
        if not text_block: return None
        
        text = ""
        for line in text_block.contents:
            text += unicode(line)

        rating_block = quote_html.find('span', {'class': 'rating'})
        if not rating_block: return None
        post_id = int(rating_block['id'].strip('v'))
        post_dict['text'] = text

        rating = rating_block.string
        if rating.isdigit(): post_dict['rating'] = int(rating)
        else: post_dict['rating'] = 0

        post_dict['id'] = post_id

        if post_id > self.max_id: self.max_id = post_id

        return BashOrgRuPost(post_dict)

    def find_by_id(self, post_id):
        for one in self.quotes:
            if one['id'] == post_id:
                return one

    def with_rating_gt(self, rating, from_id = 0):
        result = []
        for one in self.quotes:
            if one.rating >= rating and one.post_id > from_id:
                result.append(one)
        return result
    
    @classmethod
    def posts_with_rating_gt(cls, rating, from_id = 0):
        if not from_id: from_id = 0
        bash_im = cls()
        bash_im.get_posts()
        return bash_im.with_rating_gt(rating, from_id = from_id), bash_im.max_id
    
    @classmethod
    def new_posts_with_rating_gt(cls, rating, count):
        posted_ids = cls.get_posted_ids()
        quotes, max_id = cls.posts_with_rating_gt(rating)
        new_quotes = []
        f = open(POSTED_IDS_PATH, 'a')
        for one in quotes:
            if not one.post_id in posted_ids:
                new_quotes.append(one)
        for one in new_quotes[:count]:
            to_write = u"{post_id}: {text}\n".format(post_id = one.post_id, text = one.text.replace("\n", r'\n'))
            f.write(to_write.encode('utf-8'))
        f.close()
        return new_quotes

    @classmethod
    def get_posted_ids(cls):
        if not os.path.isfile(POSTED_IDS_PATH):
            print "no file %s"%POSTED_IDS_PATH
            return []
        command = 'tail -n 50 %s'%POSTED_IDS_PATH
        lines = exec_command(command, output_as = 'array')
        result = []
        for line in lines:
            line = line.strip()
            if line and ":" in line:
                post_id = line.split(":")[0]
                if post_id and post_id.isdigit() : result.append( int(post_id) )
        print "posted ids: {0}".format(result)
        return result

class BashOrgRuPost():
    def __init__(self, post_dict):
        self.text = html2text(post_dict['text']).replace("\n\n", r"\n")
        self.text = self.text.replace("\n", " ").replace(r"\n", "\n")
        self.post_id = post_dict['id']
        self.rating = post_dict['rating']
        self.url = "http://bash.im/quote/{0}".format(self.post_id)
        formats = {
            'post_id': self.post_id,
            'rating': self.rating,
            'text': self.text,
            'url': self.url
        }
        self.text_with_link = u"Цитата №{post_id} ({rating}):\n{text}\nЦитатник Рунета {url}".format(**formats)
    def __unicode__(self):
        return self.text_with_link
    def __str__(self):
        return self.__unicode__()

# Just an example ;)
if __name__ == '__main__':
    quotes = BashOrgRuParser.new_posts_with_rating_gt(6000)
    for one in quotes:
        print one.text_with_link
