# 杰尼龟影视交接与使用文档

## 1. 项目概览

杰尼龟影视是一个纯前端影视聚合站，核心文件是 `index.html`，无自建后端。页面通过公共 CORS 代理访问采集接口，适合部署在 GitHub Pages / Cloudflare Pages 这类静态托管环境。

本地目录：

```text
D:\项目资料\杰尼龟影视
```

线上入口：

```text
https://jiesny.github.io/jienigui-video/
https://jienigui-video.pages.dev/
```

GitHub 仓库：

```text
https://github.com/jiesny/jienigui-video
```

## 2. 运行与部署

本地预览：

```powershell
python -m http.server 4173 --bind 127.0.0.1
```

访问：

```text
http://127.0.0.1:4173/index.html
```

提交部署：

```powershell
Copy-Item -LiteralPath index.html -Destination v1.7.html
git add index.html v1.7.html README.md HANDOFF.md
git commit -m "Your change summary"
git push
```

查看 GitHub Pages 工作流：

```powershell
& 'C:\Users\19255\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe' run list --repo jiesny/jienigui-video --limit 3
```

Cloudflare Pages 当前绑定 GitHub 仓库；推送到 `main` 后，GitHub Pages 和 Cloudflare Pages 都应触发更新。Cloudflare 的完成时间以 Cloudflare 后台为准。

## 3. 主要文件

- `index.html`：主站点，包含 UI、主题、采集源、聚合、搜索、详情播放、友链入口等逻辑。
- `v1.7.html`：当前主页面备份，必须和 `index.html` 同步。
- `.github/workflows/pages.yml`：GitHub Pages 自动部署工作流。
- `.nojekyll`：避免 GitHub Pages 走 Jekyll 处理。
- `README.md`：简短项目说明。
- `HANDOFF.md`：交接与使用文档。

## 4. 当前访问入口与友链

站点设置底部有“友链入口”，对应：

| 入口 | 地址 | 标签 | 备注 |
| --- | --- | --- | --- |
| 杰尼龟影视（GitHub） | `https://jiesny.github.io/jienigui-video/` | 科学上网 | 适合科学上网环境，推荐使用香港、新加坡节点；非凡资源约 6 分钟有广告，鸭鸭资源可能有小广告浮窗。 |
| 杰尼龟影视（Cloudflare） | `https://jienigui-video.pages.dev/` | 国内直连 | 适合国内直连环境；电影天堂、非凡资源直连稳定性可能波动。 |

友链配置入口：

```js
const FRIEND_LINKS = [...]
```

## 5. 当前采集源与优先级

采集源配置位于：

```js
const DEFAULT_SOURCES = [...]
```

当前顺序即默认优先级：

| 优先级 | 名称 | ID | 格式 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 电影天堂资源 | `source_dytt` | XML | 高优先级 |
| 2 | 优质资源库 | `source_yzzy` | JSON | 高优先级，使用 `inc/apijson.php`，可返回完整播放地址 |
| 3 | 如意资源 | `source_ryzy` | XML | 高优先级 |
| 4 | 西瓜资源 | `source_xigua` | JSON | 高优先级 |
| 5 | 非凡资源 | `source_ffzy` | JSON | 低优先级，播放约 6 分钟有广告 |
| 6 | 鸭鸭资源 | `source_yaya` | JSON | 低优先级，可能有小广告浮窗 |

低优先级源配置：

```js
const LOW_PRIORITY_SOURCE_IDS = ['source_ffzy', 'source_yaya'];
```

后续新增源时，先用 PowerShell 验证：

```powershell
Invoke-WebRequest -Uri '接口地址?ac=list' -UseBasicParsing -TimeoutSec 20
Invoke-WebRequest -Uri '接口地址?ac=detail&pg=1' -UseBasicParsing -TimeoutSec 20
```

XML 源对象加 `format: 'xml'` 作为展示标识；实际解析由 `parseApiResponse()` 和 `parseXmlData()` 处理。

## 6. 搜索与聚合逻辑

搜索已从串行改为并发增量：

- `handleGlobalSearch()`：创建搜索批次 `searchRunId`，所有源并发请求，任意源返回后立即更新搜索结果。
- `searchCompletedCount / searchTotalCount / searchPendingSources`：用于展示搜索进度。
- `fetchList(source, options)`：支持透传 `timeoutMs`。
- 搜索场景使用 `timeoutMs: 5000`；首页、分类、自检仍使用默认 10 秒。
- `localScanSearch()`：当源不支持关键词搜索时走本地扫页兜底；普通源最多扫 2 页。鸭鸭资源接口明确返回“暂不支持搜索”，首轮只扫前 2 页参与进度，随后后台从第 3 页起最多再扫 40 页，命中后追加到当前结果，不阻塞首批搜索。
- `groupSearchResults(items)`：按片名和年份聚合来源。
- `sortBySourcePriority(items)`：保证非凡、鸭鸭排到来源列表后面。

搜索记录：

- 本地搜索记录保存在 `localStorage`。
- 配置项：

```js
const SEARCH_HISTORY_KEY = 'jng_search_history';
const MAX_SEARCH_HISTORY = 12;
```

- 搜索框聚焦/点击/输入时显示历史。
- 支持点击复搜、单条删除、清空全部。

## 7. 分类、首页与详情

分类配置：

