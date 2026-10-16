#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/10/16 20:20
# @Author  : xiangcaiee
# @Github: https://github.com/xiangcaiee
import argparse
import os
import sys
import time
from core.fofaMain import FofaMain
from tookit import unit, config
from tookit.levelData import LevelData
from tookit.outputData import OutputData
from tookit.unit import clipKeyWord, outputLogo

# 第一层 固定主体搜索条件，第一搜索条件
DEFAULT_SEARCH_KEY = 'body="xxx"'

# 第二层 资产类型是否为独立域名区分
DOMAIN_TYPES = ["false", "true"]

# 第三层 可根据需要自行增减国家/地区代码
COUNTRIES = [
    "US", "UK", "JP", "HK", "SG", "KR",
    "TW", "DE", "GB", "CA", "FR",
]

# 第四层：云服务商 / CDN 列表（可根据需要自行增减），同步注释43行、49行
# CLOUD_NAMES = [
#    "Aliyundun",
#    "Cloudflare",
# ]

def build_search_keys(base_key=DEFAULT_SEARCH_KEY):
    """
    生成按资产类型 (is_domain) 和国家/地区 (country) 和其他划分的组合查询条件列表。
    顺序：先遍历所有国家的 is_domain="false"，再遍历所有国家的 is_domain="true"
    """
    search_keys = []

    for domain_type in DOMAIN_TYPES:
        for country in COUNTRIES:
            #for cloud_name in CLOUD_NAMES:
            # 拼接一层查询条件
            search_key = (
                f'{base_key} && '
                f'is_domain="{domain_type}" && '
                f'country="{country}"'
                #f'cloud_name="{cloud_name}"'
            )
            search_keys.append(search_key)

    return search_keys


import gettext
import locale
import mmh3
import requests
import base64
import codecs

config.ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', None):
    dir = sys._MEIPASS
else:
    dir = config.ROOT_PATH

# 获取当前的语言设置
lang, _ = locale.getdefaultlocale()
if lang and lang.startswith('zh'):
    _ = lambda x: x
else:
    language = gettext.translation('fofa_hack', localedir=os.path.join(dir, "locale"), languages=['en'])
    language.install()
    _ = language.gettext


