# 奇怪的 UITableView

从刚开始做 iOS 开发的时候开始，UITableView 就一直是被我用的做多的 UIKit 控件，这么多年过去了，有时还是会在使用 UITableView 的过程中遇到一些奇怪的问题。

在大部分的开发过程中，每当遇到 UITableView 的奇怪的的现象，我总寄希望于自定义的 UITableViewCell, 也就是直接继承一个 UITableViewCell, 然后在上面添加自己的控件，这样的做法屡试不爽。但是过后，有时会在想，到底是什么原因会造成这样奇怪的问题呢？

## Grouped UITableView 和 奇怪的 Section Header 

当我们使用 UITableViewStyle.Grouped 的样式来创建一个 UITableView 的时候，而同时又去修改某个 Section 中的 header 高度时，就会出现很奇怪的现象:

> 在 UITableViewStyleGrouped 中，你不能直接把 heightForHeaderInSection 修改为一个很小的值 （小余 22.0）

默认的情况下， heightForHeaderInSection 和 heightForFooterInSection 都是 `22.0`，我们可以在 UITableViewDelegate 中来设置这两个值

    override func tableView(tableView: UITableView, heightForHeaderInSection section: Int) -> CGFloat {
        return 60.0
    }

这样的确起效果了，然而，当你指定的高度为 `10.0` 时，显示的时候却仍然是 22.0 的高度。

    override func tableView(tableView: UITableView, heightForHeaderInSection section: Int) -> CGFloat {
        return 10.0
    }

没错，就是怎么奇怪，当你设置小余 `22.0` 的高度时候就是无效的。

解决的办法也很奇葩， **你必须同时指定一下 heightForFooterInSection, 比如指定一个非常小的值 (0.0001)**。

    override func tableView(tableView: UITableView, heightForFooterInSection section: Int) -> CGFloat {
            return 0.0001
    }
    
这样的 Section Header 就显示正确了。

> 这个问题只有在使用 UITableViewStyle.Grouped 来创建 UITableView 的时候才会出现，而默认的样式中随意指定 Section Header 高度都是可以的。

设置 heightForFooterInSection 还顺带解决了另一个问题。有时我们会看到一个 UITableView 只有几行有内容（并没有撑满一屏）的时候，UITableView 会为剩余空白的地方仍然绘制分割线。而当你设置了 heightForFooterInSection 之后，他们就不会出现了，只会显示空的位置。

## UITableViewCell 的分割线 

为什么 UITableViewCell 的分割线不能从左边直接开始而非要留一些空呢？ 如果我们看看系统自带的 App, 他们中的分割线都是离左边有些距离的。似乎这就是现在 iOS 的设计风格。

然而，我遇到的所有设计师都是会把这根线撑满整个 UITableViewCell 的宽度的。所以我做过的 App 中所有的 UITableViewCell 都需要改掉这跟线的位置。 在 `iOS7` 中，只要直接修改 `UITableView.separatorInset` 和 `UITableViewCell.separatorInset` 就可以控制分割线的位置了。比如:

    tableView.separatorInset = UIEdgeInsetsZero
    tableViewCell.speratorInset = UIEdgeInsetsZero

但是 iOS8/iOS9 这样却没用了, 因为从 iOS 8 开始，又有了一个 `layoutMargin`，所以得改成:

    self.separatorInset = UIEdgeInsetsZero
        if #available(iOS 8.0, *) {
            self.layoutMargins = UIEdgeInsetsZero
        }
        
**UITableView/UITableViewCell** 中都得这样设置。而且奇怪的是， `iOS 8` 中还得设置 `tableViewCell.preservesSuperviewLayoutMargins = false` 才可以。而 `iOS 9` 却不设置也可以。

    extension UITableViewCell {
    /// 让分割线贴到左边
        func cx_fixSeperator() {
            self.separatorInset = UIEdgeInsetsZero
            if #available(iOS 8.0, *) {
                self.layoutMargins = UIEdgeInsetsZero
                self.preservesSuperviewLayoutMargins = false /// 只有 iOS8 需要这样
            }
        }
    }

### 使用 UIAppearance

由于一般 App 中所有的 UITableView 风格都是统一的，我想应该直接可以通过 UIAppearance 来控制所有的分割线位置了吧，比如在 `func application(application: UIApplication, didFinishLaunchingWithOptions launchOptions: [NSObject: AnyObject]?) -> Bool` 中设置他：

        UITableView.appearance().separatorInset = UIEdgeInsetsZero
        if #available(iOS 8.0, *) {
            UITableView.appearance().layoutMargins = UIEdgeInsetsZero
        }
        UITableViewCell.appearance().separatorInset = UIEdgeInsetsZero
        if #available(iOS 8.0, *) {
            UITableViewCell.appearance().layoutMargins = UIEdgeInsetsZero
        }
        if #available(iOS 8.0, *) {
            UITableViewCell.appearance().preservesSuperviewLayoutMargins = false
        }

**但是我又发现这样做没啥作用！？原因不明**

### 去掉一个 UITableViewCell 的分割线的方法

通过 `UITableView.separatorStyle = UITableViewCellSeparatorStyle.None`  可以去掉所有的分割线，那要是想去掉 **其中一个** UITableViewCell 的分割线该怎么办呢? 其实也就是这时这个 Cell 的 `separatorInset/layoutMargins`, 可以设置偏移到屏幕外面的距离去:

    /// 删除分割线
    func cx_removeSeperator() {
        self.separatorInset = UIEdgeInsetsMake(0.0, 1000.0, 0.0, 0.0)
        if #available(iOS 8.0, *) {
            self.layoutMargins = UIEdgeInsetsMake(0.0, 1000.0, 0.0, 0.0)
        }
    }
    
但是你会发现有时这样做也是没用的，在 UITabelViewStyle.Grouped 的 UITableView 中，由于 UITableViewHeaderFooterView 上就会有一根分割线，所以以这样的方式来删除 section 中最后一个 cell 的分割线时，其实是没用的。

同时，我发现用这种方法后会让 UITableView.textLabel 的内容偏移到后面去，所以这并不是一个好的方法。

## 被遮挡的子视图背景色

当 UITableViewCell 中增加一些子视图的时候，有时点击 Cell 的时候就会发现有些子视图的背景色不见了。

![](http://7vihfk.com1.z0.glb.clouddn.com/Simulator%20Screen%20Shot%202016%E5%B9%B43%E6%9C%8830%E6%97%A5%20%E4%B8%8B%E5%8D%882.37.42.png)

这是由于当点击 Cell 的时候，子元素会变成 Hightlighted 状态，而选中之后又会变成 Selected 状态，UITableViewCell 的状态会传递给子视图。有些 View (比如 UIButton, UILabel 等) 会根据状态呈现不同的样式的时候，他们就会在 UITableViewCell 被点击和选择的时候被呈现出不同的样子了。

解决的办法是重写 UITableView 的 `- setSelected:animated:` 和 `- setHighlighted:animated:` 方法，并在这里设置子视图的样式。

	override func setSelected(selected: Bool, 
		animated: Bool) {
        super.setSelected(selected, animated: animated)
        self.button.backgroundColor = UIColor.blackColor()

    }
	override func setHighlighted(highlighted: Bool, 
		animated: Bool) {
	     super.setSelected(selected, animated: animated)
	     self.button.backgroundColor = UIColor.blackColor()
	 }

或者就干脆把 `selectionStyle` 改成 `UITableViewCellSelectionStyle.None` 吧。



我印象中还有一些奇怪的坑在这个 UITableView 中，只是一时想不起来了...
    


