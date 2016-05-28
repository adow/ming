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
MING_DIR = os.path.realpath(__file__) if os.path.islink(__file__) else __file__

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

class ArticlePreviewPage:
    def GET(self,filename):
        '''用于预览页面'''
        article = ArticleManager.sharedManager().article_for_filename(filename) 
        if article:
            html = article.render_page()
            return html



routers = (
        #'/(.*)','TestPage',
        r'/(.*)(.html|.xml)',SitePage,
        r'/_themes/(.*)', ThemesStaticPage,
        r'/preview/(.*)', ArticlePreviewPage,
        )

def run():
    app = web.application(routers, globals())
    app.run()

if __name__ == "__main__":
    run() 
   

