# 探究 Promise 对象

Promise 对象的出现归根到底是为了拯救陷落在无数闭包大括号中的我们。虽然这个笑话经常出现在吐槽 Javascript 的段子中，但是在现在 Objective-C 和 Swift 充斥着无数滥用闭包/Block 的 iOS 中，难道不是一样的么。

为了避免在异步嵌套代码中出现一层又一层的大括号，天才的程序员们发明了 Promise 对象，用一种面向对象的方式来解决多层闭包嵌套的问题。以下是从 `PromiseKit.org` 中抄袭来的一段代码:

    login()
    .then {

        // our login method wrapped an async task in a promise
        return API.fetchKittens()
    
    }.then { fetchedKittens in
    
        // our API class wraps our API and returns promises
        // fetchKittens returned a promise that resolves with an array of kittens
        self.kittens = fetchedKittens
        self.tableView.reloadData()
    
    }.error { error in
    
        // any errors in any of the above promises land here
        UIAlertView(…).show()
    
    }

`login()` 作为一个封装了异步调用的函数，他返回了一个 `Promise` 对象，而这个 Promise 对象有一个 `then` 方法，他传入一个闭包并返回一个新的 `Promise` 对象，而这个 `Promise` 对象又可以调用他的 `then` 方法...， 这样通过很多 `then` 方法来实现多层的联级调用。

这段文字看上去比代码更加绕口，其实就是 一个 Promise 对象通过 `then` 方法传入一个闭包，他其实是告诉这个 Promise 对象，完成当前的操作后，后面将干什么。

## 构造 Promise 对象

Promise 对象在构造时会传入一个闭包，一般他应该是一段异步操作代码，当这段操作完成时，要么调用 `resolve` 方法用来告诉 Promise 对象我正确操作完成了，要么调用 `reject` 告诉 Promise 对象有地方出错了。

    AWPromise<NSData>(block: { (resolve, reject) in
                print("start")
                dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), {
                    print("wait")
                    NSThread.sleepForTimeInterval(3.0)
                    dispatch_sync(dispatch_get_main_queue(), {
                        print("wait complete")
                        resolve(NSData())
                    })
                    
                })
            })

在 Promise 构造函数内部，`resolve` 调用的时候，会保存运行的结果，并修改状态为 `FullFilled`；`reject` 调用的时候，会保存出错信息，并修改状态为 `Rejected`。 以下是 Promise 对象的构造函数

    typealias ResolveFunc = (T) -> ()
    typealias RejectFunc = (NSError) -> ()
    typealias PromiseBlock = (resolve:ResolveFunc,reject:RejectFunc) -> ()
    /// 用来保存后续操作
    var f_then : ResolveFunc? = nil
    /// 用来保存错误处理
    var f_error : RejectFunc? = nil
    /// 状态
    var state:AWPromiseState = .Panding
    /// 运行的结果
    var result : AWResult<T>? = nil
    init(@noescape block:PromiseBlock){
        block(resolve: { (t) in
            self.complete(t)
        }) { (error) in
            self.fail(error)
        }
    }
    func complete(t:T) -> () {
        self.result = AWResult.Success(t)
        state = .FullFilled
        f_then?(t) /// 如果 promise 内是同步函数， f_then 是还未被赋值时就被 complete 调用的
    }
    func fail(error:NSError) -> () {
        self.result = AWResult.Error(error)
        state = .Rejected
        f_error?(error)
    }

## Promise 对象的状态

Promise 对象会有三种状态:

* Panding: 刚开始构造函数，其中的闭包还没完成的时候
* FullFilled: 操作完成了；
* Rejected: 操作完成但是出错了；

## 为什么可以实现联级调用

每个 `then` 返回一个新的 Promise 对象，你又可以调用这个 Promise 对象的 `then` 方法，从而实现联级调用。

当调用 `then` 的时候，传入的闭包参数将会被 `Promise` 对象保存下来，并在当前这个 Promise 完成自己的操作后，执行后续操作时被调用。

所以，在每个 `Promise` 对象中含有一个非常重要的属性 `f_then`, 他将在自己的任务完成后被调用，由于他实际上包含了 `then` 方法中传递进来的操作代码块，所以实际上，`f_then` 的调用就是执行了之前 `then` 传递来的代码块。

所以正确的流程是

