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
import time

from jinja2 import Environment,PackageLoader
from mikoto.libs.text import render


OUTPUT_DIR = '_output'
DOCUMENTS_DIR = '_documents'
THEMES_DIR = '_themes'

# config
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

class Config(Modal):
    '''配置信息'''
    def __init__(self, row = None, **args):
        '''会载入全站的统一配置'''
        f = open('./site.json')
        s = f.read()
        f.close()
        d = json.loads(s)
        super(Config,self).__init__(row = d, **args)

    def load_article_config(self,article_config_filename):
        '''会合并文章的配置文件'''
        d = {}
        if os.path.exists(article_config_filename):
            f = open(article_config_filename)
            s = f.read()
            f.close()
            d = json.loads(s)
        for (k,v) in d.items():
            self[k] = v

class Article(Modal):
    '''文章'''
    def __init__(self,article_filename):
        super(Article,self).__init__()
        self.article_filename = os.path.join(DOCUMENTS_DIR,article_filename)
        self.article_config = Config()
        self.markdown = ''
        self.markdown_without_title = ''
        self.article_mtime = 0
        self._load_article_config() # 先读取配置文件
        self._parse_markdown_from_article() # 解析内容

    def _parse_markdown_from_article(self):
        ''' 解析 markdown '''
        if not os.path.exists(self.article_filename):
            raise Exception('Article not found:%s'%(self.article_filename,))
        self.article_mtime = os.stat(self.article_filename).st_mtime #修改时间
        f = open(self.article_filename)
        self.markdown = f.read()
        f.close()
        self.markdown_without_title = self.markdown
        lines = self.markdown_without_title.split('\n')
        if lines:
            first_line = lines[0]
            if first_line.startswith('#'):
                # 配置中没有标题的话就从文章里取一个
                if not self.article_config.article_title:
                    title_from_markdown = first_line[1:].strip()
                    self.article_config.article_title = title_from_markdown
                # 输出到 html 的时候要去掉标题
                if len(lines):
                    self.markdown_without_title = '\n'.join(lines[1:])
        # 如果没有标题就用默认的
        if not self.article_config.article_title:
            self.article_config.article_title = 'Untitled'
        # 获取文章的链接
        if not self.article_config.article_link:
            self.article_config.article_link = self.article_config.article_title + '.html'

    def _load_article_config(self):
        ''' 读取配置文件'''
        article_config_filename = self.article_filename + '.json'
        self.article_config.load_article_config(article_config_filename)

    def render_html(self):
        '''使用模板渲染到 html'''
        article_html = render(self.markdown_without_title.decode('utf-8'))
        theme_name = self.article_config.get('themes','default')
        env=Environment(loader=PackageLoader(THEMES_DIR,theme_name))
        theme = env.get_template('article.html')
        theme_dir = os.path.join('/',THEMES_DIR,theme_name) 
        html = theme.render(theme_dir = theme_dir, 
                content = article_html , 
                article_config = self.article_config)
        print self.article_config
        return html

    def generate_html(self):
        '''输出到 html 文件'''
        html = self.render_html()
        if not self.article_config.article_link:
            raise Exception('No Article Link')
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR,
                self.article_config.article_link)
        print output_filename
        f = open(output_filename,'w')
        f.write(html.encode('utf-8'))
        f.close()

def generate_article_table():
    '''获取全部的文章列表'''
    _t_start = time.time()
    folder = os.path.join(os.path.dirname(__file__),DOCUMENTS_DIR)
    name_list = os.listdir(folder)
    file_name_list = [os.path.join(folder,f) for f in name_list if os.path.splitext(f)[-1].upper() in ['.MD','.MARKDOWN']]
    file_name_list.sort(lambda f1,f2: os.stat(f2).st_mtime - os.stat(f1).st_mtime)
    #print file_name_list
    article_table = {}
    for f in file_name_list:
        _,filename = os.path.split(f)
        article = Article(filename)
        #del article['markdown']
        #del article['markdown_without_title']
        link = article.article_config.article_link
        article_table[link] = article
    _t_end = time.time()
    print (_t_end - _t_start)
    #print article_table
    return article_table

