#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FOFA 查询辅助模块（已移除 before 语法及时间限制）。
"""

import base64
import json
import time
import requests
from tookit import fofaUseragent
from tookit.sign import getUrl


def _decode_search_key(search_basekey):
    """将 Base64 编码的搜索条件解码为普通字符串。"""
    try:
        return base64.b64decode(search_basekey).decode("utf-8")
    except Exception as exc:
        raise ValueError("搜索条件 Base64 解码失败：{}".format(exc)) from exc


def _request_assets(search_key, timeout=180, proxy=None):
    """请求 FOFA 并返回 assets 列表。"""
    search_base64 = base64.b64encode(
        search_key.encode("utf-8")
    ).decode("utf-8")

    request_url = getUrl(search_base64)

    try:
        response = requests.get(
            request_url,
            headers=fofaUseragent.getFofaPageNumHeaders(),
            timeout=timeout,
            proxies=proxy
        )

        if response.status_code == 429:
            raise RuntimeError(
                "FOFA 返回 HTTP 429：请求过于频繁，请暂停请求并检查账户额度或接口频率限制。"
            )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError("FOFA 请求失败：{}".format(exc)) from exc

    try:
        result = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "FOFA 返回的不是有效 JSON：{}".format(response.text[:300])
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError("FOFA 返回数据格式异常：响应不是 JSON 对象。")

    error_code = str(result.get("code", ""))
    if error_code == "820006":
        raise RuntimeError(
            "FOFA API 今日访问额度已用完，请检查账户额度或稍后再试。"
        )

    if result.get("error"):
        message = (
            result.get("errmsg")
            or result.get("message")
            or str(result)
        )
        raise RuntimeError("FOFA API 返回错误：{}".format(message))

    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(
            "FOFA 返回数据结构异常：{}".format(str(result)[:300])
        )

    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise RuntimeError("FOFA 返回数据异常：assets 不是列表。")

    return assets


def _format_assets(assets):
    """提取资产地址，优先使用 link，没有 link 时使用 host。"""
    results = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue

        address = asset.get("link") or asset.get("host")
        if address:
            results.append(address)

    return results


def api(search_key, endcount=100, timesleep=3, timeout=180, proxy=None):
    """使用普通搜索条件查询 FOFA。"""
    if not isinstance(search_key, str) or not search_key.strip():
        raise ValueError("搜索条件不能为空。")

    try:
        endcount = int(endcount)
        timesleep = float(timesleep)
        timeout = float(timeout)
    except (TypeError, ValueError) as exc:
        raise ValueError("endcount、timesleep 和 timeout 必须是有效数字。") from exc

    if endcount <= 0:
        return

    host_set = set()

    while len(host_set) < endcount:
        if timesleep > 0:
            time.sleep(timesleep)

        assets = _request_assets(
            search_key=search_key,
            timeout=timeout,
            proxy=proxy
        )
        format_data = _format_assets(assets)

        if not format_data:
            break

        previous_count = len(host_set)
        for address in format_data:
            host_set.add(address)

        yield format_data

        if len(host_set) == previous_count:
            break


def base64_api(search_basekey, endcount=100, timesleep=3, timeout=180, proxy=None):
    """使用 Base64 编码的搜索条件查询 FOFA。"""
    search_key = _decode_search_key(search_basekey)
    yield from api(
        search_key=search_key,
        endcount=endcount,
        timesleep=timesleep,
        timeout=timeout,
        proxy=proxy
    )