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
import re
import shutil
from datetime import datetime,date, tzinfo,timedelta

from jinja2 import Environment,PackageLoader
from mikoto.libs.text import render
from vendor import rfeed
from feedgen.feed import FeedGenerator

OUTPUT_DIR = './_output' 
DOCUMENTS_DIR = './_documents' 
THEMES_DIR = './_themes' 

#time
def now():
    '''现在时间'''
    return time.time()

def date_to_string(t=now()):
    '''日期转换成字符串 yyyy-MM-dd'''
    TIMEFORMAT="%Y-%m-%d"
    return time.strftime(TIMEFORMAT,time.localtime(t))

def string_to_time_float(string):
    '''字符串转时间'''
    if string is None or string =='':
        return 0
    if ':' not in string:
        string+=" 00:00:00"
    TIMEFORMAT="%Y-%m-%d %H:%M:%S"
    t=time.strptime(string,TIMEFORMAT)
    return time.mktime(t)

def string_to_date_float(string):
    '''字符串转日期'''
    TIMEFORMAT="%Y-%m-%d"
    t=time.strptime(string,TIMEFORMAT)
    return time.mktime(t)

class UTC(tzinfo):
    """UTC"""
    def __init__(self,offset = 0):
        self._offset = offset

    def utcoffset(self, dt):
        return timedelta(hours=self._offset)

    def tzname(self, dt):
        return "UTC +%s" % self._offset

    def dst(self, dt):
        return timedelta(hours=self._offset)

# modal
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

# config
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

# Article
class Article(Modal):
    def __init__(self,article_filename):
        super(Article,self).__init__() 
        self._article_filename = article_filename 
        self._article_filepath = os.path.join(DOCUMENTS_DIR,article_filename)
        self._article_config_filepath = self._article_filepath + '.json'
        #print 'article_filename:%s'%(self._article_filename,)
        #print 'article_filepath:%s'%(self._article_filepath,)
        #print 'article_config_filepath:%s'%(self._article_config_filepath,)
        self._markdown = ''
        self._markdown_without_title = ''
        self._mtime = 0
        self._sort_value = 0 # 这个值用于列表排序, 他从 article_publish_date 中获取，如果没有，就是文章的修改时间
        self._load_config()
        self._parse_markdown()

    def _load_config(self):
        '''加载配置文件'''
        config = Config()
        config.load_article_config(self._article_config_filepath)
        for (k,v) in config.items():
            self[k] = v

    def _parse_markdown(self):
        if not os.path.exists(self._article_filepath):
            print 'not found:%s'%(self._article_filepath,)
            return
        self._mtime = os.stat(self._article_filepath).st_mtime
        self._sort_value = self._mtime
        f = open(self._article_filepath)
        self._markdown = f.read()
        f.close()
        self._markdown_without_title = self._markdown
        # 去掉标题 
        lines = self._markdown_without_title.split('\n')
        if lines:
            first_line = lines[0]
            if first_line.startswith('#'):
                if not self.article_title:
                    title_from_markdown = first_line[1:].strip()
                    self.article_title = title_from_markdown
                self._markdown_without_title = '\n'.join(lines[1:])
        # 文件内配置 
        pos_inner_config = self._markdown_without_title.find('```\nMING-ARTICLE-CONFIG')
        if pos_inner_config >= 0:
            # 读取文件内的配置, 配置内容必须放在文件的末尾
            inner_config_str = self._markdown_without_title[pos_inner_config:]
            p = '```\nMING-ARTICLE-CONFIG\n(.*?)\n```'
            j_l = re.findall(p, inner_config_str,re.S)
            if j_l:
                j = j_l[-1].strip()
                inner_config = json.loads(j)
                for (k,v) in inner_config.items():
                    #print 'inner config %s:%s'%(k,v,)
                    self[k] = v
            # 从文件从删除配置的内容
            self._markdown_without_title = self._markdown_without_title[:pos_inner_config]

        #print self._markdown_without_title
        # _sort_value 
        if self.article_publish_date:
            if ':' in self.article_publish_date:
                self._sort_value = string_to_time_float(self.article_publish_date)
            else:
                self._sort_value = string_to_date_float(self.article_publish_date)
        else:
            self.article_publish_date = date_to_string(self._mtime)

    def render_article_html(self):
        self._article_html = render(self._markdown_without_title.decode('utf-8'))

    def render_html(self):
        self._load_next_previous_article() #载入上一篇和下一篇文章
        self.render_article_html()
        # css
        d_css = {}
        if self.article_css:
            for (selector,d_value) in self.article_css.items():
                css_v = "{"
                for k,v in d_value.items():
                    css_v += '%s:%s;'%(k,v,)
                css_v += "}"
                d_css[selector] = css_v
        theme_name = self.article_theme or 'default'
        env=Environment(loader=PackageLoader(THEMES_DIR.replace('./',''),theme_name))
        theme = env.get_template('article.html')
        theme_dir = os.path.join('/',THEMES_DIR.replace('./',''),theme_name) 
        html = theme.render(theme_dir = theme_dir,article = self,d_css = d_css)
        return html

    def generate_html(self):
        html = self.render_html()
        if not self.article_link:
            raise Exception('No Article Link')
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR,
                self.article_link)
        print output_filename
        f = open(output_filename,'w')
        f.write(html.encode('utf-8'))
        f.close()
        # copy theme
        theme_name = self.article_theme or 'default'
        copy_theme(theme_name)

    def _load_next_previous_article(self):
        '''载入上一篇和下一篇文章'''
        site_maker = SiteMaker() 
        link = self.article_link
        if link not in site_maker.link_list:
            return
        pos = site_maker.link_list.index(link)
        # 上一篇文章
        if pos > 0 :
            previous_pos = pos - 1
            previous_link = site_maker.link_list[previous_pos]
            self._previous_article = site_maker.article_table[previous_link]
        # 下一篇文章
        if pos < len(site_maker.link_list) - 1:
            next_pos = pos + 1
            next_link = site_maker.link_list[next_pos]
            self._next_article = site_maker.article_table[next_link]

