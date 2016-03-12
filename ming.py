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
import datetime

from jinja2 import Environment,PackageLoader
from mikoto.libs.text import render
from vendor import rfeed

OUTPUT_DIR = '_output'
DOCUMENTS_DIR = '_documents'
THEMES_DIR = '_themes'

#time
def now():
    '''现在时间'''
    return time.time()

def time_to_long_string(t=now()):
    '''时间转换成 yyyy-MM-dd HH:mm:ss'''
    TIMEFORMAT="%Y-%m-%d %X"
    return time.strftime(TIMEFORMAT,time.localtime(t))

def now_long_string():
    '''现在时间的字符串'''
    return time_to_long_string()

def today_str():
    '''今天的日期'''
    return str(datetime.date.today())

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

def string_to_time(string):
    '''字符串转时间'''
    if string is None or string =='':
        return 0
    if ':' not in string:
        string+=" 00:00:00"
    TIMEFORMAT="%Y-%m-%d %H:%M:%S"
    t=time.strptime(string,TIMEFORMAT)
    return t

def string_to_date(string):
    '''字符串转日期'''
    TIMEFORMAT="%Y-%m-%d"
    t=time.strptime(string,TIMEFORMAT)
    return t

def make_runat_seconds(hours,minutes=0,seconds=0):
    '''从0点到现在的秒数'''
    return hours*60*60+minutes*60+seconds

def now_seconds():
    '''现在的秒数'''
    t=time.localtime()
    return make_runat_seconds(t.tm_hour,t.tm_min,t.tm_sec)

def start_of_today():
    '''今天开始的时间'''
    return time.time()-now_seconds() 

def end_of_today():
    '''今天结束的时间'''
    return start_of_today()+3600*24

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

# Article
class Article(Modal):
    def __init__(self,article_filename):
        super(Article,self).__init__() 
        self._article_filename = article_filename 
        self._article_filepath = os.path.join(DOCUMENTS_DIR,article_filename)
        self._article_config_filepath = self._article_filepath + '.json'
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
            return
        self._mtime = os.stat(self._article_filepath).st_mtime
        self._sort_value = self._mtime
        f = open(self._article_filepath)
        self._markdown = f.read()
        f.close()
        # article_title
        self._markdown_without_title = self._markdown
        lines = self._markdown_without_title.split('\n')
        if lines:
            first_line = lines[0]
            if first_line.startswith('#'):
                if not self.article_title:
                    title_from_markdown = first_line[1:].strip()
                    self.article_title = title_from_markdown
                self._markdown_without_title = '\n'.join(lines[1:])
        # _sort_value 
        if self.article_publish_date:
            if ':' in self.article_publish_date:
                self._sort_value = string_to_time_float(self.article_publish_date)
            else:
                self._sort_value = string_to_date_float(self.article_publish_date)
        else:
            self.article_publish_date = date_to_string(self._mtime)

    def render_html(self):
        self._load_next_previous_article() #载入上一篇和下一篇文章
        self._article_html = render(self._markdown_without_title.decode('utf-8'))
        # css
        d_css = {}
        for (selector,d_value) in self.css.items():
            css_v = "{"
            for k,v in d_value.items():
                css_v += '%s:%s;'%(k,v,)
            css_v += "}"
            d_css[selector] = css_v
        theme_name = self.themes or 'default'
        env=Environment(loader=PackageLoader(THEMES_DIR,theme_name))
        theme = env.get_template('article.html')
        theme_dir = os.path.join('/',THEMES_DIR,theme_name) 
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
        folder = os.path.join(os.path.dirname(__file__),DOCUMENTS_DIR)
        name_list = os.listdir(folder)
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
        theme_name = self.themes or 'default'
        env=Environment(loader=PackageLoader(THEMES_DIR,theme_name))
        theme = env.get_template('archive.html')
        theme_dir = os.path.join('/',THEMES_DIR,theme_name) 
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
                    pubDate = datetime.datetime.strptime(article.article_publish_date,'%Y-%m-%d'))
            item_list.append(item)
        feed = rfeed.Feed(title = self.site_title,
                link = self.site_url,
                description = '',
                language = 'zh-cn',
                lastBuildDate = datetime.datetime.now(),
                items = item_list)
        return feed.rss()

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
        article_filename = '_about.md'
        article = Article(article_filename)
        article.generate_html()

    def make_feed(self):
        xml =  self.render_feed()
        filename = os.path.join(os.path.dirname(__file__),OUTPUT_DIR,'feed.xml')
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
    top = os.path.join(os.path.dirname(__file__),OUTPUT_DIR)
    print top
    for (root,dirs,files) in os.walk(top):
        for one_file in files:
            path = os.path.join(root,one_file)
            print path
            os.remove(path)
        for one_dir in dirs:
            path = os.path.join(root,one_dir)
            print path
            os.rmdir(path)

def cli_init():
    params = sys.argv[2:] if len(sys.argv) > 2 else []
    # TODO: site.json
    site_json = {}
    # TODO: _documents
    # TODO: _documents/_ming.md, _documents/_ming.md.json
    # TODO: _themes
    # TODO: _themes/default
    # TODO: _output
    pass

def help():
    print 'ming local-server: start local web server' 
    print 'ming create-article -n <articlename> -t <article title>'
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
            'create-article':cli_create_article,
            'make-article':cli_make_article,
            'make-archive':cli_make_archive,
            'make-about':cli_make_about,
            'make-index': cli_make_index,
            'make-feed':cli_make_feed,
            'make-site': cli_make_site,
            'clean':cli_clean,
            'test':test}.get(cmd,help)()