```js
const STANDARD_CATEGORIES = [...]
const FILTER_GROUPS = {...}
const COMMON_FILTERS = {...}
```

核心函数：

- `fetchCategories(source)`：拉取某个源分类。
- `fetchAllCategories()`：并发拉取全部源分类。
- `fetchStandardCategoryList(source, standardCategory, page)`：将源内小分类映射到大类。
- `fetchAggregatedList(standardCategory, page)`：跨源拉取、合并、去重、排序。
- `groupVideosByTitle(items)`：同名同年影片聚合来源。

首页和分类页现在会保留 `sources`，进入详情后可以展示多个可用来源。

详情相关函数：

- `openSearchResult(item)`
- `openAggregatedDetail(video)`
- `openDetailFromVideo(video, source, push)`
- `selectDetailSource(index)`

## 8. 播放线路处理

播放 URL 解析：

```js
parsePlayUrls(rawUrlStr, sourceId)
```

特殊规则：

- 西瓜资源：跳过第一组线路，只保留后面的可用线路。
- 非凡资源：跳过第一组分享页线路，只保留 m3u8 线路。
- 鸭鸭资源：接口本身返回 `yym3u8`，不需要跳过。
- XML 源：`parseXmlData()` 只提取 `flag` 包含 `m3u8` 的 `dd`。

域名替换：

```js
const URL_REPLACEMENTS = [...]
```

如遇某源播放失败，优先检查 `vod_play_url` 是否被正确解析，以及是否需要新增旧域名替换规则。

## 9. 代理与 Cloudflare Pages 注意事项

静态托管无法运行后端代理，页面依赖公共 CORS 代理：

```js
const PROXIES = [...]
```

当前包括：

- `Corsproxy.io`
- `AllOrigins`
- `Codetabs`

`fetchWithFallback(targetUrl, options)` 会按当前代理和备用代理逐个尝试。`parseApiResponse()` 会识别 HTML 错误页、403、Cloudflare 拦截页，避免把错误页当 XML 空列表。

已知差异：

- GitHub Pages 环境下部分接口更稳定。
- Cloudflare Pages 国内可直连，但部分代理/源可能返回 403、空列表或波动。
- 如果 Cloudflare 入口自检异常而 GitHub 正常，优先检查公共代理返回内容，而不是直接判定采集源失效。

## 10. 主题与移动端布局

主题配置：

```js
const THEMES = [...]
```

当前主题：

- 暗夜玫瑰
- 深海蓝
- 松林绿
- 暖影橙
- 纯白花嫁
- 透明玻璃

注意：

- 纯白花嫁使用纯白、柔粉、淡金提示风格。
- 透明玻璃在手机端关闭背景和卡片流动动画，避免频繁闪动；仍保留玻璃模糊质感。
- 移动端顶部布局为 logo、搜索框、设置键一行。
- 竖屏详情页播放器占满屏宽，详情内容在下方滚动；详情面板使用受控 overflow，避免长内容撑出右侧边框。
- 横屏详情页为左侧播放器、右侧详情栏。

## 11. 浏览器历史与路由

页面使用 `history.pushState/replaceState` 支持：

- 首页
- 分类
- 搜索
- 设置面板
- 详情弹窗

相关函数：

```js
routeState()
routeUrl()
pushRoute()
replaceRoute()
applyRouteState()
stateFromUrl()
```

路由 state 会保存 `scrollTop`，打开详情前先记录 `#app` 滚动位置，关闭详情或浏览器返回后通过 `applyRouteState()` 恢复原位置。新增页面状态时必须同步这些函数，否则浏览器后退/前进会失效。

## 12. 提交前检查清单

每次改 `index.html` 后必须同步：

```powershell
Copy-Item -LiteralPath index.html -Destination v1.7.html
```

语法检查：

```powershell
$content=Get-Content -LiteralPath index.html -Raw
$script=$content -replace '(?s)^.*?<script>','' -replace '(?s)</script>.*$',''
Set-Content -LiteralPath "$env:TEMP\jng-check.js" -Value $script -Encoding UTF8
node --check "$env:TEMP\jng-check.js"
```

本地验证重点：

- 首页能加载。
- 搜索能快速出首批结果，进度不会卡死。
- 搜索记录能展示、复搜、单条删除、清空。
- 分类页 `?view=category&cat=movie` 能加载。
- 详情页能展示多个来源并切换。
- 手机竖屏播放器自适应正常。
- 设置页自检、主题、友链入口正常。
- GitHub Pages 工作流完成。

部署后检查：

```powershell
& 'C:\Users\19255\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe' run list --repo jiesny/jienigui-video --limit 3
```

## 13. 常见改动入口

新增采集源：

```js
const DEFAULT_SOURCES = [...]
```

调整低优先级源：

```js
const LOW_PRIORITY_SOURCE_IDS = [...]
```

调整友链：

```js
const FRIEND_LINKS = [...]
```

调整主题：

```js
const THEMES = [...]
body[data-theme="..."] { ... }
```

调整搜索：

```js
handleGlobalSearch()
localScanSearch()
groupSearchResults()
```

调整播放线路：

```js
parsePlayUrls(...)
parseXmlData(...)
```

调整详情来源切换：

```js
openSearchResult(...)
openAggregatedDetail(...)
openDetailFromVideo(...)
selectDetailSource(...)
```