# site
class SiteMaker(Modal):
    def __init__(self):
        super(SiteMaker,self).__init__()
        self.article_table = {}
        self.link_list = []
        self._load_config()
        self._prepare_articles()

    def _load_config(self):
        config = Config()
        for (k,v) in config.items():
            self[k] = v

    def _prepare_articles(self):
        folder = DOCUMENTS_DIR 
        #print folder
        name_list = os.listdir(folder)
        #print name_list
        file_name_list = [os.path.join(folder,f) for f in name_list if os.path.splitext(f)[-1].upper() in ['.MD','.MARKDOWN'] and not f.startswith('_')]
        file_name_list.sort(lambda f1,f2: int(os.stat(f2).st_mtime) - int(os.stat(f1).st_mtime))
        self.article_table = {}
        for f in file_name_list:
            _,filename = os.path.split(f)
            article = Article(filename)
            link = article.article_link
            self.article_table[link] = article
        def _cmp(link_1, link_2):
            article_1 = self.article_table.get(link_1)
            article_2 = self.article_table.get(link_2)
            return int(article_2._sort_value - article_1._sort_value)
        self.link_list = self.article_table.keys() 
        self.link_list.sort(_cmp) # 排序的链接列表

    def index_article(self):
        top_link = self.link_list[0]
        article = self.article_table[top_link]
        return article

    def archive(self):
        '''按年列出文件列表'''
        d = {}
        for link in self.link_list:
            article = self.article_table[link]
            col = article.article_publish_date.split('-')
            year = col[0]
            if year not in d:
                l = [article,]
                d[year] = l
            else:
                l = d[year]
                l.append(article)
                d[year] = l
        return d

    def render_archive(self):
        d_archive = self.archive()
        theme_name = self.site_theme or 'default'
        env=Environment(loader=PackageLoader(THEMES_DIR.replace('./',''),theme_name))
        theme = env.get_template('archive.html')
        theme_dir = os.path.join('/',THEMES_DIR.replace('./',''),theme_name) 
        html = theme.render(theme_dir = theme_dir,site=self,
                archive = d_archive)
        return html

    def render_feed(self):
        item_list = []
        for link in self.link_list:
            article = self.article_table[link]
            item = rfeed.Item(title = article.article_title,
                    link = article.article_link,
                    description = article.article_subtitle,
                    author = article.author or '',
                    guid = rfeed.Guid(article.article_link),
                    pubDate = datetime.strptime(article.article_publish_date,'%Y-%m-%d'))
            item_list.append(item)
        feed = rfeed.Feed(title = self.site_title,
                link = self.site_url,
                description = '',
                language = 'zh-cn',
                lastBuildDate = datetime.now(),
                items = item_list)
        return feed.rss()

    def render_atom(self):
        fg = FeedGenerator()
        fg.id(self.site_url)
        fg.title(self.site_title)
        fg.link(href = self.site_url,rel = 'alternate')
        fg.link(href = self.site_url + 'atom.xml',rel = 'self')
        fg.language('zh-cn')
        for link in self.link_list:
            article = self.article_table[link]
            fe = fg.add_entry()
            fe.id(article.article_link)
            fe.link(link = {'href':self.site_url + article.article_link})
            fe.title(article.article_title)
            fe.description(article.article_subtitle or '')
            fe.author(name = article.author or '',
                    email = article.author_email or '')
            d = datetime.strptime(article.article_publish_date,'%Y-%m-%d') 
            pubdate = datetime(year = d.year, month = d.month, day = d.day,tzinfo = UTC(8))
            fe.pubdate(pubdate) 
            article.render_article_html()
            fe.content(content = article._article_html,
                    type = 'html')
        atom_feed = fg.atom_str(pretty = True)
        return atom_feed

    def create_article(self,name,title = 'untitled',link = None):
        '''往 _documents 中添加一篇新文章'''
        config = Config()
        config.article_title = title
        if not link:
            config.article_link = title + '.html'
        else:
            config.article_link = link
        del config['site_name']
        del config['site_name_mobile']
        del config['site_title']
        del config['site_title_mobile']
        del config['site_url']
        del config['site_links']
        _,ext = os.path.splitext(name)
        if ext not in ['md','markdown']:
            name += '.md'
        if not title.startswith('#'):
            title = '# ' + title
        article_filename = os.path.join(DOCUMENTS_DIR,name)
        print 'article:%s'%(article_filename,)
        f = open(article_filename,'w')
        f.write(title)
        f.close()
        article_config_filename = article_filename + '.json'
        print 'article config:%s'%(article_config_filename,)
        s = json.dumps(config)
        f = open(article_config_filename,'w')
        f.write(s)
        f.close()
        print 'article title:%s'%(title,)
        print 'article link:%s'%(link,)

    def make_article(self,article_filename):
        _,ext = os.path.splitext(article_filename)
        if not ext:
            article_filename += '.md'
        article = Article(article_filename)
        article.generate_html()

    def make_archive(self):
        #html = 'archive.html'
        html = self.render_archive()
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = os.path.join(OUTPUT_DIR, 'archive.html')
        print output_filename
        f = open(output_filename,'w')
        f.write(html.encode('utf-8'))
        f.close()
        # copy theme
        theme_name = self.site_theme or 'default'
        copy_theme(theme_name)

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
        # copy theme
        theme_name = self.site_theme or 'default'
        copy_theme(theme_name)

    def make_about(self):
        article_filename = '_about.md'
        article = Article(article_filename)
        article.generate_html()

    def make_feed(self):
        #xml =  self.render_feed()
        #filename = os.path.join(os.path.dirname(__file__),OUTPUT_DIR,'feed.xml')
        xml = self.render_atom()
        filename = os.path.join(OUTPUT_DIR,'atom.xml')
        f = open(filename,'w')
        f.write(xml)
        f.close()
        print filename

    def make_site(self):
        self.make_index()
        self.make_about()
        self.make_archive()
        self.make_feed()
        # 依次生成每一篇文章
        for (link,article) in self.article_table.items():
            article.generate_html()

