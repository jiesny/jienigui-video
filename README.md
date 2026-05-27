# 杰尼龟影视

一个部署在 GitHub Pages 上的纯前端影视聚合页面。

线上地址：

https://jiesny.github.io/jienigui-video/

## 本地预览

在项目目录运行：

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

然后打开：

```text
http://127.0.0.1:4173/index.html
```

## 部署

本项目通过 GitHub Actions 自动部署到 GitHub Pages。

常用命令：

```powershell
git add index.html README.md HANDOFF.md
git commit -m "Update site"
git push
```

推送到 `main` 后会自动触发 Pages 部署。

## 当前采集源

默认聚合以下采集源：

- 非凡资源
- 电影天堂资源
- 优质资源库
- 如意资源
- 鸭鸭资源
- 西瓜资源

采集源配置在 `index.html` 的 `DEFAULT_SOURCES`。

## 维护文档

后续迭代前请先阅读：

[HANDOFF.md](./HANDOFF.md)
