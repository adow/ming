# 说说NSURLCache 中的那些坑

我估计有很多人都会跟我一样在 iOS App 中自己去实现一个缓存 (Cache), 最常见的地方是一些图片下载和在线的配置参数。即使去看看现在主流的图片下载工具，比如 SDWebImage, 或者 Kingfisher, 他们也都自己建了一套缓存。

为什么我们去建一套自己的缓存而不是使用系统内置的呢？

我估计很多人都跟我想的一样，因为觉得实现缓存是一种非常简单的事情，如果要重新造一个轮子的话，这是一个非常易于上手的项目，然后我们就开始实现各种 XXXCache 了。

对我而言，虽然我很早就开始写 iOS App，但是却一直不知道有 NSURLCache/NSCache 这样的存在，然后又因为觉得这个非常简单啊，所以在我的很多 App 中，都有不同方式实现的 Cache。直到前两年我看到了这篇文章，[NSURLCache](http://nshipster.cn/nsurlcache/)，我才焕然大悟，原来我白折腾了这么多年。

事实上，只要两行代码就可以配置完 App 中所有请求的缓存，剩下的只要依靠 `http` 响应头中 `Cache-Control` 的设置就可以完成自动的缓存和管理了。

    - (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
    {
      NSURLCache *URLCache = [[NSURLCache alloc] initWithMemoryCapacity:4 * 1024 * 1024
                                                           diskCapacity:20 * 1024 * 1024
                                                               diskPath:nil];
      [NSURLCache setSharedURLCache:URLCache];
    }

由于, NSURLCache 可以同时缓存在内存和磁盘上，而且他还会根据 `Cache-Control` 以及系统资源的压力而自动管理，我现在将本地所有的缓存都替换了。

但是在使用的过程中，我却发现了几个坑要注意:

* 如果一个请求的响应内容的大小超过了 NSURLCache 中对应磁盘大小的 5%, 他就不会被缓存；我之前一直没有找到这条规则，但是我有一个图片的请求永远都没法缓存下来（我设置的 NSURLCache 中磁盘大小是 10MB, 但是这个图片有 3.8 MB）, 直到我在 `optional func URLSession(_ session: NSURLSession, dataTask dataTask: NSURLSessionDataTask, willCacheResponse proposedResponse: NSCachedURLResponse, completionHandler completionHandler: (NSCachedURLResponse?) -> Void)` 中看到了说明

    > The response size is small enough to reasonably fit within the cache. (For example, if you provide a disk cache, the response must be no larger than about 5% of the disk cache size.)
    
* 如果这个请求的响应头中有 `Transfer-Encoding: Chunked`, 那他也不会缓存；

事实上，在`optional func URLSession(_ session: NSURLSession, dataTask dataTask: NSURLSessionDataTask, willCacheResponse proposedResponse: NSCachedURLResponse, completionHandler completionHandler: (NSCachedURLResponse?) -> Void)` 中对于缓存的条件还有一些限制，比如 `NSURLSessionConfiguration` 中没有禁止缓存，`NSMutableURLRequest` 中没有禁止缓存等。这个方法属于 `NSURLSessionDataDelegate`, 但是有时你会发现 `NSURLSession` 中设置的 `delegate`后，一个回调函数都没有被调用

> 当你使用类似 `func dataTaskWithURL(_ url: NSURL, completionHandler completionHandler: (NSData?, NSURLResponse?, NSError?) -> Void) -> NSURLSessionDataTask` 这些带有 `completionHandler` 的方法时，delegate 将不会被调用。

这一点确实很奇怪，因为这个原因，当我使用带有 `completionHandler` 时，我甚至都不能通过 `willCacheResponse` 来强制缓存了。

除此之外，我还发现了 NSULRRequest 中对请求超时时间的设置几乎是没用的，当你设置 `timeoutInterval` 为很小的值，比如 `10s` 的时候，他不会起任何作用。Google 了一圈，有人说貌似这时 Apple 故意这么设计的，你不能指定小余 `240s` 的数字, 但是有人说这个已经改过了，也有人说这个限制只针对 POST 请求，可以参考这几个链接：

* [NSURLRequest Timeout IOS](http://stackoverflow.com/questions/11718256/nsurlrequest-timeout-ios)
* [NSMutableURLRequest timeout interval not taken into consideration for POST requests](http://stackoverflow.com/questions/1466389/nsmutableurlrequest-timeout-interval-not-taken-into-consideration-for-post-reque)
* [Timeout for NSMutableURLRequest not working](http://stackoverflow.com/questions/10408185/timeout-for-nsmutableurlrequest-not-working)

但是我发现我设置的超时时间都没有起过作用, 现在唯一的解决办法就是去设置一个 `NSTimer` 然后手动取消请求了。