# copy themes
def copy_theme(name):
    '''copy theme from ./_themes/<name> to ./output/_themes/<name>'''
    theme_dir_from = os.path.join(THEMES_DIR,name)
    theme_dir_to = os.path.join(OUTPUT_DIR,'_themes',name)
    if not os.path.exists(theme_dir_from):
        print 'theme not found'
        return
    #print 'from:%s'%(theme_dir_from,)
    #print 'to:%s'%(theme_dir_to,)
    for (root,dirs,files) in os.walk(theme_dir_from):
        for one_file in files:
            from_path = os.path.join(root,one_file)
            to_path = os.path.join('./_output',from_path.replace('./',''))
            # 如果目标文件的修改时间一样就不要拷贝
            if os.path.exists(to_path):
                to_mtime = os.stat(to_path).st_mtime
                from_mtime = os.stat(from_path).st_mtime
                if from_mtime == to_mtime:
                    print 'skip file:%s to %s'%(from_path, to_path,)
                    continue
            # 先创建目录
            to_dir = os.path.dirname(to_path)
            if not os.path.exists(to_dir):
                print 'create dir:%s'%(to_dir,)
                os.makedirs(to_dir)
            shutil.copy2(from_path,to_path)
            print 'copy file:%s to %s'%(from_path,to_path,)
        for one_dir in dirs:
            from_path = os.path.join(root,one_dir)
            to_path = os.path.join('./_output',from_path.replace('./',''))
            if os.path.exists(to_path):
                print 'skip dir %s to %s'%(from_path, to_path,)
                continue
            else:
                # copy dir
                os.makedirs(to_path)
                shutil.copystat(from_path,to_path)
                print 'copy dir: %s to %s'%(from_path,to_path,) 

