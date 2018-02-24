# 被忽视的 NSURLCache

作为一个 iOS 开发，你一定用过多种图片下载库，大名鼎鼎的 SDWebImage, Swift 下面的 Kingfisher。

我写此文的目的是想拉你入坑，来构造一个新的轮子，AWebImage 用来实现 iOS App 中的图片下载。

对于这个新的坑，他是 

* 使用 NSURLCache 和 NSCache 来实现缓存；
* 使用 NSURLSession 实现下载；

他没有：

* 没有实现自己的缓存系统；
* 没有进行图片处理，所以他不能创建缩略图，更不能处理GIF 图片；

对于 NSURLSession， 我想不用多说，因为现在大部分的网络请求库都用 NSURLSession 替换原来的 NSURLConnection。但这里的确想说说 NSURLCache。

## 前篇:  NSURLCache

现在大多数图片下载库都使用自建的缓存系统，当然我们知道原理是很简单，每个对应的 URL 都在本地保存一个文件，这样重复的 URL 将不再需要访问网络请求，而是从本地读取这个文件，为了更高效的获取图片，我们还会把图片保存在内存中。这样，当开始请求一个图片是，我们先从内存中尝试读取这个文件，如果没有再从磁盘中读取这个文件，如果还是没有，才真正的去网络上请求这个地址。

保存文件的过程如此简单，但是一旦涉及到如何管理这些缓存文件时，才是真正的问题；

* 我们如何知道缓存的图片什么时候过期（也许他永不过期）；
* 我们的磁盘不是无限大的，那些已经很久以前的图片文件该如何删除他们呢？
* 我们的内存也不是无限大的，我在内存中如何有些的管理这些缓存文件呢？内存不够的时候该怎么办？

所以我们不得不用使用更多的机制来管理这些缓存文件，我们可以有一个文件来记录这些文件的地址和过期时间，我们必须在 App 中实时监控磁盘和内存的使用情况，在适当的时候去移除不必要的图片引用。一旦你开始着手开始这部分的工作，你会发现这其中会非常复杂，到最后可能就直接放弃，不再管他们了。因为我们一开始的目标是减少图片的下载次数，在 App 中更高效的去显示他们，反正这个目的已经达到。

然而你一旦用上 NSURLCache，这些问题全部不用考虑，你只需要 **设置磁盘和内存的大小** 就可以了； 使用 NSURLCache 的优势在于：

* 系统自动管理缓存内容，所以你在开发 App 中不用知道该什么时候来删除这些磁盘或者内存中的缓存内容；不用担心系统内存不够的时候该如何有效的清理他们，一旦磁盘或者内存有压力，系统会自动清理他们，当然你也不用关心缓存的时间；
* 我感觉最大的优势在于 Cache-Control，因为我们只需要在服务端上根据 Http 协议设置 Cache-Control 的内容就可以告诉 NSURLCache, 这个缓存应该是什么时候过期了，客户端上设置不需要写任何一行代码 （NSURLRequest 的默认缓存策略就是这个）；

### 使用 NSURLCache 缓存

使用 NSURLCache 的最方便之处在于，他只需要几行代码就可以完成一个稳定的缓存系统；

首先我们要创建一个 NSURLCache，可以指定用于缓存的磁盘和内存的大小是多少；

    let cache = NSURLCache(memoryCapacity: 10 * 1024 * 1024,diskCapacity: 30 * 1024 * 1024,diskPath: "adow.adimageloader.urlcache")
    
构造一个 SessionConfiguration, 并使用这个 URLCache

    sessionConfiguration = NSURLSessionConfiguration.defaultSessionConfiguration()
    sessionConfiguration.URLCache = cache
    
用这个 sessionConfiguration 来构造一个 NSURLSession

    let session = NSURLSession(configuration: sessionConfiguration, delegate: nil, delegateQueue: self.sessionQueue)
    
