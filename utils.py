#!/usr/bin/env python
# coding: utf-8
import urllib, re
import subprocess

def exec_command(command, output_as='string'):
    print command
    child = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE) 
    output = child.stdout.read()
    if output_as == 'array':
        return output.split("\n")
    elif output_as == 'string':
        return output.replace("\n", " ")
    return output

def http_request(url, read_headers = False, follow = True, post = None, user_agent = None, cookies_file = 'cookies.txt'):
    if not user_agent: user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6'
    keys = ["-s", "-A '%s'"%user_agent]
    if cookies_file:
        keys.append("-c '{cf}' -b '{cf}'".format(cf = cookies_file))
    if follow: keys.append("-L")
    if read_headers: keys.append("-i")
    if post: keys.append("-X POST -d '%s'"%urllib.urlencode(post))
    keys.append("'%s'"%url)
    command = "curl %s"%(' '.join(keys))
    return exec_command(command, output_as = "raw")

def url_params(params):
    return urllib.urlencode(params)

def get_page(url):
    return urllib.urlopen(url).read()

def expand_url(url):
    lines = exec_command( "curl -I -R -s -m 3 '{0}'".format(url), output_as = 'array' )
    expanded_url = None
    for line in lines:
        head = "Location: "
        if line.startswith(head):
            expanded_url = line.replace(head, "")
            print("expanded_url: {0}".format(expanded_url))
    return expanded_url or url

def expand_urls_in(text):
    url_re = re.compile(r'http:\/\/[a-zA-Z0-9\.\-\/]{6,15}')
    urls = re.findall(url_re, text)
    print("urls: {0}".format(urls))
    if not urls: return text
    for url in urls: text = text.replace(url, expand_url(url))
    return text
