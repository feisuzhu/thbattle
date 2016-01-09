# Python-getting-started

一个简单的使用 Flask 的 Python 应用。
可以运行在 LeanEngine Python 运行时环境。

## 本地运行

首先确认本机已经安装 [Python](http://python.org/)2.7 运行环境。然后执行下列指令：

```
$ git clone git@github.com:leancloud/python-getting-started.git
$ cd python-getting-started
```

准备启动文件:

```
$ cp start.sh.example start.sh
$ chmod +x start.sh
```

将 app id 等信息更新到 `start.sh` 文件中：

```
export LC_APP_ID=<your app id>
export LC_APP_KEY=<your app key>
export LC_APP_MASTER_KEY=<your master key>
```

启动项目：

```
$ ./start.sh
```

应用即可启动运行：[localhost:3000](http://localhost:3000)

## 部署到 LeanEngine

首先确认本机已经安装 [LeanCloud 命令行工具](https://leancloud.cn/docs/cloud_code_commandline.html)。

部署到测试环境：
```
$ avoscloud deploy
```

部署到生产环境：
```
$ avoscloud publish
```

## 相关文档

* [LeanEngine 指南](https://leancloud.cn/docs/leanengine_guide.html)
* [Python SDK 指南](https://leancloud.cn/docs/python_guide.html)
* [Python SDK API](https://leancloud.cn/docs/api/python/index.html)
* [命令行工具详解](https://leancloud.cn/docs/cloud_code_commandline.html)
* [LeanEngine FAQ](https://leancloud.cn/docs/cloud_code_faq.html)
