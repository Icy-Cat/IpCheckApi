"""
IP查询服务模块

提供IP地址查询功能，支持DrissionPage和httpx两种方式
优化支持多进程并发查询
集成SQLite缓存功能，支持1天有效期缓存和并发控制
"""

from DrissionPage import SessionPage, SessionOptions
import httpx
import re
from fake_useragent import UserAgent
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
import time
from cache import cache_manager


class IPQueryService:
    """IP查询服务类 - 支持多进程并发"""

    def __init__(self, max_workers=None):
        """
        初始化查询服务

        Args:
            max_workers: 最大工作线程/进程数，默认为CPU核心数
        """
        self.base_url = "https://cloud.baidu.com/api/afd-ip-threat/act/v1/ipage"
        self.overall_baseurl = f"{self.base_url}/overall"
        self.ip_base_baseurl = f"{self.base_url}/base"

        # 设置并发工作数
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)

        # 创建线程池用于单进程内并发
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def query_ip_with_httpx(self, ip_address, proxy_url=None, method="GET"):
        """
        使用httpx查询IP地址信息（支持代理和fake User-Agent）

        Args:
            ip_address: 要查询的IP地址
            proxy_url: 代理服务器地址 (例如: "http://proxy.example.com:8080")
            method: HTTP请求方法，默认为"GET"

        Returns:
            dict: 包含查询结果的字典
        """
        try:
            # 构建查询URL
            url = f"{self.overall_baseurl}/{ip_address}"

            # 配置代理
            if proxy_url and not proxy_url.startswith("http"):
                proxy_url = "http://" + proxy_url

            # 生成fake User-Agent
            ua = UserAgent()
            user_agent = ua.random

            # 设置请求头
            headers = {
                "User-Agent": user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Connection": "keep-alive",
                "host": "cloud.baidu.com",
                "referer": f"https://cloud.baidu.com/product-s/afd_s/ip-threat.html?s={ip_address}",
            }

            # 发送HTTP请求
            with httpx.Client(proxy=proxy_url, headers=headers, timeout=20.0) as client:
                response = client.get(url)

                # 检查响应状态
                response.raise_for_status()

                over_all_data = response.json()["ret_data"]["data"]

                # ip_base_response = client.get(f"{self.ip_base_baseurl}/{ip_address}")
                # ip_base_response.raise_for_status()
                # over_base_data = ip_base_response.json()["ret_data"]["data"]

                # 解析响应内容
                result = {
                    "ip": ip_address,
                    "status": "success",
                    "data": {
                        "overall": over_all_data,
                        # "ip_base": over_base_data,
                    },
                }

                return result

        except httpx.ProxyError as e:
            return {"ip": ip_address, "status": "error", "error": f"代理错误: {str(e)}", "method": "httpx"}
        except httpx.TimeoutException as e:
            return {"ip": ip_address, "status": "error", "error": f"请求超时: {str(e)}", "method": "httpx"}
        except httpx.HTTPStatusError as e:
            return {"ip": ip_address, "status": "error", "error": f"HTTP错误: {str(e)}", "method": "httpx"}
        except Exception as e:
            return {"ip": ip_address, "status": "error", "error": str(e), "method": "httpx"}

    def query_ip_with_cache(self, ip_address, proxy_url=None, method="GET"):
        """
        使用httpx查询IP地址信息（带缓存功能）

        集成SQLite缓存：
        - 缓存有效期1天
        - 并发请求同一IP时，只查询一次
        - 其他请求等待查询结果

        Args:
            ip_address: 要查询的IP地址
            proxy_url: 代理服务器地址
            method: HTTP请求方法

        Returns:
            dict: 包含查询结果的字典（来自缓存或新查询）
        """
        # 使用缓存管理器的get_or_query方法
        return cache_manager.get_or_query(
            ip_address, self.query_ip_with_httpx, proxy_url=proxy_url, method=method
        )

    def batch_query(self, ip_list, proxy_url=None, max_workers=None):
        """
        批量并发查询IP地址

        Args:
            ip_list: IP地址列表
            proxy_url: 代理服务器地址
            max_workers: 最大并发数

        Returns:
            list: 查询结果列表
        """
        workers = max_workers or self.max_workers
        results = []

        # 使用线程池进行并发查询
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交所有任务
            future_to_ip = {executor.submit(self.query_ip_with_cache, ip, proxy_url): ip for ip in ip_list}

            # 收集结果
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"ip": ip, "status": "error", "error": str(e)})

        return results

    def query_ip_with_httpx_sync(self, ip_address, proxy_url=None, method="GET"):
        """
        同步版本的IP查询（用于多进程）
        """
        return self.query_ip_with_httpx(ip_address, proxy_url, method)

    def close(self):
        """关闭线程池"""
        if hasattr(self, "thread_pool"):
            self.thread_pool.shutdown(wait=True)


# 创建全局查询服务实例
query_service = IPQueryService()


def _query_ip_multiprocess(args):
    """多进程查询函数 - 用于跨进程调用"""
    ip, proxy_url, method = args
    service = IPQueryService()
    try:
        result = service.query_ip_with_httpx_sync(ip, proxy_url, method)
        return result
    finally:
        service.close()


def batch_query_multiprocess(ip_list, proxy_url=None, max_workers=None):
    """
    跨进程批量查询IP地址

    Args:
        ip_list: IP地址列表
        proxy_url: 代理服务器地址
        max_workers: 最大并发进程数

    Returns:
        list: 查询结果列表
    """
    workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)

    # 准备参数
    args_list = [(ip, proxy_url, "GET") for ip in ip_list]

    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        future_to_ip = {executor.submit(_query_ip_multiprocess, args): args[0] for args in args_list}

        # 收集结果
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"ip": ip, "status": "error", "error": str(e)})

    return results


if __name__ == "__main__":
    # 测试查询功能
    ip = "36.184.64.231"
    httpx_res = query_service.query_ip_with_httpx(
        ip, proxy_url="15951531090:1Dkvavbt@tunnel-42.91http.cc:10630"
    )
    print("HTTPX查询结果:", httpx_res)

    # 测试批量查询
    # test_ips = ["36.184.64.231", "8.8.8.8"]
    # print("\n批量查询结果:")
    # batch_results = query_service.batch_query(
    #     test_ips, proxy_url="15951531090:1Dkvavbt@tunnel-42.91http.cc:10630"
    # )
    # for result in batch_results:
    #     print(f"IP: {result['ip']}, Status: {result['status']}")
