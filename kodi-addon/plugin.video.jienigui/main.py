# -*- coding: utf-8 -*-
"""杰尼龟影视 Kodi 插件
遥控器操控：方向键选择，OK 键确认，返回键退出。
菜单层：首页分类 → 筛选类型 → 列表页 → 选源播放。
"""

import sys
import urllib.parse

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc

# 将 lib 目录加入 Python 路径
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))
from api import (
    SOURCES,
    STANDARD_CATEGORIES,
    fetch_videos,
    search_videos,
    fetch_all_categories,
    parse_play_urls,
    normalize_url,
)

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo("name")
ADDON_HANDLE = int(sys.argv[1])
BASEURL = sys.argv[0]

# ======================== Kodi 列表构建 ========================

def add_directory_item(label, url, thumb=None, icon=None, fanart=None):
    """添加一个目录项（点击进入下一层菜单）"""
    li = xbmcgui.ListItem(label, offscreen=True)
    art = {}
    if thumb: art["thumb"] = thumb
    if icon: art["icon"] = icon
    if fanart: art["fanart"] = fanart
    if art:
        li.setArt(art)
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)


def add_video_item(video, is_folder=False):
    """添加一个视频项"""
    name = video.get("vod_name", "未知")
    remarks = video.get("vod_remarks", "")
    title = "%s  [%s]" % (name, remarks) if remarks else name

    # 构建播放 URL（指向本插件自身，带播放参数）
    play_url = "%s?action=play&name=%s&url=%s&source_id=%s" % (
        BASEURL,
        urllib.parse.quote(name),
        urllib.parse.quote(video.get("vod_play_url", "")),
        video.get("source_id", ""),
    )

    # 构建详情 URL（进入选集菜单）
    detail_url = "%s?action=episodes&name=%s&url=%s&source_id=%s" % (
        BASEURL,
        urllib.parse.quote(name),
        urllib.parse.quote(video.get("vod_play_url", "")),
        video.get("source_id", ""),
    )

    li = xbmcgui.ListItem(title, offscreen=True)

    # 封面图
    poster = normalize_url(video.get("vod_pic", ""))
    if poster:
        li.setArt({"thumb": poster, "poster": poster, "icon": poster})

    # InfoLabel
    info = {
        "title": name,
        "originaltitle": name,
        "plot": video.get("vod_content", "")[:500],
        "tagline": video.get("vod_sub", ""),
        "year": int(video["vod_year"]) if video.get("vod_year", "").isdigit() else 0,
        "cast": (video.get("vod_actor", "") or "").split(","),
        "director": (video.get("vod_director", "") or "").split(","),
        "country": video.get("vod_area", ""),
    }
    li.setInfo("video", info)

    xbmcplugin.addDirectoryItem(
        handle=ADDON_HANDLE,
        url=detail_url if is_folder else play_url,
        listitem=li,
        isFolder=is_folder,
    )


def add_simple_video_item(name, url, thumb=""):
    """添加可直接播放的视频项"""
    li = xbmcgui.ListItem(name, offscreen=True)
    if thumb:
        li.setArt({"thumb": thumb, "icon": thumb})
    li.setInfo("video", {"title": name})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=False)


def end_directory():
    """结束目录列表，设置基本属性"""
    xbmcplugin.setContent(ADDON_HANDLE, "movies")
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ======================== 页面逻辑 ========================

def show_main_menu():
    """首页：标准分类 + 搜索"""
    for std in STANDARD_CATEGORIES:
        url = "%s?action=filter&category=%s" % (BASEURL, std["key"])
        add_directory_item(std["name"], url)

    # 搜索入口
    search_url = "%s?action=search" % BASEURL
    add_directory_item("[搜索]", search_url)

    end_directory()


def show_filter_list(std_category_key):
    """筛选列表页：每个采集源的匹配分类 + 直接列表"""
    # 为每个源拉取该标准分类下的视频列表
    # 简化处理：直接跳转到聚合列表
    url = "%s?action=list&category=%s&page=1" % (BASEURL, std_category_key)
    add_directory_item("全部", url)

    end_directory()


