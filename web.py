#coding= utf-8

import os
import sys
import logging
import time
import datetime
import json
import re
import subprocess

import tornado.ioloop
import tornado.web
from tornado.options import define,options
from tornado.httpclient import *
import tornado.httpserver
from jinja2 import Environment,PackageLoader

from ming import Article,OUTPUT_DIR,DOCUMENTS_DIR,THEMES_DIR,SiteMaker

# themes
THEMES_PATH = os.path.join(os.path.dirname(__file__),THEMES_DIR)
# output
OUTPUT_PATH = os.path.join(os.path.dirname(__file__),OUTPUT_DIR)
# static
STATIC_PATHA  = os.path.join(os.path.dirname(__file__),'static') #tornado setting static_path

class ArticlePage(tornado.web.RequestHandler):
    '''文章预览'''
    def get(self):
        url = self.request.path
        (_,filename) = os.path.split(url)
        print filename
        article = Article(filename)
        html = article.render_html()
        self.write(html)

# themes
class ThemeArticle(tornado.web.RequestHandler):
    '''模板预览页面'''
    def get(self,theme_name):
        article = Article('_ming.md')
        article.theme = theme_name
        html = article.render_html()
        self.write(html)

class ThemeAbout(tornado.web.RequestHandler):
    def get(self,theme_name):
        article = Article('_about.md')
        article.theme = theme_name
        html = article.render_html()
        self.write(html)

class ThemeArchive(tornado.web.RequestHandler):
    def get(self,theme_name = 'default'):
        #self.write('archive')
        site_maker = SiteMaker()
        site_maker.themes = theme_name
        html = site_maker.render_archive()
        self.write(html)

# site
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

# cli
class CliPage (tornado.web.RequestHandler):
    def get(self,cmd = 'help'):
        script = 'python ming.py %s'%(cmd,)
        self.write(script)
        cli = script.split(' ')
        subprocess.call(cli)

# writer
class WriterArchive(tornado.web.RequestHandler):
    def get(self):
        site_maker = SiteMaker()
        s = site_maker.render_archive()
        self.write(s)

class WriterArticle(tornado.web.RequestHandler):
    def get(self,name,ext):
        filename = name + ext
        article = None
        if ext in ['.md','.markdown']:
            article = Article(filename)
        else:
            site_maker = SiteMaker()
            article = site_maker.article_table[filename]
        if article:
            html = article.render_html()
            self.write(html)

class WriterIndex(tornado.web.RequestHandler):
    def get(self):
        site_maker = SiteMaker()
        article = site_maker.index_article()
        html = article.render_html()
        self.write(html)

class WriterAbout(tornado.web.RequestHandler):
    def get(self):
        article = Article('_about.md')
        html = article.render_html()
        self.write(html)

class WriterDash(tornado.web.RequestHandler):
    def get(self):
        html = '<h1>MING LocalServer</h1>'
        html += '<h2>Output Site</h2>'
        html += '<ul>'
        html += "<li><a href = '/index.html'>首页</a></li>"
        html += "<li><a href = '/archive.html'>归档</a></li>"
        html += "<li><a href = '/about.html'>关于</a></li>"
        html += '</ul>'
        html += '<h2>Site Maker</h2>'
        html += '<ul>'
        html += "<li><a href = '/_cli/make-site'>Make Site</a></li>"
        html += "<li><a href = '/_cli/make-archive'>Make Archive</a></li>"
        html += "<li><a href = '/_cli/make-about'>Make About</a></li>"
        html += '</ul>'
        html += '<h2>Dynamic Preview</h2>'
        html += '<ul>'
        html += "<li><a href = '/_writer/index.html'>首页</a></li>"
        html += "<li><a href = '/_writer/archive.html'>归档</a></li>"
        html += "<li><a href = '/_writer/about.html'>关于</a></li>"
        html += '</ul>'
        html += '<h3>Article List</h3>'
        html += '<ul>'
        site_maker = SiteMaker()
        for link in site_maker.link_list:
            link = link.encode('utf-8')
            article = site_maker.article_table[link]
            _,filename = os.path.split(article._article_filepath)
            html += "<li><a href = '%s'>%s</a>:%s</li>"%(filename,filename,article.article_title.encode('utf-8'),)
        html += '</ul>'
        html += '<h2>Themes Development</h2>'
        html += '<ul>'
        html += "<li><a>Default Theme</a></li>"
        html += '<ul>'
        html += "<li><a href = '/_themes/default/index.html'>index</a></li>"
        html += "<li><a href = '/_themes/default/article.html'>article</a></li>"
        html += "<li><a href = '/_themes/default/about.html'>about</a></li>"
        html += "<li><a href = '/_themes/default/archive.html'>archive</a></li>"
        html += '</ul>'
        html += '</ul>'
        self.write(html)

# 启动 web 服务器
def start_local_server():
    handlers = [
            (r'/article/.*',ArticlePage),
            (r'/_writer/index.html',WriterIndex),
            (r'/_writer/archive.html',WriterArchive),
            (r'/_writer/about.html',WriterAbout),
            (r'/_writer/(.*)(.md|.markdown|.html|.htm)',WriterArticle),
            (r'/_writer/',WriterDash),
            (r'/_cli/(.*)',CliPage),
            (r'/_themes/(.*)/article.html',ThemeArticle),
            (r'/_themes/(.*)/index.html',ThemeArticle),
            (r'/_themes/(.*)/about.html',ThemeAbout),
            (r'/_themes/(.*)/archive.html',ThemeArchive),
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
