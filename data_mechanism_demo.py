#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import random
import time
import pandas as pd
from pathlib import Path
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ==========================================
# 1. 代理机制 (Proxy Mechanism)
# ==========================================
class ProxyManager:
    """管理并随机选择代理"""
    def __init__(self, proxy_file='instock/config/proxy.txt'):
        self.proxies = []
        if os.path.exists(proxy_file):
            with open(proxy_file, "r") as f:
                self.proxies = [line.strip() for line in f if line.strip()]

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {"http": proxy, "https": proxy}

# ==========================================
# 2. Cookie 机制 (Cookie Mechanism)
# ==========================================
class CookieManager:
    """管理 Cookie 的获取"""
    @staticmethod
    def get_eastmoney_cookie(cookie_file='instock/config/eastmoney_cookie.txt'):
        # 优先级: 环境变量 > 配置文件 > 默认
        cookie = os.environ.get('EAST_MONEY_COOKIE')
        if cookie:
            return cookie

        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookie = f.read().strip()
            if cookie:
                return cookie

        # 默认备选 Cookie
        return 'st_si=78948464251292; st_psi=20240205091253851-119144370567-1089607836; st_pvi=07789985376191; st_sp=2024-02-05%2009%3A11%3A13; st_inirUrl=https%3A%2F%2Fxuangu.eastmoney.com%2FResult; st_sn=12; st_asi=20240205091253851-119144370567-1089607836-webznxg.dbssk.qxg-1'

# ==========================================
# 3. 数据抓取器 (Data Fetcher)
# ==========================================
class DataFetcher:
    """封装请求逻辑"""
    def __init__(self):
        self.proxy_mgr = ProxyManager()
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Cookie': CookieManager.get_eastmoney_cookie()
        }
        session.headers.update(headers)
        return session

    def fetch_stock_spot(self):
        """获取东方财富实时行情 (数据来源示例)"""
        url = "http://82.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "20", "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2", "fid": "f12",
            "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
            "fields": "f12,f14,f2,f3,f4,f5,f6",
        }

        proxies = self.proxy_mgr.get_proxy()
        print(f"正在使用代理: {proxies if proxies else '无'}")

        response = self.session.get(url, params=params, proxies=proxies, timeout=10)
        response.raise_for_status()

        data = response.json()["data"]["diff"]
        df = pd.DataFrame(data)
        # 显式重命名列，避免顺序问题
        df.rename(columns={
            "f12": "代码",
            "f14": "名称",
            "f2": "最新价",
            "f3": "涨跌幅",
            "f4": "涨跌额",
            "f5": "成交量",
            "f6": "成交额"
        }, inplace=True)
        return df[["代码", "名称", "最新价", "涨跌幅"]]

# ==========================================
# 测试运行
# ==========================================
if __name__ == "__main__":
    print("=== InStock 项目机制演示与测试 ===")
    try:
        fetcher = DataFetcher()
        result = fetcher.fetch_stock_spot()
        print("\n成功获取到前20条股票数据:")
        print(result)
        print("\n[测试结论]: 数据抓取、Cookie 注入和代理逻辑运行正常。")
    except Exception as e:
        print(f"\n[测试失败]: {e}")
