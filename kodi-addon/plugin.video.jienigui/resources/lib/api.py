# -*- coding: utf-8 -*-
"""杰尼龟影视 - API 模块
对接 6 个采集站，支持 JSON 和 XML 两种返回格式。
Kodi Python 环境，无需 CORS 代理，直接请求即可。
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# ======================== 采集源配置 ========================

SOURCES = [
    {"id": "source_dytt",  "name": "电影天堂资源", "url": "https://caiji.dyttzyapi.com/api.php/provide/vod/at/xml/", "format": "xml"},
    {"id": "source_yzzy",  "name": "优质资源库",   "url": "https://api.yzzy-api.com/inc/apijson.php",             "format": "json"},
    {"id": "source_ryzy",  "name": "如意资源",     "url": "https://cj.rycjapi.com/api.php/provide/vod/at/xml/",  "format": "xml"},
    {"id": "source_xigua", "name": "西瓜资源",     "url": "https://xgzy.tv/api.php/provide/vod/",                "format": "json"},
    {"id": "source_ffzy",  "name": "非凡资源",     "url": "https://api.ffzyapi.com/api.php/provide/vod/",        "format": "json"},
    {"id": "source_yaya",  "name": "鸭鸭资源",     "url": "https://cj.yayazy.net/api.php/provide/vod/",          "format": "json"},
]

# 标准分类
STANDARD_CATEGORIES = [
    {"key": "movie",  "name": "电影", "aliases": ["电影", "电影片", "动作片", "喜剧片", "爱情片", "科幻片", "恐怖片", "剧情片", "战争片", "惊悚片", "犯罪片", "悬疑片", "冒险片", "奇幻片", "4K电影", "蓝光电影", "网络电影", "Netflix电影", "邵氏电影", "院线", "大片"]},
    {"key": "series", "name": "剧集", "aliases": ["电视剧", "连续剧", "国产剧", "大陆剧", "内地剧", "欧美剧", "美剧", "韩剧", "韩国剧", "日剧", "日本剧", "港剧", "香港剧", "台剧", "台湾剧", "泰剧", "海外剧", "英剧", "新马剧", "其他剧", "Netflix自制剧"]},
    {"key": "anime",  "name": "动漫", "aliases": ["动漫", "动漫片", "国产动漫", "国漫", "日韩动漫", "日本动漫", "欧美动漫", "港台动漫", "海外动漫", "动画片", "有声动漫", "漫剧", "番剧", "新番"]},
    {"key": "show",   "name": "综艺", "aliases": ["综艺", "综艺片", "大陆综艺", "内地综艺", "日韩综艺", "韩国综艺", "港台综艺", "欧美综艺", "海外综艺", "演唱会", "真人秀", "晚会", "脱口秀"]},
    {"key": "short",  "name": "短剧", "aliases": ["短剧", "短视频", "爽文短剧", "女频恋爱", "反转爽剧", "古装仙侠", "年代穿越", "脑洞悬疑", "现代都市", "擦边短剧", "微短剧", "网剧短剧"]},
    {"key": "doc",    "name": "纪录", "aliases": ["纪录", "纪录片", "记录片", "纪实", "科普学习", "探索", "人文", "自然"]},
    {"key": "sports", "name": "体育", "aliases": ["体育", "体育赛事", "篮球", "足球", "网球", "斯诺克", "赛事", "NBA", "CBA", "英超", "西甲", "欧冠"]},
    {"key": "other",  "name": "其他", "aliases": ["伦理", "伦理片", "写真热舞", "两性课堂", "资讯", "娱乐新闻", "午夜", "福利", "解说", "影视解说", "电影解说", "预告片", "预告解说", "影评", "混剪"]},
]

# URL 域名替换
URL_REPLACEMENTS = [
    ("img.image8899.net", "img.ffzy888.com"),
    ("vip.ffzy-video.com", "vod.feifei-video.com"),
    ("vip.ffzy-online4.com", "vod.feifei-online.com"),
    ("svipsvip.ffzyread1.com", "vod.feifei-kan.com"),
    ("svipsvip.ffzy-online5.com", "vip.ffzy-plays.com"),
    ("vip.dytt-watch.com", "vip.dytt-broadcast.com"),
]

# ======================== 工具函数 ========================

def http_get(url, timeout=10):
    """发送 GET 请求，返回文本"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_url(url):
    """替换失效域名"""
    if not url:
        return url
    for old, new in URL_REPLACEMENTS:
        url = url.replace(old, new)
    return url


def strip_html(text):
    """去除 HTML 标签"""
    if not text:
        return ""
    import re
    return re.sub(r"<[^>]*>", " ", text).replace("&nbsp;", " ").strip()


def clean_category_name(name):
    """清洗分类名，用于匹配"""
    if not name:
        return ""
    import re
    name = re.sub(r"[（）()【】\[\]\s_-]", "", str(name))
    for word in ["专区", "频道", "资源", "大全", "列表", "推荐", "热门", "高清", "蓝光", "专区"]:
        name = name.replace(word, "")
    return name


