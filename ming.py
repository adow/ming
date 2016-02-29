#!/usr/bin/python
#coding=utf-8
# ming.py
#
# ming

import os
import sys
import getopt
import copy
import json

from jinja2 import Environment,PackageLoader
from mikoto.libs.text import render

OUTPUT_DIR = 'output'
DOCUMENTS_DIR = 'documents'
# config
SITE_CONFIG = {
        'site_name':'ming site',
        'site_title': 'ming title',
        'url':'http://mingpy.com',
        'author':'ming',
        'email':'mingpy@gmail.com',
        'theme':'default',
        }

class Modal(dict):
    def __init__(self,row=None,**args):
        '''row should be type of dict or database.Row'''
        if row and issubclass(row.__class__,dict):
            for k in row:
                v = row[k]
                if isinstance(v,dict) and '__model__' in v:
                    m_c_col = v["__model__"].split('.')
                    m_name = m_c_col[0].encode('utf-8')
                    c_name = m_c_col[1].encode('utf-8')
                    m = sys.modules[m_name]
                    c = getattr(m,c_name)
                    self[k] = c(row = v) 
                else:
                    self[k]=row[k]  
        for k in args:
            self[k]=args[k]

    def __getattr__(self,name):
        try:
            return self[name]
        except:
            return None

    def __setattr__(self,name,value):
        self[name]=value
    
    def __deepcopy__(self,memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k in self:
            v = self[k]
            setattr(result,k,copy.deepcopy(v,memo))
        return result

class SiteConfig(Modal):
    def __init__(self,row = None, **args):
        super(SiteConfig,self).__init__(row = row, **args)

    @classmethod
    def localConfig(CLS):
        config_filename = './site.json'
        f = open(config_filename)
        s = f.read()
        f.close()
        d = json.loads(s)
        config = SiteConfig(row = d)
        return config

class Article(object):
    def __init__(self,article_filename):
        super(Article,self).__init__()
        self.article_filename = os.path.join('documents',article_filename)
        self.site_config = SiteConfig.localConfig()
        self.article_config = copy.deepcopy(self.site_config)
        self.markdown_raw = ''
        self.markdown = ''
        self.title_from_markdown = ''
        self.article_html = ''

    def _parse_markdown_from_article(self):
        ''' 解析 markdown '''
        if not os.path.exists(self.article_filename):
            raise Exception('Article not found:%s'%(self.article_filename,))
        f = open(self.article_filename)
        self.markdown_raw = f.read()
        f.close()
        self.markdown = self.markdown_raw
        lines = self.markdown.split('\n')
        if lines:
            first_line = lines[0]
            if first_line.startswith('#'):
                self.title_from_markdown = first_line[1:].strip()
                if len(lines):
                    self.markdown = '\n'.join(lines[1:])
        self.article_html = render(self.markdown.decode('utf-8'))

    def _load_article_config(self):
        ''' 读取配置文件'''
        article_config_filename = self.article_filename + '.json'
        if not os.path.exists(article_config_filename):
            return
        f = open(article_config_filename)
        s = f.read()
        f.close()
        d = json.loads(s) if s else {}
        for (k,v) in d.items():
            self.article_config[k] = v 

    def render_html(self):
        self._parse_markdown_from_article()
        self._load_article_config()
        if not self.article_config.get('title') and self.title_from_markdown:
            self.article_config['title'] = self.title_from_markdown
        theme_name = self.article_config.get('themes','default')
        env=Environment(loader=PackageLoader('themes',theme_name))
        theme = env.get_template('index.html')
        theme_dir = os.path.join('/','themes',theme_name) 
        html = theme.render(theme_dir = theme_dir, 
                content = self.article_html , 
                article_config = self.article_config,
                site_config = self.site_config)
        return html

# test
def _test_parse_article():
    article_file = 'documents/README.md'
    parse_article(article_file)

def _test_make_html():
    article_file = 'documents/README.md'
    make_html(article_file)

if __name__ == '__main__':
    #_test_parse_article()
    _test_make_html()
