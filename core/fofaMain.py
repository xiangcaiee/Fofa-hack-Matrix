#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/10/16 20:20
# @Author  : xiangcaiee
# @Github: https://github.com/xiangcaiee
import json
import os
import random
import sys
import urllib
import base64
import time
from tookit import unit, fofaUseragent, config
from tookit.client_main import get_result_from_api
from tookit.levelData import LevelData
from tookit.outputData import OutputData
import re, requests
from lxml import etree

from tookit.sign import getUrl
from tookit.unit import clipKeyWord, colorize
import gettext
import locale

if getattr(sys, 'frozen', None):
    dir = sys._MEIPASS
else:
    dir = config.ROOT_PATH

# 获取当前的语言设置
lang, _ = locale.getdefaultlocale()
if lang.startswith('zh'):
    _ = lambda x: x
else:
    language = gettext.translation('fofa_hack', localedir=os.path.join(dir, "locale"), languages=['en'])
    language.install()
    _ = language.gettext


class FofaMain:
    '''
    FUZZ规则
    '''
    LEFT_LIST_RULE = '//div[@class="hsxa-meta-data-list-main-left hsxa-fl"]'
    CITY_RULE = 'p[3]/a/@href'
    ASN_RULE = 'p[4]/a/text()'
    ORG_RULE = 'p[5]/a/text()'
    PORT_RULE = '//a[@class="hsxa-port"]/text()'

    def __init__(self, search_key, inputfile, filename, time_sleep, endcount, level, level_data, output, output_data,
                 fuzz, timeout, is_proxy, proxy=None):
        """
        初始化方法
        """
        self.search_key = search_key
        self.inputfile = inputfile
        self.filename = filename
        self.time_sleep = time_sleep
        self.endcount = endcount
        self.level = level
        self.level_data = level_data
        self.output = output
        self.output_data = output_data
        self.fuzz = fuzz
        self.timeout = timeout
        self.is_proxy = is_proxy
        self.proxy = proxy

        self.host_set = set()
        self.timestamp_list = [set()]
        self.city_list = [set()]
        self.asn_list = [set()]
        self.org_list = [set()]
        self.port_list = [set()]
        self.old_length = -1

        self.timestamp_index = 0
        self.no_new_data_count = 0
        self.MAX_MATCH_RETRY_NUM = 3
        self.EXIT_FLAG = False

    def outInitMsg(self):
        """
        输出初始化信息
        """
        print(colorize(_('''[*] LEVEL = {} , 初始化成功
[*] 爬取延时: {}s
[*] 爬取关键字: {}
[*] 爬取结束数量: {}
[*] 输出格式为: {}
[*] 存储文件名: {}
[*] 是否开启关键字fuzz: {}
[*] 是否开启代理: {}
[*] 读取文件: {}
''').format(self.level, self.time_sleep, self.search_key, self.endcount, self.output, self.filename,
            self.fuzz, self.is_proxy, self.inputfile), "green"))

    def format_single_proxy(self, proxy):
        proxies = {}
        if proxy:
            proxies = {
                'http': config.PROXY_TYPE + '://' + proxy,
                'https': config.PROXY_TYPE + '://' + proxy
            }
            return proxies
        else:
            return proxies

    def get_proxy(self):
        if self.proxy:
            return self.proxy

        if config.IS_PROXY:
            if config.PROXY_SINGLE:
                return self.format_single_proxy(config.PROXY_ARGS)
            elif config.PROXY_FROM_TXT:
                file_path = os.path.join(config.ROOT_PATH, config.PROXY_ARGS)
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                proxy = random.choice(lines).strip()
                return self.format_single_proxy(proxy)
            else:
                rep = requests.get(config.PROXY_ARGS, headers=fofaUseragent.getNormalHeaders(), timeout=10)
                if rep:
                    proxy = rep.text.strip()
                    return self.format_single_proxy(proxy)
                else:
                    return {}
        else:
            return {}

    def getFofaKeywordsCount(self, search_key):
        """
        获取关键字的搜索数量值（带429异常重试机制，防止直接崩掉）
        """
        searchbs64 = base64.b64encode(f'{search_key}'.encode()).decode()
        print(colorize(_("[*] 爬取页面为:https://fofa.info/result?qbase64={}").format(searchbs64), "green"))
        if config.AUTHORIZATION:
            return searchbs64, ""

        retry_count = 0
        while retry_count < 5:
            try:
                resp = requests.get(
                    url="https://fofa.info/result?qbase64=" + searchbs64,
                    headers=fofaUseragent.getFofaPageNumHeaders(),
                    timeout=self.timeout,
                    proxies=self.get_proxy()
                )
                if resp.status_code == 429:
                    print(colorize("[-] 触发 429 Too Many Requests，暂停 15 秒后重试...", "red"))
                    time.sleep(15)
                    retry_count += 1
                    continue

                html = resp.text
                tree = etree.HTML(html)
                countnum_list = tree.xpath('//span[@class="hsxa-highlight-color"]/text()')
                countnum = countnum_list[0] if countnum_list else '0'
                print(colorize(_("[*] 存在数量:{}").format(countnum), "green"))
                return searchbs64, countnum
            except Exception as e:
                print(colorize("[-] 获取页面计数异常: {}，重试中...".format(e), "red"))
                time.sleep(5)
                retry_count += 1

        print(colorize("[-] 连续多次请求失败或遭遇官方封禁，跳过该组合条件", "red"))
        return searchbs64, '0'

    def getTimeList(self, text):
        timelist = list()
        try:
            data = json.loads(text)
            assets = data.get("data", {}).get("assets", [])
            for asset in assets:
                if config.TIME_TYPE == "day":
                    mtime = asset["mtime"].split()[0]
                else:
                    mtime = asset["mtime"]
                timelist.append(mtime)
        except Exception:
            pass
        return timelist

    def setIndexTimestamp(self, searchbs64, timestamp_index):
        """
        请求 FOFA API 获取数据，增加 429 频率限制处理
        """
        retry_count = 0
        while retry_count < 5:
            try:
                request_url = getUrl(searchbs64)
                if config.DEBUG:
                    print("[+] 当前请求网址: " + request_url)

                rep = requests.get(
                    request_url,
                    headers=fofaUseragent.getFofaPageNumHeaders(),
                    timeout=self.timeout,
                    proxies=self.get_proxy()
                )

                if rep.status_code == 429:
                    print(colorize("[-] API 请求触发 429 频率限制，暂停 20 秒后重试...", "red"))
                    time.sleep(20)
                    retry_count += 1
                    continue

                rep.raise_for_status()

                if len(rep.text) <= 55 and '820006' in rep.text:
                    raise RuntimeError("API call limit reached for today")

                timelist = self.getTimeList(rep.text)
                for temptime in timelist:
                    self.timestamp_list[timestamp_index].add(temptime)
                return rep
            except Exception as e:
                print(colorize("[-] 请求报错: {}，重试中...".format(e), "red"))
                time.sleep(5)
                retry_count += 1
        return None

    def fofaSpiderOnePageData(self, search_key, searchbs64, timestamp_index):
        print(colorize(_("now search key: {}").format(search_key), "blue"))
        TEMP_RETRY_NUM = 0

        while TEMP_RETRY_NUM < self.MAX_MATCH_RETRY_NUM:
            try:
                rep = self.setIndexTimestamp(searchbs64, timestamp_index)
                if not rep:
                    raise RuntimeError("API 返回内容为空")

                self.saveDataToFile(rep)
                for data in self.level_data.format_data:
                    if self.level == "1":
                        self.host_set.add(data)
                    elif self.level == "2":
                        self.host_set.add(data["url"])
                    else:
                        self.host_set.add(data["id"])

                time.sleep(self.time_sleep)
                return rep.text

            except Exception as e:
                print(colorize("[-] error: {}".format(e), "red"))
                TEMP_RETRY_NUM += 1
                print(colorize(_('[-] 第{}次尝试获取页面URL').format(TEMP_RETRY_NUM), "red"))
                time.sleep(5)

        print(colorize(_('[-] FOFA资源获取重试超过最大次数，跳过当前分支'), "red"))
        return None

    def saveDataToFile(self, rep):
        self.level_data.startSpider(rep)
        print(
            colorize(_("[*] 已爬取条数 {} : {}").format(len(self.host_set), str(self.level_data.format_data)), "green"))
        self.output_data.output(self.level_data.format_data)

    def fofaSpider(self, search_key, searchbs64, index):
        """
        核心爬取逻辑：仅对当前组合关键字进行查询，彻底剔除 before 递归追加逻辑
        """
        self.old_length = len(self.host_set)
        self.timestamp_list[index].clear()

        # 直接抓取当前组合关键字
        self.fofaSpiderOnePageData(search_key, searchbs64, index)

    def cleanInitParameters(self):
        self.host_set = set()
        self.timestamp_list = [set()]
        self.city_list = [set()]
        self.asn_list = [set()]
        self.org_list = [set()]
        self.port_list = [set()]
        self.old_length = -1
        self.timestamp_index = 0
        self.no_new_data_count = 0
        self.EXIT_FLAG = False

    def start(self):
        self.outInitMsg()
        print(colorize(_('[*] 开始运行'), "green"))
        if self.inputfile:
            with open(self.inputfile, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    if not line.strip():
                        continue
                    self.cleanInitParameters()
                    self.search_key = clipKeyWord(line.strip())

                    searchbs64, countnum = self.getFofaKeywordsCount(self.search_key)
                    if str(countnum) == "0" and len(str(countnum)) == 1:
                        print(colorize(_('无搜索结果，执行下一条'), "red"))
                        continue
                    else:
                        if config.FOFA_KEY:
                            get_result_from_api(self.search_key)
                        else:
                            self.fofaSpider(self.search_key, searchbs64, 0)
                            print(colorize(_('[+] 抓取结束,{}关键字共抓取数据 {} 条\n').format(self.search_key,
                                                                                               str(len(self.host_set))),
                                           "green"))
        else:
            searchbs64, countnum = self.getFofaKeywordsCount(self.search_key)
            if str(countnum) == "0" and len(str(countnum)) == 1:
                print(colorize(_('无搜索结果'), "red"))
            else:
                if config.FOFA_KEY:
                    get_result_from_api(self.search_key)
                else:
                    self.fofaSpider(self.search_key, searchbs64, 0)
                    print(colorize(_('[*] 抓取结束，共抓取数据 {} 条').format(str(len(self.host_set))), "green"))

    def _destroy(self):
        pass