def main():
    outputLogo()
    parser = argparse.ArgumentParser(description=_("Fofa-hack v{} 使用说明").format(config.VERSION_NUM))

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--keyword', '-k', help=_('fofa搜索关键字'))
    group.add_argument('--inputfile', '-i', help=_("指定文件,从文件中批量读取fofa语法"))
    group.add_argument('--base', '-b', help=_("以base64的形式输入关键字 -b InRoaW5rcGhwIg=="))
    group.add_argument('--iconurl', type=str, help="指定url的icon作为icon_hash关键字")
    group.add_argument('--iconfile', type=str, help="指定icon_file作为icon_hash关键字")

    parser.add_argument('--timesleep', '-t', help=_('爬取每一页等待秒数,防止IP被Ban,默认为3'), default=3)
    parser.add_argument('--timeout', '-to', help=_('爬取每一页的超时时间,默认为180秒'), default=180)
    parser.add_argument('--endcount', '-e', help=_('爬取结束数量'))
    parser.add_argument('--level', '-l', help=_('爬取等级: 1-3 ,数字越大内容越详细,默认为 1'))
    parser.add_argument('--output', '-o', help=_('输出格式:txt、json、csv,默认为txt'))
    parser.add_argument('--outputname', '-on', help=_("指定输出文件名，默认文件名为 fofaHack"))
    parser.add_argument('--fuzz', '-f', help=_('关键字fuzz参数,增加内容获取粒度'), action='store_true')

    parser.add_argument('--proxy-type', choices=['socks4', 'socks5', 'http'], help=_("代理类型,默认为http"),
                        default='http')
    parser.add_argument('--authorization', type=str, help="指定Authorization值")
    parser.add_argument('--authorization-file', type=str,
                        help="从文件中读取authorization列表 --authorization-file authorization.txt")

    parser.add_argument('--fofa-key', type=str, help="fofa api key值(配合fofa终身会员使用)")
    parser.add_argument('--debug', help="fofa-hack调试模式,运行过程中输出更多运行日志", action='store_true')
    parser.add_argument('--time-type', help="fofa-hack时间类型 (day | hour)", choices=['day', 'hour'], default='day')

    proxy_group = parser.add_mutually_exclusive_group()
    proxy_group.add_argument('--proxy', help=_("指定代理,代理格式 --proxy '127.0.0.1:7890'"))
    proxy_group.add_argument('--proxy-url', help=_("指定代理url"))
    proxy_group.add_argument('--proxy-file', help=_("指定txt格式的代理文件"))

    args = parser.parse_args()

    if args.debug:
        config.DEBUG = args.debug

    if args.time_type:
        config.TIME_TYPE = args.time_type

    if args.fofa_key:
        config.FOFA_KEY = args.fofa_key

    if args.authorization_file:
        config.AUTHORIZATION_FILE = args.authorization_file
        with open(config.AUTHORIZATION_FILE, 'r') as f:
            for line in f.readlines():
                config.AUTHORIZATION_LIST.append(line.strip())

    time_sleep = int(args.timesleep)
    timeout = int(args.timeout)

    # 确定基础关键字
    base_keyword = DEFAULT_SEARCH_KEY
    if args.keyword:
        base_keyword = clipKeyWord(args.keyword)
    elif args.base:
        try:
            base_keyword = base64.b64decode(args.base).decode('utf-8')
        except Exception as e:
            print(e)
            base_keyword = ""
    elif args.iconurl:
        if args.iconurl.endswith(".ico"):
            icon_url = args.iconurl
        else:
            icon_url = args.iconurl + "favicon32.ico" if args.iconurl.endswith("/") else args.iconurl + "/favicon32.ico"
        try:
            _icon = mmh3.hash(codecs.lookup('base64').encode(requests.get(icon_url).content)[0])
            base_keyword = '''icon_hash="{}"'''.format(_icon)
        except:
            print("icon url " + icon_url + " 访问错误")
            exit(0)
    elif args.iconfile:
        file_path = args.iconfile
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                _icon = mmh3.hash(codecs.lookup('base64').encode(f.read())[0])
                base_keyword = '''icon_hash="{}"'''.format(_icon)

    endcount = int(args.endcount) if args.endcount else 100
    level = args.level if args.level else "1"
    level_data = LevelData(level)
    fuzz = args.fuzz

    output = args.output if args.output else "txt"
    outputname = args.outputname if args.outputname else "fofaHack"

    filename = "{}.{}".format(outputname, output)
    if os.path.exists(filename):
        os.remove(filename)
    if os.path.exists("final_" + filename):
        os.remove("final_" + filename)

    output_data = OutputData(filename, level, pattern=output)

    if args.proxy or args.proxy_url or args.proxy_file:
        config.IS_PROXY = True
        if args.proxy:
            config.PROXY_SINGLE = True
            config.PROXY_ARGS = args.proxy
        elif args.proxy_url:
            config.PROXY_FROM_URL = True
            config.PROXY_ARGS = args.proxy_url
        else:
            config.PROXY_FROM_TXT = True
            config.PROXY_ARGS = args.proxy_file
    if args.proxy_type:
        config.PROXY_TYPE = args.proxy_type

    inputfile = args.inputfile if args.inputfile else None
    if args.authorization:
        config.AUTHORIZATION = args.authorization

    # 如果没有指定 inputfile，则自动利用组合条件遍历各国家与 is_domain 状态
    if not inputfile:
        search_keys_list = build_search_keys(base_keyword)
        print(_("[-] 已生成多维组合查询条件，共计 {} 个组合任务。").format(len(search_keys_list)))

        for idx, sub_search_key in enumerate(search_keys_list, 1):
            print(_("\n[+] 正在执行第 {}/{} 个组合查询: {}").format(idx, len(search_keys_list), sub_search_key))
            try:
                fofa = FofaMain(
                    sub_search_key, None, filename, time_sleep, endcount,
                    level, level_data, output, output_data, fuzz, timeout, config.IS_PROXY
                )
                fofa.start()
            except Exception as e:
                print(_("[-] 执行该组合查询时发生异常: {}").format(e))
                continue
    else:
        # 如果指定了 inputfile，按原本文件读取逻辑执行
        fofa = FofaMain(
            "", inputfile, filename, time_sleep, endcount,
            level, level_data, output, output_data, fuzz, timeout, config.IS_PROXY
        )
        fofa.start()


if __name__ == '__main__':
    main()