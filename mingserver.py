#coding= utf-8

import os
import sys
import logging
import time
import datetime
import json
import re 
import subprocess

import web
from jinja2 import Environment,PackageLoader

from ming import Article, ArticleManager,OUTPUT_DIR,DOCUMENTS_DIR,THEMES_DIR,SiteMaker

# 当前 ming 的执行目录
MING_DIR = os.path.dirname(os.path.realpath(__file__) if os.path.islink(__file__) else __file__)

# themes
THEMES_PATH = os.path.join('.',THEMES_DIR)
# output
OUTPUT_PATH = os.path.join('.',OUTPUT_DIR)
# static
STATIC_PATHA  = os.path.join('.','static') #tornado setting static_path


class TestPage:
    def GET(self,name = None):
        print 'web.py'
        return 'web.py:%s'%(name,)

class ThemesStaticPage:
    '''用于访问模板中的引用文件'''
    def GET(self,filename):
        static_filename = os.path.join(THEMES_PATH,filename)
        f = open(static_filename,'r')
        data = f.read()
        f.close()
        return data

# output
class SitePage:
    def GET(self,name, ext):
        '''输出的文件'''
        filename = os.path.join(OUTPUT_PATH,'%s%s'%(name,ext))
        if not os.path.exists(filename):
            return 'not found:%s'%(filename,)
        f = open(filename)
        s = f.read()
        f.close()
        return s

# preview
class PreviewArticlePage:
    '''/preview/<article-filename.md>'''
    def GET(self,name,ext):
        '''用于预览页面'''
        filename = name + ext
        article = None
        if ext in ['.md','.markdown']:
            article = ArticleManager.sharedManager().article_for_filename(filename)
        else:
            article = ArticleManager.sharedManager().article_for_link(filename)
        if article:
            html = article.render_page()
            return html

class PreviewArchivePage:
    '''/preview/archive.html'''
    def GET(self):
        site_maker = SiteMaker()
        s = site_maker.render_archive()
        return s

class PreviewIndexPage:
    '''/preview/index.html'''
    def GET(self):
        print 'index'
        article = ArticleManager.sharedManager().top_article()
        if article:
            theme_index_filename = os.path.join(THEMES_PATH,article.site_theme,
                    'index.html')
            if os.path.exists(theme_index_filename):
                html = article.render_page_for_index()
            else:
                html = article.render_page()
            return html
        else:
            return 'no index'

class PreviewAboutPage:
    '''/preview/about.html'''
    def GET(self):
        article = ArticleManager.sharedManager().article_for_filename('_about.md')
        if article:
            html = article.render_page()
            return html
        else:
            return 'no about page'

class PreviewFeedsPage:
    '''/preview/atom.xml'''
    def GET(self):
        site_maker = SiteMaker()
        xml = site_maker.render_atom()
        return xml

routers = (
        #'/(.*)','TestPage',
        r'/_themes/(.*)', ThemesStaticPage,
        r'/preview/index.html',PreviewIndexPage,
        r'/preview/archive.html', PreviewArchivePage,
        r'/preview/about.html', PreviewAboutPage,
        r'/preview/atom.xml',PreviewFeedsPage,
        r'/preview/(.*)(.html|.md|.htm|.markdown)', PreviewArticlePage,
        r'/(.*)(.html|.xml)',SitePage,
        )

def run():
    app = web.application(routers, globals())
    app.run()

if __name__ == "__main__":
    run() 
   