def match_standard_category(source_category_name):
    """将采集源分类匹配到标准分类"""
    name = clean_category_name(source_category_name)
    if not name:
        return None
    for std in STANDARD_CATEGORIES:
        for alias in std["aliases"]:
            cleaned_alias = clean_category_name(alias)
            if cleaned_alias and (name == cleaned_alias or cleaned_alias in name or name in cleaned_alias):
                return std["key"]
    return None


def parse_play_urls(raw_url_str, source_id=""):
    """解析播放地址字符串: 组用$$$分隔, 集用#分隔, 名和URL用$分隔"""
    if not raw_url_str:
        return []
    groups = raw_url_str.split("$$$")
    if source_id in ("source_xigua", "source_ffzy"):
        groups = groups[1:]  # 跳过第一组(广告)
    result = []
    for gi, group in enumerate(groups):
        if not group.strip():
            continue
        episodes = []
        for ep in group.split("#"):
            if not ep.strip():
                continue
            parts = ep.split("$")
            if len(parts) >= 2:
                episodes.append({"name": parts[0].strip(), "url": normalize_url(parts[1].strip())})
            elif parts[0].strip():
                episodes.append({"name": "播放源-%d" % (gi + 1), "url": normalize_url(parts[0].strip())})
        if episodes:
            result.append({"source_name": "线路 %d" % (gi + 1), "episodes": episodes})
    return result


# ======================== API 响应解析 ========================

def parse_xml_response(text, source):
    """解析 XML 格式的 API 响应。先用 ElementTree，失败则回退到 regex。"""
    try:
        return _parse_xml_etree(text, source)
    except Exception:
        return _parse_xml_regex(text, source)


def _parse_xml_etree(text, source):
    root = ET.fromstring(text)
    list_node = root.find("list")

    videos = []
    for video_el in root.findall("video"):
        def txt(tag):
            el = video_el.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        play_urls = []
        for dl in video_el.findall("dl"):
            for dd in dl.findall("dd"):
                flag = (dd.get("flag") or "").lower()
                if "m3u8" in flag:
                    content = (dd.text or "").strip()
                    if content:
                        play_urls.append(content)

        videos.append({
            "vod_id": txt("id"),
            "vod_name": txt("name"),
            "type_id": txt("tid"),
            "type_name": txt("type"),
            "vod_pic": normalize_url(txt("pic")),
            "vod_sub": txt("subname"),
            "vod_lang": txt("lang"),
            "vod_area": txt("area"),
            "vod_year": txt("year"),
            "vod_remarks": txt("note"),
            "vod_actor": txt("actor"),
            "vod_director": txt("director"),
            "vod_content": txt("des"),
            "vod_time": txt("last"),
            "vod_play_url": "$$$".join(play_urls),
            "source_id": source["id"],
            "source_name": source["name"],
        })

    categories = []
    seen = set()
    for v in videos:
        if v["type_id"] and v["type_name"] and v["type_id"] not in seen:
            seen.add(v["type_id"])
            categories.append({"type_id": v["type_id"], "type_name": v["type_name"]})

    page = int(list_node.get("page", 1)) if list_node is not None else 1
    pagecount = int(list_node.get("pagecount", 1)) if list_node is not None else 1
    return {"categories": categories, "videos": videos, "page": page, "pagecount": pagecount}


def _parse_xml_regex(text, source):
    """regex 回退：匹配 <video>...</video> 块，手动提取字段"""
    import re

    videos = []
    # 匹配每个 <video> 块
    video_blocks = re.findall(r"<video[^>]*>(.*?)</video>", text, re.DOTALL)
    for block in video_blocks:
        def re_txt(tag):
            m = re.search(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), block, re.DOTALL)
            return m.group(1).strip() if m else ""

        play_urls = []
        # 匹配 <dl> 下的 <dd flag="...m3u8..."> 内容
        dl_blocks = re.findall(r"<dl[^>]*>(.*?)</dl>", block, re.DOTALL)
        for dl_block in dl_blocks:
            dd_blocks = re.findall(r"<dd[^>]*flag=[\"']([^\"']*m3u8[^\"']*)[\"'][^>]*>(.*?)</dd>", dl_block, re.DOTALL | re.IGNORECASE)
            for flag, content in dd_blocks:
                if content.strip():
                    play_urls.append(content.strip())

        videos.append({
            "vod_id": re_txt("id"),
            "vod_name": re_txt("name"),
            "type_id": re_txt("tid"),
            "type_name": re_txt("type"),
            "vod_pic": normalize_url(re_txt("pic")),
            "vod_sub": re_txt("subname"),
            "vod_lang": re_txt("lang"),
            "vod_area": re_txt("area"),
            "vod_year": re_txt("year"),
            "vod_remarks": re_txt("note"),
            "vod_actor": re_txt("actor"),
            "vod_director": re_txt("director"),
            "vod_content": re_txt("des"),
            "vod_time": re_txt("last"),
            "vod_play_url": "$$$".join(play_urls),
            "source_id": source["id"],
            "source_name": source["name"],
        })

    categories = []
    seen = set()
    for v in videos:
        if v["type_id"] and v["type_name"] and v["type_id"] not in seen:
            seen.add(v["type_id"])
            categories.append({"type_id": v["type_id"], "type_name": v["type_name"]})

    return {"categories": categories, "videos": videos, "page": 1, "pagecount": 1}


