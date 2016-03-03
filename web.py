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

from ming import Article,generate_article_table, OUTPUT_DIR,DOCUMENTS_DIR,THEMES_DIR

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
          <img src="/_themes/default/images/article-image.png" alt=""/>
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

article_table = {}
def update_article_table():
    global article_table 
    article_table = generate_article_table()
    print 'update_article_table'

class WriterArchive(tornado.web.RequestHandler):
    def get(self):
        update_article_table()
        print article_table
        s = json.dumps(article_table)
        self.write(s)

class WriterHtml(tornado.web.RequestHandler):
    def get(self,name):
        if not article_table:
            update_article_table()
        link = name + '.html'
        article = article_table.get(link)
        if not article:
            self.write('article not found: %s'%(link,))
            return
        # 因为这个 article 获取不到内容, 所以要重新取一遍
        _,filename = os.path.split(article.article_filename)
        new_article = Article(filename)
        html = new_article.render_html()
        self.write(html)

class WriterMarkdown(tornado.web.RequestHandler):
    def get(self,name,ext):
        filename = name + ext
        article = Article(filename)
        html = article.render_html()
        self.write(html)

class DefaultPage(tornado.web.RequestHandler):
    def get(self):
        html = '<ul>'
        html += "<li><a href = '/_themes/default/index.html'>Default Theme</a></li>"
        html += "<li><a href = '/writer/archive.html'>/writer/archive.html</a></li>" 
        html += "<li><a href = '/secrecy-swift.html'>SecrecySwift</a></li>"
        html += '</ul>'
        self.write(html)

# 启动 web 服务器
def start_local_server():
    handlers = [
            (r'/',DefaultPage),
            (r'/article/.*',ArticlePage),
            (r'/writer/archive.html',WriterArchive),
            (r'/writer/(.*).html',WriterHtml),
            (r'/writer/(.*)(.md|.markdown)',WriterMarkdown),
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