* 构造 Promise 对象时传入异步代码块;
* 调用 `then` 方法为当前的 `Promise` 对象保存下一步需要操作的代码块，同时他返回一个新的 `Promise` 对象，并重复这一过程；
* 每个 Promise 对象的代码块执行完成的时候，他会调用 `f_then` 操作后面的过程。

由于每个 Promise 对象构造方法中传入的都是异步代码块，所以当进行 Promise **对象完成构造** 时，其中的代码应该还没有被执行完成，所以肯定是后续的 `then` 方法会比构造方法中的异步代码块先执行（未验证这种说法，但是这并不会成为问题，因为我们下面会处理构造方法闭包参数中使用同步代码的情况）。当构造参数闭包中的异步代码终于完成时，我们的 Promise 对象已经持有了下一步继续操作所需的代码块 `f_then`，所以通过对他的调用就完成了后续代码的调用。

### then 中嵌套另一个异步过程的情况

如果要在 `then` 中使用另一个异步代码时，我们必须构造另一个 `Promise` 对象，并在其中完成异步代码，就和创建第一个 `Promise` 对象的方法一样。

这样，`then` 方法将有另一种形式的参数，也就是他的闭包参数类型中应该返回一个 `Promise` 类型。

所以，他其实有两种形式:

	func then<U>(f: (T throws -> U)) -> AWPromise<U>
	func then<U>(f : (T throws -> AWPromise<U>)) -> AWPromise<U>

恰好对应了 `flat/flatMap` 的写法。

## then 内包含非异步代码怎么办

前面我们的假设都是建立在一个前提下的：

当我们调用 Promise 对象的 `then` 方法用来注册下一步操作的代码块时，Promise 构造方法中传入的异步代码还未完成调用。所以当异步操作完成时， `f_error` 已经知道该在下一步做什么了。

但是有没有一种可能是，异步操作比 `then` 调用先完成呢。我觉得应该是有可能的，如果后续的 `then` 方法调用中有一处阻塞了主线程呢，那异步操作可能会先完成。

还有一种更直接的做法是，构造 Promise 对象的闭包中，只有同步的代码，那他可以肯定会在 `then` 前完成（在 Promise 对象构造中就完成了）。

这种时候我们就没法正确的调用 `f_then`,因为他还没有被赋值。

为了解决这种情况，就需要对 `then` 调用做些处理，当`then` 调用时，如果 `Promise` 操作还没完成，他就需要通过 `f_then` 来保存下一步操作代码块。如果 Promise 已经完成了自己的工作了，我们就直接调用 `then` 传递来的代码块，将结果传递出去。

当然我们不得不说，在 Promise 构造函数中的闭包中传递同步代码是一种很蛋疼的行为，因为你完全没必要这么做，把他们放在 `promise/then` 的外部执行不是更加清楚么。

## 错误处理

在 Promise 对象中有一个 `error` 方法，传递一个闭包参数，用来处理发送异常时的情况。 `error` 不会返回新的 `Promise`, 所以不能被联级调用，他应该在整个调用链的最后被调用，只要操作链中有一处抛出错误，就会调用 `error` 传递来的代码块（他被保存在 `f_error` 中）

    .error { (error) in
                print("\(error.domain)")
    }

在构造 Promise 的闭包中，我们通过 `reject` 函数调用来抛出一个错误。

    AWPromise<NSData>(block: { (resolve, reject) in
                print("start")
                dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), {
                    print("wait")
                    NSThread.sleepForTimeInterval(3.0)
                    dispatch_sync(dispatch_get_main_queue(), {
                        print("wait complete")
                        let error = NSError(domain: "test error", code: 1, userInfo: nil)
                        reject(error)
                    })
                    
                })
            })

在 `then` 代码中，我们没法调用 `reject` 方法，最简单的 `throw` 一个异常。

    .then { (data) -> [String:String] in
          throw AWPromiseError.PromiseError("1 error")
    }

但是我们每个 `then` 产生的都是一个全新的 `Promise` 对象，而且我们要求 `error` 必须在调用链的最后被调用，所以错误代码其实只在最后一个 `Promise` 对象上面保存着。

