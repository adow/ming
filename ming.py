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

# config
OUTPUT_DIR = 'output'

SITE_CONFIG = {
        'site_name':'ming site',
        'site_title': 'ming title',
        'url':'http://mingpy.com',
        'author':'ming',
        'email':'mingpy@gmail.com',
        'theme':'default',
        }

ARTICLE_CONFIG = copy.deepcopy(SITE_CONFIG)
ARTICLE_CONFIG['title'] = 'Article Title on MING'
ARTICLE_CONFIG['summery'] = 'Summery of this Article'
ARTICLE_CONFIG['category'] = 'ming'
ARTICLE_CONFIG['link'] = 'ming-first-article'
ARTICLE_CONFIG['author'] = 'adow'
ARTICLE_CONFIG['publish_date'] = '2016-02-26'
ARTICLE_CONFIG['theme'] = 'default'
ARTICLE_CONFIG['css'] = {}

print ARTICLE_CONFIG

# make
def parse_article(article_file):
    f = open(article_file)
    markdown = f.read()
    f.close()
    return markdown

def make_html(article_file):
    article_config = load_article_config(article_file) 
    markdown = parse_article(article_file) 
    # title
    title_from_markdown = ''
    lines = markdown.split('\n')
    if lines:
        first_line = lines[0]
        if first_line.startswith('#'):
            title_from_markdown = first_line[1:].strip()
            if len(lines):
                markdown = '\n'.join(lines[1:])
    # html
    content = render(markdown.decode('utf-8'))
    
    # link
    article_link = article_config.get('link')
    # TODO: generate link from title if no link in config 
    if not article_link:
        print 'no article link'
        return
    # title
    if not article_config.get('title') and title_from_markdown:
        article_config['title'] = title_from_markdown
    # theme
    env=Environment(loader=PackageLoader('themes','default'))
    theme = env.get_template('index.html')
    html = theme.render(content = content, article_config = article_config)
    # write html file
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    article_file = os.path.join(OUTPUT_DIR,article_link + '.html')
    f = open(article_file,'w')
    f.write(html.encode('utf-8'))
    f.close()
    # TODO: update archive
    # output
    print html
    print article_config

def load_article_config(article_file):
    article_config = ARTICLE_CONFIG
    config_file = article_file + '.json'
    if not os.path.exists(config_file):
        return article_config
    f = open(config_file)
    config_str = f.read()
    f.close()
    d = json.loads(config_s) if config_str else {}
    for (k,v) in d:
        article_config[k] = v
    return article_config

class Article(object):
    def __init__(self,article_filename):
        super(Article,self).__init__()
        self.article_filename = os.path.join('documents',article_filename)
        self.article_config = {}
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
        for (k,v) in d:
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
                article_config = self.article_config)
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
