#!/usr/bin/env python
# coding: utf-8
import re
from time import sleep
from utils import http_request, url_params
import memcache
import simplejson as json

class VkontakteApi():

    def __init__(self, login, passwd, debug = False, app_id = None, app_secret = None):
        self.login = login
        self.passwd = passwd
        self.app_code = None
        self.app_id = None
        self.app_secret = None
        self.token = None
        self.debug = debug
        self.cookies_file = "%s_cookies.txt"%self.login
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.user_id = None
        self.scope = 'wall'

    def get_auth_html(self, appid):
        params = {
            'client_id': appid,
            'scope': self.scope,
            'redirect_uri': 'http://api.vkontakte.ru/blank.html',
            'display': 'wap',
            'response_type': 'token'
        }
        param_str = url_params(params)
        # url = "http://oauth.vk.com/authorize?%s"%param_str
        url = "http://api.vk.com/oauth/authorize?%s"%param_str
        html = http_request(url, cookies_file = self.cookies_file, read_headers = True)
        return html

    def parse_form_data(self, html):
        re_inputs = r'<input ([^>]+)'
        inputs = re.findall(re_inputs, html)
        form_data = {}
        for one in inputs:
            one = one.strip()
            key, value = "", ""
            attrs = one.split(" ")
            for attr in attrs:
                attr = attr.replace('"', '')
                if "=" in attr:
                    parts = attr.split("=")
                    attr_name, attr_value = parts
                    if attr_name == 'name':
                        key = attr_value
                    if attr_name == 'value':
                        value = attr_value
            if key: form_data[key] = value
        return form_data

    def parse_form_action(self, html):
        try:
            re_form_tag = r'<form ([^>]+)'
            form_tag = re.search(re_form_tag, html).group(1)
            re_action = r'action="([^"]+)"'
            action = re.search(re_action, form_tag).group(1)
        except AttributeError:
            print "parse_form_action error on html:\n%s"%html
            exit()
        return action

    def fill_auth_data(self, form_data):
        form_data['email'] = self.login
        form_data['pass'] = self.passwd
        return form_data

    def mc_key_for_token(self, app_id, login = None):
        if not login: login = self.login
        key = "vk-app-%s-token-for-%s"%(app_id, login)
        if self.debug: print "mc_key_for_token: %s"%key
        return key

    def parse_token_and_user_id(self, html):
        location_head = "Location: http://api.vk.com/blank.html#"
        rows = html.split("\n")
        token, user_id = None, None
        for one in rows:
            one = one.strip()
            if one.startswith(location_head):
                params = one.replace(location_head, "")
                params = params.split("&")
                for param in params:
                    if param.startswith("access_token="): token = param.replace("access_token=", "")
                    if param.startswith("user_id="): user_id = param.replace("user_id=", "")
        return token, user_id

    def fetch_new_token_for_app(self, app_id):
        # open(self.cookies_file, 'w').close()
        html = self.get_auth_html(app_id) # Получаем форму авторизации
        # print html
        if not "Login success" in html:
            form_action_url = self.parse_form_action(html) # Адрес куда отправлять данные авторизации
            form_data = self.fill_auth_data( self.parse_form_data(html) ) # Заполненные данные формы логина
            sleep(3)
            confirm_form = http_request(form_action_url, post = form_data, cookies_file = self.cookies_file)
            form_action_url = self.parse_form_action(confirm_form)
            sleep(2)
            response = http_request(form_action_url, read_headers = True, cookies_file = self.cookies_file)
        else:
            response = html

        self.app_token, self.user_id = self.parse_token_and_user_id(response)
        # open(self.cookies_file, 'w').close()
        if self.debug: print "caching token: %s"%self.app_token
        self.mc.set(self.mc_key_for_token(app_id, self.login), self.app_token, 60*60*12)
        return self.app_token

    def get_access_token_for_app(self, app_id, app_secret, force_new = False):
        token = self.mc.get( self.mc_key_for_token(app_id, self.login) )
        if self.debug: print "got from cache: %s"%token
        if not token or force_new:
            if self.debug: print "Getting new token"
            token = self.fetch_new_token_for_app(app_id)
        self.token = token
        return token

    def get_token(self):
        if not self.token and self.app_id and self.app_secret:
            self.token = self.get_access_token_for_app(self.app_id, self.app_secret)
        return self.token

    def vk_method(self, method, params = {}, post = False):
        # c57458088a0fe802c56a15e004c54f99a9cc56ac56a35e26d70d459c8ada8da
        # http://api.vk.com/api.php?v=3.0&api_id=1901988&method=getProfiles&format=json&rnd=343&uids=100172&fields=photo%2Csex&sid=10180116c4fd93480439bca47d636d6dd75fac30b851d4312e82ec3523&sig=5be698cf7fa09d30f58b941a4aea0e9b
        for key, param in params.iteritems():
            try: params[key] = param.encode('utf-8')
            except: pass
        if post:
            url = "http://api.vk.com/api.php"
            # params['method'] = method
            params['api_id'] = self.app_id
            params['format'] = 'json'
            params['access_token'] = self.get_token()
            url = "https://api.vkontakte.ru/method/{method}".format(method = method)
            response = http_request(url, post = params, cookies_file = self.cookies_file)
        else:
            url = "https://api.vkontakte.ru/method/{method}?access_token={token}&{param_str}"
            url = url.format(method = method, token = self.get_token(), param_str = url_params(params))
            response = http_request(url)

        try:
            json_data = json.loads(response)
            if json_data.has_key('response'): return json_data['response']
            return json_data
        except json.decoder.JSONDecodeError:
            print "Json error: %s"%response
            return response

    def wall_post(self, message, to_user_id = None, post = True):
        params = {'message': message}
        if to_user_id: params['owner_id'] = to_user_id
        response = self.vk_method('wall.post', params, post = post)
        if response.has_key('post_id'): return response['post_id']
        return response

    def get_user_id(self):
        user_info = self.vk_method('getUserInfo')
        self.user_id = user_info['user_id']
        return self.user_id

    def get_user_settings(self):
        return self.vk_method('getUserSettings')