为了能顺着调用链执行错误处理，我们必须在每个 `Promise` 对象中都持有下一个 `Promise` 对象的错误处理方法，这样当调用链中发生异常时，每个 Promise 对象会调用错误处理方法, 直到最后一个 Promise 中正在开始真正的处理这个错误（因为只有他持有 f_error 操作块）。

所以在 `then` 中和处理 `f_then` 一样，将新的 Promise 对象的 `reject` 操作赋值给 **当前对象** 的 `f_error`。 在 `then` 中类似这样:

    func then<U>(f: (T throws -> U)) -> AWPromise<U> {
            return AWPromise<U>(block: { (resolve, reject) in
                self.f_error = reject /// 错误处理
                self.f_then = { (t:T) -> () in /// 下一步操作
                    let u = f(t)
                    resolve(u)
                }
            })
    }
    
## 完整使用 Promise 对象进行网络请求的例子

下面的例子将依次发起两次网络请求，第一次访问 `https://www.zhihu.com`, 在获取到内容后，再发起第二次网络请求 `http://www.apple.com`。两次请求都会输出获取到的内容，并在两次都完成后输出 `All Completed`。

    func test_http_promise() {
        /// NSURLSession 的一些配置
        let queue = NSOperationQueue()
        let sessionConfiguration = NSURLSessionConfiguration.defaultSessionConfiguration()
        sessionConfiguration.timeoutIntervalForRequest = 3.0
        
        /// 1. 构造第一个请求
        AWPromise<NSData> (block:{ (resolve, reject) in
            let session = NSURLSession(configuration: sessionConfiguration, delegate: nil, delegateQueue: queue)
            let task = session.dataTaskWithURL(NSURL(string:"https://www.zhihu.com")!, completionHandler: { (data, response, error) in
                dispatch_sync(dispatch_get_main_queue(), { 
                    if let error = error {
                        reject(error)
                    }
                    else if let data = data {
                        resolve(data)
                    }    
                })
            })
            task.resume()
        })
        /// 2. 第一个请求返回结果
        .then { (data) -> () in
            print("First Request")
            let str = String(data: data, encoding: NSUTF8StringEncoding)
            print(str)
        }
        /// 3. 构造第二个请求
        .then { () -> AWPromise<NSData> in
            return AWPromise<NSData>(block: { (resolve, reject) in
                let session = NSURLSession(configuration: sessionConfiguration, delegate: nil, delegateQueue: queue)
                let task = session.dataTaskWithURL(NSURL(string:"https://www.apple.com")!, completionHandler: { (data, response, error) in
                    dispatch_sync(dispatch_get_main_queue(), { 
                        if let error = error {
                            reject(error)
                        }
                        else if let data = data {
                            resolve(data)
                        }    
                    })
                })
                task.resume()
            })
        }
        /// 4. 第二个请求返回结果，这里先转换到 String
        .then { (data) -> String in
            let str = String(data: data, encoding: NSUTF8StringEncoding)!
            return str
        }
        /// 5. 得到第二个请求的结果的字符串
        .then { (str) -> () in
            print("Second Request")
            print(str)
            print("All Completed")
        }
        /// 6. 用来处理错误
        .error { (error) in
            debugPrint(error)
        }
    }
    
* 当第一个请求构造的时候，位于 `1` 的位置，我们创建一个 Promise 对象，并传入一个闭包，这个闭包是一个异步网络请求;
* 当这个异步请求完成的时候，调用这个 Promise 对象的 `then` 方法，这时位于 `2`, 他会得到一个 `NSData` 内容，是(dataTaskWithRequest)回调时的 `NSData`;
* 我们还想要做后续操作，所以可以继续使用 `then`, 由于下面一步并不需要来自前面的结果，所以 `then` 中的闭包并没有传递来参数，这时在 `3` 的位置，我们要构建第二个异步网络请求，访问 `https://www.apple.com`， 因为他又是一个异步请求，所以我们又要构造一个 Promise 对象用来封装这个过程。
* 第二个请求返回的时候来到 `4`, 得到了 `NSData` 数据，为了让代码看上去更清晰一点，我们在这里没有做更多的处理，只将他转换到 `String` ，然后将这后面工作划分到下面一步完成。
* `5` 的时候得到了前面传递来的 `String`, 输出来，这样我们完成了全部流程了；
* 如果将第二个请求的地址改为 `https://www.google.com`, 由于一些奇怪的因素，第二个请求会发生错误， 这时会到 `6`，输出错误信息了。