# cli
def cli_make_article():
    if len(sys.argv) < 3:
        print 'no article specificed' 
        return
    article_filename = sys.argv[2]
    site_maker = SiteMaker()
    site_maker.make_article(article_filename)
    site_maker.make_index()
    site_maker.make_archive()

def cli_create_article():
    opts,args = getopt.getopt(sys.argv[2:],"n:t:l:",["name=","title=","link="])
    name = ''
    title = 'untitled'
    link = ''
    for (op,value) in opts:
        if op in ['-n','--name']:
            name = value 
        if op in ['-t','--title']:
            title = value
        if op in ['-l','--link']:
            link = value
    if not name:
        print '-n or --name required'
        return
    site_maker = SiteMaker()
    site_maker.create_article(name,title=title,link = link)

def cli_make_archive():
    site_maker = SiteMaker()
    site_maker.make_archive()

def cli_make_about():
    site_maker = SiteMaker()
    site_maker.make_about()

def cli_make_index():
    site_maker = SiteMaker()
    site_maker.make_index()

def cli_make_feed():
    site_maker = SiteMaker()
    site_maker.make_feed()

def cli_make_site():
    site_maker = SiteMaker()
    site_maker.make_site()

def cli_clean():
    '''清理 _output 目录下的全部内容'''
    top = OUTPUT_DIR 
    print top
    for (root,dirs,files) in os.walk(top):
        for one_file in files:
            path = os.path.join(root,one_file)
            print path
            os.remove(path)
        for one_dir in dirs:
            path = os.path.join(root,one_dir)
            print path
            shutil.rmtree(path)

def cli_init():
    '''初始化一个站点配置'''
    params = sys.argv[2:] if len(sys.argv) > 2 else []
    if '.' in params:
        params = params[1:]
    opts,args = getopt.getopt(params,"n:t:l:d:",["name=","title=","link=","dir="])
    d = '.'
    site_name = 'MING SITE'
    site_title = 'MING SITE'
    site_url = 'http://localhost/'
    for (op,value) in opts:
        if op in ['-n','--name']:
            site_name = value 
        if op in ['-t','--title']:
            site_title = value 
        if op in ['-l','--link']:
            site_url = value
        if op in ['-d','--dir']:
            d = value
    # ming dir
    ming_file = os.path.realpath(__file__) if os.path.islink(__file__) else __file__ 
    ming_dir = os.path.dirname(ming_file)
    print 'ming dir:%s'%(ming_dir,)
    # site.json
    site_json = {
            "site_theme":"default",
            "site_name":site_name,
            "site_title":site_title,
            "site_name_mobile":site_name,
            "site_title_mobile":site_title,
            "site_url":site_url,
            "site_links":[
                {"title":"存档",
                    "url":"archive.html"},
                {"title":"关于",
                    "url":"about.html"},
                ],
            "author":"adow",
            "author_email":"",
            "author_status":"",
            "author_avatar":"",
            "author_weibo":"",
            "author_twitter":"",
            "author_github":"",
            "article_theme":"default",
            "article_css":{
                },
            }
    site_json_str = json.dumps(site_json,indent = 4)
    site_json_filename = os.path.join(d,'site.json')
    site_json_f = open(site_json_filename,'w')
    site_json_f.write(site_json_str)
    site_json_f.close()
    print site_json_filename
    #  _documents
    documents_dir_from = os.path.join(ming_dir,'_documents')
    documents_dir_to = os.path.join(d,'_documents')
    shutil.copytree(documents_dir_from,documents_dir_to)
    print 'documents:%s'%(documents_dir_to,)
    # _themes
    themes_dir_from = os.path.join(ming_dir,'_themes')
    themes_dir_to = os.path.join(d,'_themes')
    shutil.copytree(themes_dir_from,themes_dir_to)
    print 'themes:%s'%(themes_dir_to,)
    # _output
    output_dir = os.path.join(d,'_output')
    print 'output:%s'%(output_dir,)
    os.makedirs(output_dir)

def help():
    print 'ming local-server: start local web server' 
    print 'ming create-article -n <articlename> -t <article title>'
    print 'ming make-article <article-name>: make html'
    print 'ming make-archive: make archive.html'
    print 'ming make-about: make about.html'
    print 'ming make-index: make index.html'
    print 'ming make-site: make all pages'
    print 'ming init -n <sitename> -t <sitetitle> -l <siteurl>'
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
            'create-article':cli_create_article,
            'make-article':cli_make_article,
            'make-archive':cli_make_archive,
            'make-about':cli_make_about,
            'make-index': cli_make_index,
            'make-feed':cli_make_feed,
            'make-site': cli_make_site,
            'clean':cli_clean,
            'init':cli_init,
            'test':test}.get(cmd,help)()