如果想更简单，可以设置一个全局的 NSURLCache， 这样如果没有特别指定，所有的请求都将使用这个 URLCache。

    NSCache.setSharedURLCache(cache)

后面，就像没有使用缓存一样的去用 session 和 NSURLRequest 去做请求，不用任何改变，比如使用 `dataTaskWithRequest` 来请求，

    self.task = session.dataTaskWithRequest(request) { (data, response, error) in
            if let error = error {
                NSLog("error:%@", error.domain)
            }
            ...
        }
    
当这个 NSURLRequest 命中缓存的时候， `dataTaskWithRequest` 将不会发起真正的网络请求，而是从缓存中获取内容，我们也不用关心这个缓存到底来自磁盘还是内存。

### CachePolicy

使用 NSURLCache 的最大好处在于可以通过服务器控制 Cache-Control 来管理本地缓存的策略，另外也可以指定另外的几种策略；

* NSURLRequestReloadIgnoringLocalCacheData： 忽略缓存，必须从远程地址下载；
* NSURLRequestReturnCacheDataElseLoad：只要本地有缓存就使用本地的缓存（不管过期时间），只有本地没有缓存的时候才使用远程地址下载；
* NSURLRequestReturnCacheDataDontLoad：只从本地缓存获取内容，如果本地没有的话，也不会去远程地址下载（也就是离线模式）；
* NSURLRequestUseProtocolCachePolicy：默认缓存策略；

设置 CachePolicy 有两个地方：

* 可以为每个 NSURLRequest 设置单个请求的 `cachePolicy`;
* 也可以通过 NSURLSessionConfiguration 设置 `cachePolicy` 来实现 `NSURLSession` 下所有的请求都使用同样的缓存策略；

### Cache-Control

对于最常用的 NSURLRequestUseProtocolCachePolicy， 我们需要有两个注意的地方，即使当一个请求在本地存在缓存的情况下，如果这个请求需要重新验证 （Revalidation),那系统还是会发起一个 HEAD 请求到服务器上去确定内容是否已经被修改过，如果修改的话还是会重新下载；如果缓存内容不需要验证，那系统只需要确定缓存时间是不是已经过期就可以了；

在开发中，我们只需要在服务端为每个图片资源设置 `Cache-Control` 响应头，比如下面的地址