def parse_json_response(data, source):
    """解析 JSON 格式的 API 响应"""
    if not isinstance(data, dict) or not isinstance(data.get("list"), list):
        return {"categories": [], "videos": [], "page": 1, "pagecount": 1}

    videos = []
    for item in data["list"]:
        if not isinstance(item, dict):
            continue
        videos.append({
            "vod_id": str(item.get("vod_id", item.get("id", ""))),
            "vod_name": str(item.get("vod_name", "")),
            "type_id": str(item.get("type_id", "")),
            "type_name": str(item.get("type_name", "")),
            "vod_pic": normalize_url(str(item.get("vod_pic", ""))),
            "vod_sub": str(item.get("vod_sub", item.get("vod_remarks", ""))),
            "vod_lang": str(item.get("vod_lang", "")),
            "vod_area": str(item.get("vod_area", "")),
            "vod_year": str(item.get("vod_year", "")),
            "vod_remarks": str(item.get("vod_remarks", "")),
            "vod_actor": str(item.get("vod_actor", "")),
            "vod_director": str(item.get("vod_director", "")),
            "vod_content": strip_html(str(item.get("vod_content", item.get("vod_blurb", "")))),
            "vod_time": str(item.get("vod_time", "")),
            "vod_play_url": normalize_url(str(item.get("vod_play_url", ""))),
            "source_id": source["id"],
            "source_name": source["name"],
        })

    categories = []
    seen = set()
    for cat in (data.get("class") or []):
        if isinstance(cat, dict):
            tid = str(cat.get("type_id", ""))
            tname = str(cat.get("type_name", ""))
            if tid and tname and tid not in seen:
                seen.add(tid)
                categories.append({"type_id": tid, "type_name": tname})

    return {
        "categories": categories,
        "videos": videos,
        "page": int(data.get("page", 1)),
        "pagecount": int(data.get("pagecount", 1)),
    }


def parse_response(text, source):
    """自动识别 XML 或 JSON 并解析"""
    text = text.strip()
    if text.startswith("<"):
        return parse_xml_response(text, source)
    else:
        return parse_json_response(json.loads(text), source)


# ======================== 业务 API ========================

def build_url(source, params):
    """构建 API URL"""
    base = source["url"]
    connector = "&" if "?" in base else "?"
    qs = urllib.parse.urlencode(params)
    return base + connector + qs


def fetch_categories(source):
    """获取采集源的分类列表"""
    url = build_url(source, {"ac": "list"})
    text = http_get(url)
    return parse_response(text, source)["categories"]


def fetch_videos(source, page=1, category_id=None):
    """获取视频列表"""
    params = {"ac": "detail", "pg": str(page)}
    if category_id:
        params["t"] = category_id
    url = build_url(source, params)
    text = http_get(url)
    return parse_response(text, source)


def search_videos(source, keyword):
    """搜索视频"""
    url = build_url(source, {"ac": "detail", "wd": keyword})
    text = http_get(url)
    return parse_response(text, source)


def fetch_all_categories():
    """获取所有源的分类并按标准分类合并"""
    merged = {}
    for source in SOURCES:
        try:
            cats = fetch_categories(source)
        except Exception:
            cats = []
        for cat in cats:
            std_key = match_standard_category(cat["type_name"])
            if std_key:
                merged.setdefault(std_key, set()).add((cat["type_id"], cat["type_name"], source["id"]))
    return merged


def fetch_from_all_sources(page=1, std_category_key=None, source_category_map=None):
    """从所有源拉取视频并去重合并"""
    import hashlib

    all_videos = []
    for source in SOURCES:
        try:
            if std_category_key and source_category_map:
                # 从预匹配的分类中查找对应分类 ID
                cats_for_std = source_category_map.get(std_category_key, set())
                source_cats = [(tid, tname) for tid, tname, sid in cats_for_std if sid == source["id"]]
                if source_cats:
                    # 使用匹配到的第一个分类
                    result = fetch_videos(source, page, source_cats[0][0])
                else:
                    result = fetch_videos(source, page)
            else:
                result = fetch_videos(source, page)
            all_videos.extend(result["videos"])
        except Exception:
            pass

    # 去重 (按标准化标题 + 年份)
    seen = set()
    deduped = []
    for v in all_videos:
        name = v.get("vod_name", "")
        year = v.get("vod_year", "")
        key = "%s-%s" % (name, year)
        h = hashlib.md5(key.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            deduped.append(v)
    return deduped


def search_from_all_sources(keyword):
    """从所有源搜索"""
    all_videos = []
    for source in SOURCES:
        try:
            result = search_videos(source, keyword)
            all_videos.extend(result["videos"])
        except Exception:
            pass
    return all_videos