def prepare_articles():
    '''返回 url 和文章关联列表，同时返回排序后的链接列表'''
    folder = os.path.join(os.path.dirname(__file__),DOCUMENTS_DIR)
    name_list = os.listdir(folder)
    file_name_list = [os.path.join(folder,f) for f in name_list if os.path.splitext(f)[-1].upper() in ['.MD','.MARKDOWN']]
    file_name_list.sort(lambda f1,f2: os.stat(f2).st_mtime - os.stat(f1).st_mtime)
    article_table = {}
    for f in file_name_list:
        _,filename = os.path.split(f)
        article = Article(filename)
        link = article.article_config.article_link
        article_table[link] = article
    def _cmp(link_1, link_2):
        article_1 = article_table.get(link_1)
        article_2 = article_table.get(link_2)
    link_list = article_table.keys() #TODO: 排序的链接列表
    return (article_table,link_list)

class SiteMaker(object):
    def __init__(self):
        super(SiteMaker,self).__init__()
        self.article_table,self.link_list = prepare_articles() 

    def make_article(self,article_filename):
        _,ext = os.path.splitext(article_filename)
        if not ext:
            article_filename += '.md'
        article = Article(article_filename = article_filename)
        article.generate_html()

    def make_archive(self):
        html = 'archive.html'
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR, 'archive.html')
        print output_filename
        f = open(output_filename,'w')
        f.write(html)
        f.close()

    def make_index(self):
        top_link = self.link_list[0]
        article = self.article_table[top_link]
        html = article.render_html()
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR, 'index.html')
        print output_filename
        f = open(output_filename,'w')
        f.write(html.encode('utf-8'))
        f.close()

    def make_about(self):
        html = 'about.html'
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR, 'about.html')
        print output_filename
        f = open(output_filename,'w')
        f.write(html)
        f.close()

    def make_site(self):
        self.make_index()
        self.make_about()
        self.make_archive()
        # 依次生成每一篇文章

# cli
def make_article():
    if len(sys.argv) < 3:
        print 'no article specificed' 
        return
    article_filename = sys.argv[2]
    _,ext = os.path.splitext(article_filename)
    if not ext:
        article_filename += '.md'
    article = Article(article_filename = article_filename)
    article.generate_html()

def cli_make_article():
    if len(sys.argv) < 3:
        print 'no article specificed' 
        return
    article_filename = sys.argv[2]
    site_maker = SiteMaker()
    site_maker.make_article(article_filename)

def cli_make_archive():
    site_maker = SiteMaker()
    site_maker.make_archive()

def cli_make_about():
    site_maker = SiteMaker()
    site_maker.make_about()

def cli_make_index():
    site_maker = SiteMaker()
    site_maker.make_index()

def cli_make_site():
    site_maker = SiteMaker()
    site_maker.make_site()

def help():
    print 'ming local-server: start local web server' 
    print 'ming make-article <article-name>: make html'
    print 'ming make-archive: make archive.html'
    print 'ming make-about: make about.html'
    print 'ming make-index: make index.html'
    print 'ming make-site: make all pages'
    print 'ming test: test'

# test
def _test_generate_html():
    filename = 'README.md'
    article = Article(article_filename = filename)
    article.generate_html()

def test():
    _test_generate_html()

# start
if __name__ == '__main__':
    if len(sys.argv) < 2:
        help()
    else:
        cmd = sys.argv[1]
        params = sys.argv[2:] if len(sys.argv) > 2 else []
        from web import start_local_server 
        {'local-server':start_local_server,
            'make-article':cli_make_article,
            'make-archive':cli_make_archive,
            'make-about':cli_make_about,
            'make-index': cli_make_index,
            'make-site': cli_make_site,
            'test':test}.get(cmd,help)()