[http://7vihfk.com1.z0.glb.clouddn.com/photo-1457369804613-52c61a468e7d.jpeg](http://7vihfk.com1.z0.glb.clouddn.com/photo-1457369804613-52c61a468e7d.jpeg)

![cache-control.png](http://7vihfk.com1.z0.glb.clouddn.com/cache-control.png)

的 Response Header 中有字段: `Cache-Control:public, max-age=31536000`, 这样就可以确定这个资源的缓存时间。 但事实上，在 App 的开发过程中，我们不需要关心这个的，唯一要做的就是告诉服务端开发的人员务必在静态资源中输出正确的的 `Header`。

除了 `Cache-Control` ，还有两个字段可以用来控制缓存:

* `Last-Modified`  这个头的值表明所请求的资源上次修改的时间；
* `Etag`  这是 “entity tag” 的缩写，它是一个表示所请求资源的内容的标识符。


关于 NSURLCache 的更多使用（比如定制缓存），可以参考 : [http://nshipster.cn/nsurlcache/](http://nshipster.cn/nsurlcache/)

但是使用 NSURLCache 的过程中还是会有几个坑需要注意的: [说说 NSURLCache 中的那些坑](http://www.codingnext.com/nsurlcache.html)


## 后篇: 实现 AWebImage

介绍完 NSURLCache，我们可以开始挖坑来实现一个自己的图片缓存系统了，`AWebImage`, 他包含两个部分；

* AWebImage: 包含了 `AWImageLoader` 对象中真正的图片下载方法；
* UIImageView+AWebImage： UIImageView 的 extension, 毕竟大部分时候我们是直接在 UIImageView 上面显示下载的图片的；

除此之外，我还写了一个 Demo, 用来显示这个功能， 这个 App 调用了 `500px.com` 的编辑选推图片列表的接口，我们将他们显示在一个 `UICollectionView` 上，点击的时候还会看到这个作品的详细大图；

![500px-list.png](http://7vihfk.com1.z0.glb.clouddn.com/500px-list.png)


![500px-detail.png](http://7vihfk.com1.z0.glb.clouddn.com/500px-detail.png)

### 构建 AWebImage

我们实际使用的是一个 `AWImageLoader`, 调用其中的 `func downloadImage(url:NSURL, callback : AWImageLoaderCallback)` 来获取网络图片内容（或者来自本地缓存）。

网络访问依靠 NSURLSession， 使用基于 Block 的接口可以很快就写出一个网络请求操作，但是在这之前我们需要考虑一下 NSURLSession 需要使用哪些东西呢；

* 一个用于网络请求的队列 (NSOperationQueue);
* 一个所有图片请求共享的缓存 （NSURLCache）
* 确定的缓存策略，这里使用默认的缓存策略就好；

以上这些东西只需要一个共享的 NSURLSession 就可以了，所有的请求都使用这个 session 发出；所以我们可以构造一个单独的唯一实例的 NSURLSession （一个全局变量）, 然后所有的 `AWImageLoader` 都使用相同的 `session`; 

但是我们还需要一些其他的大家共享的东西

* 回调函数列表；
* 快速缓存；
* 其他的异步操作共享队列；

#### 回调函数

由于网络下载图片是一个异步的过程，所以我们需要一个回调函数，在这里的类型是 `AWImageLoaderCallback`, 他实际上就是 `(UIImage,NSURL) -> ()` 而已，所以在得到图片内容后，我们会得到 `UIImage` 和 `NSURL`;

有时在一个界面中有两个 UIImageView 显示了同样的图片地址，这时我们不需要发出两次请求，只需要在获取图片内容后分别调用他们的回调函数去显示图片就好了，所以我们对每个 Url 请求，都可能会存在多个回调函数，这种情况在 `UITableView` 和 `UICollectionView` 中很常见，因为在滚动的过程中，由于 `Cell Reuse` 的存在，很多内容会被重复加载；

所以我们建立一个 `fetchList:[String:AWImageLoaderCallbackList]`, 也就是说，针对每一个 url, 都会可能存在一个对应的回调函数列表；当一个请求完成时，会取得对应的回调函数列表并依次调用，然后再将这个 url 对应的回调列表清除；

但是，由于请求都会在异步线程中完成，这个回调函数队列可能在多个线程中操作，所以我们不得不做一些锁处理，在添加和删除回调函数的时候进行 Lock, 这里使用的是  `dispatch_barrier_sync` 

        /// 添加一个 url 的回调函数，如果这个 url 已经在任务中了，只需要增加回调函数，并返回 true, 通知外部不需要重新发起任务
        func addFetch(key:String, callback:AWImageLoaderCallback) -> Bool {
            var skip = false
            let f_list = fetchList[key]
            if f_list != nil {
                skip = true
            }
            dispatch_barrier_sync(fetchListOperationQueue) {
                if var f_list = f_list {
                    f_list.append(callback)
                    self.fetchList[key] = f_list
                }
                else {
                    self.fetchList[key] = [callback,]
                }
            }
            return skip
            
        }
        /// 删除一个地址的全部回调函数
        func removeFetch(key:String) {
            dispatch_barrier_sync(fetchListOperationQueue) {
                self.fetchList.removeValueForKey(key)
            }
        }
        /// 清理所有地址的回调函数
        func clearFetch() {
            dispatch_barrier_async(fetchListOperationQueue) {
                self.fetchList.removeAll()
            }
        }

#### 快速缓存

既然  NSURLCache 已经同时使用内存缓存和磁盘缓存了，我们为什么还需要另一个快速缓存呢？

因为所有 NSURLCache 中对请求的缓存都获取的是 `NSData`，所以每次获取内容和还是要将他构造成为 `UIImage`, 而在系统中 `+ (UIImage * _Nullable)imageWithData:(NSData * _Nonnull)data` 是不会缓存图片的，所以会导致重复创建 `UIImage`。另一个原因是，从 NSURLCache 中获取到内容也是一个异步的过程。如果我们把构造好的图片都存入一个单独的内存缓存，那每次下载图片前只要先从这个快速缓存中获取一次内容就可以了（而且也不用异步完成,这在用于显示 UICollectionViewCell, UITableViewCell 中的图片非常重要)，如果没有再继续从 `NSURLCache` 或者源站地址下载；

作为这个快速缓存，`NSCache` 是最适合的，他同样会在系统内存又压力时自动清理内容，类似 NSMutableDictionary， 但是他更高效和快速，不会拷贝对象，而且在任意线程中操作都是安全的。使用 NSCache 非常简单，只需要指定使用内存的大小就好了：

    fastCache = NSCache()
    fastCache.totalCostLimit = 30 * 1024 * 1024
    
#### AWImageLoader 和 AWImageLoaderManager

我们把所有共享的东西都通过 `AWImageLoaderManager` 来管理，操作队列，NSURLCache， NSCache，回调队列，共享 Session 等, 并作为一个单例；

而每个下载任务都通过一个 AWImageLoader 发起，他从 `AWImageLoaderManager` 获取所有共享的内容 (以及一个共享的 session)。其实我们完全可以把 AWImageLoader 和 AWImageLoaderManager 合并在一起形成一个单例对象。分开他是想在 `AWImageLoader` 对象中持有这个请求任务，以便于后面管理（取消）。由于每个任务都会创建 `AWImageLoader`，因此将重复的内容分离出来通过一个单例的 `AWImageLoaderManager` 来为所有的任务都共享，在外部来看 `AWImageLoaderManager` 是不需要知道，只要调用 `AWImageLoader` 的方法就可以了；

下面是 `AWImageLoader` 中实际获取图片的代码（先从 fastCache （NSCache），再从 URLCache 或者真正的网络下载，我们不需要自己去从 URLCache 中获取缓存内容，这部分是 NSURLSession 来完成的）

        func downloadImage(url:NSURL, callback : AWImageLoaderCallback){
            /// 从 fastCache(NSCache) 获取到以及构造好的图片，直接在当前线程返回
            if let cached_image = self.imageFromFastCache(url) {
                callback(cached_image, url)
                return
            }
            let fetch_key = url.absoluteString
            /// 用来将图片返回到所有的回调函数
            let f_callback = {
                (image:UIImage) -> () in
                if let f_list = AWImageLoaderManager.sharedManager.readFetch(fetch_key) {
                    AWImageLoaderManager.sharedManager.removeFetch(fetch_key)
                    dispatch_async(dispatch_get_main_queue(), {
                        f_list.forEach({ (f) in
                            f(image,url)
                        })
                    })
                }
            }
            /// origin
            /// addFetch 会返回这个请求是不是已经在列表中了，如果有的话，那就不用再次发出请求了，只需要为他添加一个回调函数就可以了
            let skip = AWImageLoaderManager.sharedManager.addFetch(fetch_key, callback: callback)
            if skip {
    //            NSLog("skip")
                return
            }
            /// request
            let session = AWImageLoaderManager.sharedManager.defaultSession
            let request = NSURLRequest(URL: url)
            self.task = session.dataTaskWithRequest(request) { (data, response, error) in
                if let error = error {
                    NSLog("error:%@", error.domain)
                }
                /// no data
                guard let _data = data else {
                    NSLog("no image:%@", url.absoluteString)
                    f_callback(emptyImage)
                    return
                }
                dispatch_async(AWImageLoaderManager.sharedManager.imageDecodeQueue, {
    //                NSLog("origin:%@", url.absoluteString)
                    let image = UIImage(data: _data) ?? emptyImage
                    AWImageLoaderManager.sharedManager.fastCache.setObject(image, forKey: fetch_key) /// 存入 fastCache
                    f_callback(image)
                    return
                })
            }
            self.task?.resume()
        }
    
### UIImageView + AWebImage

就如前面所说，大部分情况下，我们都是在 UIImageView 中显示下载的图像，所以为 UIImageView 建立一个扩展，用来下载和显示网络图像是最自然的方法。这里有一个 UIImageView + AWebImage，实际调用的时候是这样的:

           imageView.aw_downloadImageURL(photo.imageURL, showLoading: true, completionBlock: { (image, url) in
               
           })
           
其实我们只是调用 `AWImageLoader` 的 `func downloadImage(url:NSURL, callback : AWImageLoaderCallback)` 方法而已，非常简单。

但是考虑到 UIImageView 显示的图片可能不是固定的，比如在 UITableViewCell, UICollectionViewCell 中，由于 `reuse` 的时候会在同一个 `UIImageView` 上显示来自不同位置的图片，而获取图片在很多情况下又是在不可预知顺序的异步方法中，所以很有可能最后显示在屏幕上的并不是当前想要的图片了。有两种解决的办法:

* 开始获取图片的时候，会取消这个 `UIImageView` 之前的图片任务；
* 为每个 `UIImageView` 存储一个当前任务的下载地址，获取到图片后，在显示之前先判断一下这次回调图片的地址和保存在 `UIImageView` 中的地址是不是相同，如果不同的话，说明实际显示的图片已经换掉了，那就不用显示这张图片了。

这里使用第二种方案，在 `UIImageView` 新增一个属性 `aw_image_url` 用来存储当前任务的地址，由于 `extension` 中不能增加存储属性，所以只能依靠 `Associated Object` 来实现:

    private var imageUrlKey : Void?
    
    /// 在 extension UIImageView 中增加
    /// 下载的 imageurl
    var aw_image_url : NSURL? {
        get{
            return objc_getAssociatedObject(self, &imageUrlKey) as? NSURL
        }
        set {
            objc_setAssociatedObject(self, &imageUrlKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC)
        }
    }
    
当开始获取图片任务时，首先记录一下这个任务的 url, 并在任务的回调函数中检查这个地址是不是有改变, 所以整个 `UIImageView.aw_downloadImageURL` 的过程如下:

    func aw_downloadImageURL(url:NSURL,
                                   showLoading:Bool,
                                   completionBlock:AWImageLoaderCallback){
        /// 先设置要下载的图片地址
        self.aw_image_url = url
        if showLoading {
            self.aw_showLoading()
        }
        let loader = AWImageLoader()
        loader.downloadImage(url) { [weak self](image, url) in
            if showLoading {
                self?.aw_hideLoading()
            }
            guard let _self = self, let _aw_image_url = _self.aw_image_url else {
                NSLog("no imageView")
                return
            }
            /// 校验一下现在是否还需要显示这个地址的图片
            if _aw_image_url.absoluteString != url.absoluteString {
                NSLog("url not match:%@,%@", _aw_image_url,url)
            }
            else{
                self?.aw_setImage(image)
                completionBlock(image,url)
            }
        }
    }

### 在 NSDefaultRunLoopMode 开始下载图片；

如果在 UICollectionView 中使用 AWebImage 进行下载，他会在任何 `RunLoop` 模式中开始处理，但是有的时候这样做的确是在浪费，因为滚动中很多下载实际被替换掉了，我们最好在滚动结束后才开始真正的图片下载。

如果在 `NSDefaultRunLoopMode` 中开始下载过程，只有滚动结束时候才会真正开始，下载的代码被延时提交了。但是，因为 cell reuse 的时候会清理之前显示的图片，所以实际上在滚动的时候，没有任何图片会显示出来。这时候 fastCache 会体现作用，如果能从 fastCache 中获取内容，那就直接显示在 cell 中（不用等待到滚动结束后开始），如果 fastCache 中没有图片，那只能延时开始下载。

但是这又会引发另一个问题，在快速滚动中，开始可能下载的任务因为在滚动中被延时，但是紧接着这个cell因为被 `reuse` 而这时他又在另一个位置中从 fastCache 中获取了图片并显示了（恰好这个位置的图片存在于 fastCache 中)，而之前的延时任务在后面又被触发了，他会在稍后返回，这时会替换之前从 fastCache 中获取的图片，这时会看到 `Cell` 中显示图片变化了一下，而且显示的并不是现在这个位置需要的图片。需要注意的时候这种情况下是无法通过保存的 `aw_image_url` 匹配来忽略图片显示的，因为他的代码是在后面执行的（延时提交了），所以地址已经被更新了。解决的办法是引入 `aw_image_set` 作为判断，在任务真正开始前，如果 `aw_image_set` 被设置了，就不用开始这个任务了，因为这个 UIImageView 已经显示了正确的图片。

    /// 只在 DefaultRunLoopMode 模式中加载
    func aw_downloadImageURL_delay(url:NSURL,
                                   showloading:Bool,
                                   completionBlock : AWImageLoaderCallback) {
        /// 要一开始就重置状态，因为后面的方法被延时提交，而在返回的时候可能已经又其他图片从快速缓存中获取了
        self.aw_image_set = false
        /// 如果已经有存在的图片，就不要在 DefaultRunLoopMode 中加载
        let loader = AWImageLoader()
        if let cached_image = loader.imageFromFastCache(url) {
            self.aw_hideLoading()
            self.aw_setImage(cached_image)
            self.aw_image_url = url
            completionBlock(cached_image, url)
            return
        }
        /// 开始延时获取图片内容
        let par = _AWImageLoaderPar(url: url, showLoading: showloading, completionBlock: completionBlock)
        self.performSelector(#selector(UIImageView.aw_downloadImageURL_p(_:)), withObject: par, afterDelay: 0.0, inModes: [NSDefaultRunLoopMode,])
    }
    /// 延时提交的方法，由于这个方法延时提交，所以可能 cell 在下一次的 reuse 中已经获得了 image， 而此时又开始执行这个方法时就第二次获得了内容，他又会替换第一次的内容，因此在开始前先判断一下是否有图片被设置了；
    @objc private func aw_downloadImageURL_p(par:_AWImageLoaderPar) {
        if self.aw_image_set {
            NSLog("image existed")
            return
        }
        self.aw_downloadImageURL(par.url, showLoading: par.showLoading, completionBlock: par.completionBlock)
    }
    @objc
    private func aw_setImage(image:UIImage){
        self.image = image
        self.aw_image_set = true /// 设置图片后更新 aw_image_set,防止后面的任务会替换现在的图片
    }
    
### 完整的 AWebImage 以及 Demo App 代码

[https://github.com/adow/AWebImage](https://github.com/adow/AWebImage)

> 由于 500px.com在墙外，这里例子中的图片有时会下载不成功，这时在 UIImageView 中显示的都是空白的图片，并且在下一次滚动后界面更新时会重新尝试下载。




```
MING-ARTICLE-CONFIG
{
    "article_title": "被忽视的 NSURLCache", 
    "article_subtitle": "实现一个网络图片下载工具 AWebImage", 
    "article_cover_photo": "http://7vihfk.com1.z0.glb.clouddn.com/pexels-photo-55613.jpg", 
    "article_category": "swift", 
    "article_link": "you-forget-nsurlcache.html", 
    "article_css": {}, 
    "article_publish_date": "2016-06-13", 
    "article_comments": 1, 
    "article_theme": "default"
}
```
