# 杰尼龟影视

一个可部署到 GitHub Pages 的纯前端影视聚合页面。

## 部署到 GitHub Pages

1. 新建 GitHub 仓库。
2. 将本目录下的 `index.html`、`.nojekyll`、`README.md` 上传到仓库根目录。
3. 打开仓库 `Settings -> Pages`。
4. Source 选择 `Deploy from a branch`。
5. Branch 选择 `main`，目录选择 `/root`，保存。
6. 等待 Pages 生成访问地址。

## 说明

- 本项目是静态网页，GitHub Pages 只托管前端文件。
- 在线播放依赖浏览器端 HLS 播放能力和采集源返回的播放地址。
- 采集接口跨域访问通过页面内的在线代理通道完成，不需要安装浏览器插件。
