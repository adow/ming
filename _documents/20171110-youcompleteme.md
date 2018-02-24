# 20171110 一整天都在和 YouCompleteMe 较劲

今天本来要写一个 web 服务用来测试订单应用开发。因为要能够被外部访问，我就准备直接在服务器 (一台干净的 GCE 的服务器 CentOS) 上用 Python 写一个简单的应用服务。然后所做的事情经历了如下的步骤：

- `vim test.py` 写了一个简单的 `torando` 应用（输出请求内容），`python test.py` 后外面访问正常。
- 开始处理对接应用 url 回调的处理，修改 `test.py`, 发现缩进行为不对，按下 `tab` 居然不是输出4个空格。因为服务器上的 `vim` 没有任何的配置。
- 从我的 `vim` 配置仓库, `clone`， 然后连接到 `.vimrc` 文件；
- 安装 `vundle`；
- 在 `vim` 中使用 `vundle` 安装插件, `PluginInstall`，提示 `LeaderF` 和 `YouCompleteMe` 需要更高版本的 `vim`；
- 删除系统内 `vim`, 直接编译安装 `vim 8`;
- 编译安装 `YouCompleteMe`, 出现错误

不管是运行 `./install.py --clang-completer`,还是编译 `ycm_core`, 都是出现一样的编译错误：

	gmake[3]: *** [BoostParts/CMakeFiles/BoostParts.dir/libs/python/src/dict.cpp.o] 错误 4
	gmake[2]: *** [BoostParts/CMakeFiles/BoostParts.dir/all] 错误 2
	gmake[1]: *** [ycm/CMakeFiles/ycm_core.dir/rule] 错误 2
	gmake: *** [ycm_core] 错误 2
	ERROR: the build failed.

查看了 `YouCompleteMe` 的完整安装文档，把所有的工具升级到最新版，还装了 `Python3`。还是这个问题，暂时放弃了，不知道是不是 `CentOS 7` 或者 `vim8` 的问题。我只是想写个 `Python`，先用 `OmmiComplete`吧。

所以，代码还没有开始写，一天过去了。


```
MING-ARTICLE-CONFIG
{
    "article_title": "20171110 \u4e00\u6574\u5929\u90fd\u5728\u548c YouCompleteMe \u8f83\u52b2", 
    "article_subtitle": "有的时候时间不是被玩掉的", 
    "article_cover_photo": "http://7vihfk.com1.z0.glb.clouddn.com/tyler.jpg", 
    "article_category": "随手记", 
    "article_link": "20171110-youcompleteme.html", 
    "article_css": {}, 
    "article_publish_date": "2017-11-10", 
    "article_comments": 1, 
    "article_theme": "lep"
}
```