def show_video_list(std_category_key, page=1):
    """视频列表页：从所有源聚合获取，分页显示"""
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")

    try:
        videos = _fetch_videos_for_category(std_category_key, page)
    except Exception as e:
        xbmc.log("fetch error: %s" % str(e), xbmc.LOGERROR)
        videos = []

    xbmc.executebuiltin("Dialog.Close(busydialognocancel)")

    if not videos:
        xbmcgui.Dialog().notification(ADDON_NAME, "暂无数据", xbmcgui.NOTIFICATION_INFO)
        end_directory()
        return

    for v in videos:
        add_video_item(v, is_folder=True)

    # 下一页
    next_url = "%s?action=list&category=%s&page=%d" % (BASEURL, std_category_key, page + 1)
    add_directory_item("下一页 >>", next_url)

    end_directory()


def _fetch_videos_for_category(std_category_key, page):
    """从所有源聚合获取视频，按标准分类筛选"""
    import hashlib

    all_videos = []
    for source in SOURCES:
        try:
            result = fetch_videos(source, page)
            for v in result["videos"]:
                # 筛选匹配标准分类的影片
                type_name = v.get("type_name", "")
                cat_name = v.get("vod_class", "")
                combined = type_name + " " + cat_name
                if _video_matches_category(combined, std_category_key):
                    all_videos.append(v)
        except Exception:
            pass

    # 去重
    seen = set()
    deduped = []
    for v in all_videos:
        key = "%s-%s" % (v.get("vod_name", ""), v.get("vod_year", ""))
        h = hashlib.md5(key.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            deduped.append(v)
    return deduped


def _video_matches_category(type_name, std_category_key):
    """检查视频分类名是否匹配标准分类"""
    std = next((s for s in STANDARD_CATEGORIES if s["key"] == std_category_key), None)
    if not std:
        return True
    for alias in std["aliases"]:
        if alias and alias in type_name:
            return True
    return False


def show_episodes(video_name, raw_url_str, source_id):
    """选集页：展开播放线路和分集"""
    groups = parse_play_urls(raw_url_str, source_id)
    if not groups:
        xbmcgui.Dialog().notification(ADDON_NAME, "暂无可播放线路", xbmcgui.NOTIFICATION_WARNING)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    for group in groups:
        for ep in group["episodes"]:
            label = "%s - %s  [%s]" % (video_name, ep["name"], group["source_name"])
            play_url = "%s?action=play&name=%s&url=%s" % (
                BASEURL,
                urllib.parse.quote(label),
                urllib.parse.quote(ep["url"]),
            )
            add_simple_video_item(label, play_url)

    end_directory()


def show_search():
    """搜索页"""
    keyword = _get_keyboard_input("输入关键词")
    if not keyword:
        end_directory()
        return

    xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
    all_videos = []
    for source in SOURCES:
        try:
            result = search_videos(source, keyword)
            all_videos.extend(result["videos"])
        except Exception:
            pass
    xbmc.executebuiltin("Dialog.Close(busydialognocancel)")

    if not all_videos:
        xbmcgui.Dialog().notification(ADDON_NAME, "未找到 '%s'" % keyword, xbmcgui.NOTIFICATION_INFO)
        end_directory()
        return

    for v in all_videos:
        add_video_item(v, is_folder=True)

    end_directory()


def play_video(name, url):
    """播放视频"""
    if not url:
        xbmcgui.Dialog().notification(ADDON_NAME, "播放地址为空", xbmcgui.NOTIFICATION_ERROR)
        return

    li = xbmcgui.ListItem(name, path=url)
    li.setInfo("video", {"title": name})
    li.setProperty("IsPlayable", "true")

    xbmc.Player().play(url, li)


# ======================== 键盘输入 ========================

def _get_keyboard_input(heading):
    """弹出键盘输入框"""
    kb = xbmc.Keyboard("", heading)
    kb.doModal()
    if kb.isConfirmed():
        text = kb.getText().strip()
        return text if text else None
    return None


# ======================== 路由 ========================

def router():
    params = dict(urllib.parse.parse_qsl(sys.argv[2].replace("?", "")))
    action = params.get("action", "menu")

    if action == "menu":
        show_main_menu()
    elif action == "filter":
        show_filter_list(params.get("category", ""))
    elif action == "list":
        show_video_list(params.get("category", ""), int(params.get("page", 1)))
    elif action == "episodes":
        name = urllib.parse.unquote(params.get("name", ""))
        url = urllib.parse.unquote(params.get("url", ""))
        source_id = params.get("source_id", "")
        show_episodes(name, url, source_id)
    elif action == "search":
        show_search()
    elif action == "play":
        name = urllib.parse.unquote(params.get("name", ""))
        url = urllib.parse.unquote(params.get("url", ""))
        play_video(name, url)
    else:
        show_main_menu()


if __name__ == "__main__":
    router()
