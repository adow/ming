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

from ming import Article, OUTPUT_DIR,DOCUMENTS_DIR,THEMES_DIR

# themes
THEMES_PATH = os.path.join(os.path.dirname(__file__),THEMES_DIR)
# output
OUTPUT_PATH = os.path.join(os.path.dirname(__file__),OUTPUT_DIR)
# static
STATIC_PATHA  = os.path.join(os.path.dirname(__file__),'static') #tornado setting static_path

class ArticlePage(tornado.web.RequestHandler):
    '''文章预览'''
    def get(self):
        #self.write('Article') 
        url = self.request.path
        (_,filename) = os.path.split(url)
        #self.write(filename)
        print filename
        article = Article(filename)
        html = article.render_html()
        self.write(html)

class ThemePage(tornado.web.RequestHandler):
    '''模板预览页面'''
    def get(self):
        url = self.request.path
        (theme_dir,theme_filename) = os.path.split(url)
        print theme_dir
        print theme_filename
        d_theme,d_name = map(lambda s:s.replace('/',''),
                os.path.split(theme_dir))
        print d_theme
        print d_name
        env = Environment(loader = PackageLoader(d_theme,d_name))
        theme = env.get_template(theme_filename)
        article_html = '''
        <p>
          In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p> 
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
          <blockquote>
          In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </blockquote>
          <h2>
            Subtitle for Codes 
          </h2>
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
          <img src="/themes/default/images/article-image.png" alt=""/>
          <p>
    In hac habitasse platea dictumst. Vivamus adipiscing fermentum quam volutpat aliquam. Integer et elit eget elit facilisis tristique. Nam vel iaculis mauris. Sed ullamcorper tellus erat, non ultrices sem tincidunt euismod. Fusce rhoncus porttitor velit, eu bibendum nibh aliquet vel. Fusce lorem leo, vehicula at nibh quis, facilisis accumsan turpis.
          </p>
        '''
        html = theme.render(theme_dir = theme_dir, content = article_html,
                article_config = {})
        self.write(html)

class SitePage(tornado.web.RequestHandler):
    def get(self,name):
        filename = os.path.join(OUTPUT_PATH,'%s.html'%(name,))
        if not os.path.exists(filename):
            self.write('%s not found'%(filename,))
            return
        f = open(filename)
        s = f.read()
        f.close()
        self.write(s)


# 启动 web 服务器
def start_local_server():
    handlers = [
            (r'/article/.*',ArticlePage),
            (r'/_themes/.*.html',ThemePage),
            (r'/_themes/(.*)',tornado.web.StaticFileHandler,{'path':THEMES_PATH}),
            (r'/(.*).html',SitePage),
            ]

    port = 8002

    # tornado
    DEBUG = True # tornado setting debug
    COOKIE_SECRET = "mingsecret" # tornado setting cookie_secret
    TORNADO_SETTING = {
        "static_path":STATIC_PATHA,
        'debug':DEBUG,
        'cookie_secret':COOKIE_SECRET,
    }
    
    # start
    define("port", default=port, help="run on the given port", type=int)
    tornado.options.parse_command_line()
    welcome = 'MING Local Server Starts'
    print welcome 
    logging.info('URL-ROUTERS:\n' + '\n'.join([h[0] for h in handlers]))
    logging.info(welcome)
    logging.info('port:%s'%(options.port))
    AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
    application = tornado.web.Application(handlers,**(TORNADO_SETTING))
    server = tornado.httpserver.HTTPServer(application,xheaders = True)
    server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    start_web()
