# 杰尼龟影视交接与使用文档

## 1. 项目概览

这是一个纯前端影视聚合站，核心文件是 `index.html`。页面部署在 GitHub Pages，不依赖自建后端。

本地目录：

```text
D:\项目资料\杰尼龟影视
```

线上地址：

```text
https://jiesny.github.io/jienigui-video/
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
git add index.html v1.7.html README.md HANDOFF.md
git commit -m "Your change summary"
git push
```

查看 GitHub Pages 工作流：

```powershell
& 'C:\Users\19255\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe' run list --repo jiesny/jienigui-video --limit 3
```

部署成功后访问：

```text
https://jiesny.github.io/jienigui-video/
```

## 3. 主要文件

- `index.html`：主站点，包含 UI、采集源配置、聚合、搜索、详情播放逻辑。
- `v1.7.html`：当前主页面备份，通常需要和 `index.html` 同步。
- `.github/workflows/pages.yml`：GitHub Pages 自动部署工作流。
- `.nojekyll`：避免 GitHub Pages 走 Jekyll 处理。
- `README.md`：简短项目说明。
- `HANDOFF.md`：当前交接文档。

## 4. 当前采集源

采集源配置位于 `index.html`：

```js
const DEFAULT_SOURCES = [...]
```

当前源：

| 名称 | ID | 接口 | 格式 |
| --- | --- | --- | --- |
| 非凡资源 | `source_ffzy` | `https://api.ffzyapi.com/api.php/provide/vod/` | JSON |
| 电影天堂资源 | `source_dytt` | `https://caiji.dyttzyapi.com/api.php/provide/vod/at/xml/` | XML |
| 优质资源库 | `source_yzzy` | `https://api.yzzy-api.com/api.php/provide/vod/at/xml/` | XML |
| 如意资源 | `source_ryzy` | `https://cj.rycjapi.com/api.php/provide/vod/at/xml/` | XML |
| 鸭鸭资源 | `source_yaya` | `https://cj.yayazy.net/api.php/provide/vod/` | JSON |
| 西瓜资源 | `source_xigua` | `https://xgzy.tv/api.php/provide/vod/` | JSON |

新增源时优先确认：

```powershell
Invoke-WebRequest -Uri '接口地址?ac=list' -UseBasicParsing -TimeoutSec 20
Invoke-WebRequest -Uri '接口地址?ac=detail&pg=1' -UseBasicParsing -TimeoutSec 20
```

如果是 XML，源对象加 `format: 'xml'` 仅作为标识；实际解析由 `parseXmlData()` 判断文本是否以 `<` 开头。

## 5. 聚合逻辑

核心函数：

- `fetchWithFallback(targetUrl)`：通过公共 CORS 代理访问采集接口。
- `fetchList(source, options)`：拉取某个源的列表或搜索结果。
- `fetchCategories(source)`：拉取并缓存某个源的分类。
- `fetchAllCategories()`：拉取全部源分类。
- `fetchStandardCategoryList(source, standardCategory, page)`：把某个源的小分类映射到大类。
- `fetchAggregatedList(standardCategory, page)`：跨全部源拉取、合并、去重并展示。
- `groupSearchResults(items)`：搜索结果按影片名聚合来源。

目前首页、分类页是全源聚合，不再预选单个采集源。搜索页原本就是跨源搜索。

## 6. 分类与筛选

大类配置：

```js
const STANDARD_CATEGORIES = [...]
```

筛选项配置：

```js
const FILTER_GROUPS = {...}
const COMMON_FILTERS = {...}
```

分类页显示：

- 类型
- 地区
- 语言
- 年份
- 排序

分类匹配逻辑是根据各采集源返回的 `type_name` 和 `STANDARD_CATEGORIES.aliases` 做包含匹配。

后续如果出现分类为空，优先检查：

1. 源是否返回 `class` 或 XML 列表里是否有 `tid/type`。
2. `STANDARD_CATEGORIES.aliases` 是否覆盖了该源的分类名。
3. `FILTER_GROUPS` 是否过度过滤。
4. `fetchAggregatedList()` 是否因为代理失败跳过了某些源。

## 7. 播放线路处理

播放 URL 解析在：

```js
parsePlayUrls(rawUrlStr, sourceId)
```

特殊规则：

- 西瓜资源：跳过第一组线路，只保留后面的可用线路。
- 非凡资源：跳过第一组分享页线路，只保留 m3u8 线路。
- 鸭鸭资源：接口本身返回 `yym3u8`，不需要跳过。
- XML 源：`parseXmlData()` 只提取 `flag` 包含 `m3u8` 的 `dd`。

