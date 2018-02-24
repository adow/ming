# 最近使用 Javascript 生态环境开发的体验

为了了解一下 Javascript 开发的生态环境，我开始做一个小工具 `paper`。他是一个在线的 Markdown 编辑器（使用 CodeMirror)。可以用来发布一篇文章，他们在服务器上都是有一个静态的 `md` 文件。在这过程中我计划粗浅的学习这些知识： React.js, Node.js, NPM/Yarn, Babel, Webpack, ES6.

本来只想用两天的时间来完成这个测试项目，但是实际却用了五天。在一个全新的开发环境中开发不是那么容易，不过还好这次的体验中并没有遇到太多的坑。

大多数时候使用了 yarn 来作为包管理工具，因为以前并不用npm，所以没法做比较。当然这些东西比 python 下用 `easy_install` 和 pip 轻松多了。安装所有的包都很顺利。（只要不打开那个可怕的 `node_modules` 目录都觉得压力不大）

webpack 作为打包工具虽然需要配置，但是使用起来并一点也不轻松。难的地方在如何规划好现在的开发目录和发布目录，对此我还没有太多的经验，以至于全部完成项目之后，又觉得各个文件位置放的不合理，然后又重新梳理里了好几遍，以至于改了好几次配置文件。

之前用 react.js 来作个文档项目的时候并没有使用任何包管理和打包工具。我只是使用了 react的两个文件和babel的浏览器运行时文件。当然我觉得直接这样用对我而言已经足够了。不过这次为了体验一下尽可能多的 javascript 生态环境，我还是用 webpack 来进行打包。使用下来之后我仍然对前端打包工具带来的益处存在疑虑，因为他们的复杂性并不小于所带来的好处。

Node.js 的使用让我感到很轻松，用 http，fs，path 模块非常方便的完成了这次的服务端开发，虽然一开始发现 http 模块没有自带静态文件解析有点惊讶，但是事实上自己来实现一个简单的并没有花多少时间。总体感觉和用 python/webpy/tornado 的体验差不了多少。

最后说说 ES6。由于之前没有完整的看过 ES6 的书，只凭借脑海中以前看到的一些零星的记忆在客户端和服务端代码中都用一些他的语法。由于我已经使用过好多种编程语言，所以使用的时候没有遇到什么问题，总之觉得都很自然。之前我一直用 ES5 的语法来写 react.js，替换过来也很顺利。所以用现代化的 javascript 来写代码的确非常的流畅和舒心。

总体而言，我觉得现在使用 javascript 作为开发工具已经具备非常好的条件。有很多成熟的工具来改进开发体验，甚至觉得现在前端届出来的太多库和框架，让选择变的太困难了。javascript 这么糟糕的语言经过这么多年无数前端程序员无尽的踩坑之后，终于变成了一个靠谱的工具了。


```
MING-ARTICLE-CONFIG
{
    "article_title": "最近使用 Javascript 生态环境开发的体验", 
    "article_subtitle": "", 
    "article_cover_photo": "http://7vihfk.com1.z0.glb.clouddn.com/javascript.jpg", 
    "article_category": "dev", 
    "article_link": "using-javascript.html", 
    "article_css": {}, 
    "article_publish_date": "", 
    "article_comments": 0, 
    "article_theme": "lep"
}
```