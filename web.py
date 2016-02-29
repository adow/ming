#coding= utf-8

import os
import sys
import logging
import time
import datetime
import json
import re

import tornado.ioloop
import tornado.web
from tornado.options import define,options
from tornado.httpclient import *
import tornado.httpserver
from jinja2 import Environment,PackageLoader

class ArticlePage(tornado.web.RequestHandler):
    '''文章预览'''
    def get(self):
        self.write('Article') 

class ThemePage(tornado.web.RequestHandler):
    '''模板预览页面'''
    def get(self):
        url = self.request.path
        (template_dir,template_filename) = os.path.split(url)
        print template_dir
        print template_filename
        d_theme,d_name = map(lambda s:s.replace('/',''),
                os.path.split(template_dir))
        print d_theme
        print d_name
        env = Environment(loader = PackageLoader(d_theme,d_name))
        theme = env.get_template(template_filename)
        html = theme.render(template_dir = template_dir)
        self.write(html)

# themes
THEMES_DIR = os.path.join(os.path.dirname(__file__),'themes')

handlers = [
        (r'/article/.*',ArticlePage),
        (r'/themes/.*.html',ThemePage),
        (r'/themes/(.*)',tornado.web.StaticFileHandler,{'path':THEMES_DIR}),
        ]

port = 8002

# tornado
STATIC_NAME = "static/"
STATIC_DIR  = os.path.join(os.path.dirname(__file__),STATIC_NAME) #tornado setting static_path
DEBUG = True # tornado setting debug
COOKIE_SECRET = "mingsecret" # tornado setting cookie_secret
TORNADO_SETTING = {
    "static_path":STATIC_DIR,
    'debug':DEBUG,
    'cookie_secret':COOKIE_SECRET,
}

if __name__ == "__main__":
    define("port", default=port, help="run on the given port", type=int)
    tornado.options.parse_command_line()
    welcome = 'MING Starts'
    print welcome 
    logging.info('URL-ROUTERS:\n' + '\n'.join([h[0] for h in handlers]))
    logging.info(welcome)
    logging.info('port:%s'%(options.port))
    AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
    application = tornado.web.Application(handlers,**(TORNADO_SETTING))
    server = tornado.httpserver.HTTPServer(application,xheaders = True)
    server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