其实我们可以发现，其中很多步是可以合并的，比如 `2` 和 `3` 可以合并，直接在 `2` 中构造下一步的 Promise 对象， `4` 和 `5` 可以合并，之所以将他们分开，是为了让每个步骤的代码块更加清晰，事实上使用多少层 `then` 的链式调用完全取决于你想以多大的规模来区分每一步。
    
## 这里实现的 Promise 对象全部代码

* [AWPromise.swift](https://gist.github.com/adow/8e638a907ecb1a476f783663cb76b5db)

## 何去何从

我们在这里构造了一个 `Promise` 对象，用来将多层的异步代码嵌套以更直观的方法写出来。他可以实现:

* 封装异步/同步代码;
* 错误处理;

虽然实现了这些功能，代码看看整个 `AWPromise.swift` 的代码实现却一点也不谈不上简洁 （虽然只有 200 行不到的代码）,隐约中还感到某些地方有哪些问题却还发现不了。这个 Promise 远远达不到 [PromiseKit](http://promisekit.org/) 的强大和优雅，所以我写下本文的目的在于探究 Promise 对象的实现过程。如果真的要在项目中使用 Promise 的话，强烈推荐使用 `PromiseKit`。

我们用 Promise 对象来转换异步代码的写法，说白了是为了让异步代码看上去更加的直白而已（或者叫异步代码扁平化处理），其实使用 Promise 对象所带来的直观感受远远不如另外两项技术带来的更加直观。

在 `Python` 和 `ECMAScript 6` 中，由于有 `Generator`, `Yield` 的存在，最好配合函数的属性标签, 可以将异步代码写成完全的扁平化。

比如，使用 `Python` 中著名的 `Tornado` 框架的话，可以将一个异步函数改为下面这样:

    @gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch("http://example.com")
        self.write(response)
        
通过 `yiled` 关键字将当前函数转换为 `Generator`，只有当 `http_client` 获取到内容并赋值给 `response` 之后，后续的代码才会继续执行。

甚至到了 `Python3` 和 `ECMAScript 7` 中， 都有 `async/await` 关键字，专门用来实现异步代码的扁平化处理（其实就是 Generator 和 Yield 的语法糖）。

    var asyncReadFile = async function (){
      var f1 = await readFile('/etc/fstab');
      var f2 = await readFile('/etc/shells');
      console.log(f1.toString());
      console.log(f2.toString());
    };
    
Swift 中什么时候才能引入这样的特性呢？
    
## 参考 

* [Promise: 给我一个承诺，我还你一个承诺](http://zhuanlan.zhihu.com/prattle/20209175)
* [Promises in Swift](https://medium.com/@robringham/promises-in-swift-66f377c3e403#.4wtrrnmmr)
* [大白话讲解Promise（一）](http://www.cnblogs.com/lvdabao/p/es6-promise-1.html)
* [如何处理 Swift 中的异步错误](http://gold.xitu.io/entry/56c52be6d342d30053c8a254)
* [Swift 烧脑体操（五）- Monad](http://www.infoq.com/cn/articles/swift-brain-gym-monad?utm_campaign=infoq_content&utm_source=infoq&utm_medium=feed&utm_term=global)
* [聊一聊单子（Monad）](http://swiftggteam.github.io/2015/10/30/lets-talk-about-monads/)
* [Functor、Applicative 和 Monad](http://blog.leichunfeng.com/blog/2015/11/08/functor-applicative-and-monad/#jtss-tsina)
* [Swift 数组中 Map,FlatMap,Filter,Reduce的使用](http://www.cocoachina.com/swift/20160210/15068.html)
* [为Swift编码引入map()和flatMap(), map those arrays](http://zyden.vicp.cc/map-those-arrays/?)


```
MING-ARTICLE-CONFIG

{
    "article_title": "探究 Promise 对象",  
    "article_subtitle":"实现一个 Swift 下的 Promise ",
    "article_theme": "default", 
    "article_link": "awpromise.html",
    "article_publish_date":"2016-05-09", 
    "article_cover_photo":"http://7vihfk.com1.z0.glb.clouddn.com/photo-1457369804613-52c61a468e7d.jpeg", 
    "article_category":"code",
    "article_comments":1,
    "article_css": {}
}

```