域名替换在：

```js
const URL_REPLACEMENTS = [...]
```

目前包含非凡、电影天堂等源的旧域名替换规则。

## 8. 已知问题与后续优先级

### 8.1 首页进入详情只显示单个来源

当前首页和分类页虽然是聚合列表，但每张卡片仍然只携带一个来源的 `video` 对象。搜索页通过 `groupSearchResults()` 能把同名影片的多个来源聚合到详情页。

后续建议：

1. 在 `fetchAggregatedList()` 内不要只做简单 `dedupeVideos()`。
2. 参考 `groupSearchResults()`，把同名影片聚合成 `{ ...video, sources: [...] }`。
3. 首页和分类页点击时，如果 `video.sources` 存在，走类似 `openSearchResult(video)` 的逻辑。
4. 这样从首页/分类进入详情，也能显示全部可用来源。

注意：同名聚合建议用 `vod_name + vod_year`，不要只用 `vod_id`，因为不同源的 ID 不通用。

### 8.2 分类为空或不准

目前大类映射主要靠关键词包含。建议后续进一步建立按源的分类映射表，例如：

```js
const SOURCE_CATEGORY_MAP = {
  source_ffzy: {
    movie: ['电影片', '动作片', '喜剧片'],
    series: ['连续剧', '国产剧']
  }
}
```

这样比全局 `aliases` 更准确，也能减少空分类。

### 8.3 优质资源库海报缺失

优质资源库的部分列表接口没有返回 `pic`，因此页面会显示默认封面。可考虑在详情接口或搜索接口补拉完整信息，但会增加请求量。

### 8.4 公共代理不稳定

GitHub Pages 不能运行后端代理，只能靠公共 CORS 代理。页面内置：

- `AllOrigins`
- `Corsproxy.io`
- `Codetabs`

有些源会被某些代理 WAF 拦截。用户侧建议使用新加坡节点进行科学上网，页面已有提示。

## 9. 浏览器历史适配

页面使用 `history.pushState/replaceState` 支持：

- 首页
- 分类
- 搜索
- 设置面板
- 详情弹窗

相关函数：

- `routeState()`
- `routeUrl()`
- `pushRoute()`
- `replaceRoute()`
- `applyRouteState()`
- `stateFromUrl()`

后续新增视图时，需要同步这些函数，否则浏览器后退/前进会失效。

## 10. 开发注意事项

1. 编辑 `index.html` 后同步 `v1.7.html`：

```powershell
Copy-Item -LiteralPath index.html -Destination v1.7.html
```

2. 提交前做语法检查：

```powershell
$content=Get-Content -LiteralPath index.html -Raw
$script=$content -replace '(?s)^.*?<script>','' -replace '(?s)</script>.*$',''
Set-Content -LiteralPath "$env:TEMP\jng-check.js" -Value $script -Encoding UTF8
node --check "$env:TEMP\jng-check.js"
```

3. 本地浏览器验证重点：

- 首页能加载。
- 分类页 `?view=category&cat=movie` 能加载。
- 搜索能跨源返回。
- 详情弹窗能播放并切换来源。
- 浏览器后退能关闭详情或返回上一页。

4. 不要用会破坏中文编码的写入方式。优先使用 `apply_patch` 修改文件。

5. 如果 PowerShell 写文件，必须确认 UTF-8 和换行没有破坏 HTML。

## 11. 常见改动入口

新增采集源：

```js
const DEFAULT_SOURCES = [...]
```

新增旧域名替换：

```js
const URL_REPLACEMENTS = [...]
```

调整大类：

```js
const STANDARD_CATEGORIES = [...]
```

调整筛选按钮：

```js
const FILTER_GROUPS = {...}
const COMMON_FILTERS = {...}
```

调整播放线路：

```js
parsePlayUrls(...)
parseXmlData(...)
```

调整详情来源切换：

```js
openSearchResult(...)
openDetailFromVideo(...)
selectDetailSource(...)
```

## 12. 最近一次用户明确提出但尚未实现的需求

用户最新功能诉求：

1. 从主页或分类页进入影视详情页时，也要像搜索结果一样展示所有可用聚合来源。
2. 浏览分类时很多分类为空，希望总结各网站分类并重新分类。

推荐下一步实现顺序：

1. 改 `fetchAggregatedList()` 输出结构，让首页/分类列表保留 `sources`。
2. 改 `VideoCard` 点击逻辑，如果有 `sources` 就进入多源详情。
3. 增加 `SOURCE_CATEGORY_MAP` 做按源分类映射。
4. 验证 `movie/series/anime/show/short` 五个主分类。
