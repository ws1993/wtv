# 在tvs表当中插入文件
import asyncio
from time import time
import aiohttp
import pymysql
from yarl import URL
import requests
import certifi
import ssl

# http://yubeilive.cbg.cn/ch1-3.m3u8
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'


def get_data_urls(cursor):
    cursor.execute(f"select id, url from tvs")
    urls = cursor.fetchall()
    return urls


class Data:
    def __init__(self, tv_json) -> None:

        db = pymysql.connect(host='62.234.69.225',
                                  user='tvs',
                                  password='33pNBPb2xFnLc8hz',
                                  database='tvs')

        cursor = db.cursor()

        self.db = db
        self.cursor = cursor
        self.urls_list = get_data_urls(cursor)
        self.no_checked_list = []

        self.tv_json = tv_json
        self.semaphore = asyncio.Semaphore(10)  # 限制并发量为500

    def insert(self):
        for tv in self.tv_json:
            name, url = tv.split(",")

            if self.filter_url(url):
                print(f"跳过{name}{url}")
                continue

            try:
                insert_url_sql = f"insert into tvs (name,url) values ('{name}','{url}')"
                print("插入数据:", insert_url_sql)
                self.cursor.execute(insert_url_sql)
            except Exception as e:
                print("Exception:", e)
                continue

    def filter_url(self, url):
        headers = {'User-Agent': USER_AGENT}
        '''
            过滤无效的url,返回True 则表示需要过滤
        '''
        if not (url.startswith("http") or url.startswith("https")):
            return True

        # url存在则过滤掉
        if url in map(lambda item: item[1], self.urls_list):
            return True

        # URL 无法请求则过滤掉
        try:
            response = requests.head(url, timeout=1, headers=headers)
            if response.ok:
                return False
        except Exception as e:
            print(str(e))
            return True

    async def check_url(self):
        timeout = aiohttp.ClientTimeout(10)
        headers = {'User-Agent': USER_AGENT}
        # 获取ssl证书的位置
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(certifi.where())
        # 自定义ssl的连接器
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        client = aiohttp.ClientSession(
            timeout=timeout, connector=connector)

        def del_tv(_id):
            delSql = f"delete from tvs where id={_id}"
            self.cursor.execute(delSql)
            self.db.commit()

        async def is_ok(_id, url):
            async with self.semaphore:
                try:
                    async with client.head(URL(url, encoded=True), headers=headers) as response:
                        if not response.ok:
                            print(
                                f"====删除状态异常链接=={_id}=={response.status}==>", url)
                            del_tv(_id)
                        else:
                            print("ok", url)

                except Exception as e:
                    if str(e).strip():
                        print(f"====Exception=={_id}=={str(e)}==>", url)
                        del_tv(_id)
                    else:
                        self.no_checked_list.append(_id)

        # for _id, url in self.urls_list:
        #     asyncio.run(await is_ok(_id, url))
        await asyncio.gather(*[asyncio.ensure_future(is_ok(_id, url)) for _id, url in self.urls_list])
        connector.close()
        await client.close()
        # for task in [asyncio.ensure_future(is_ok(_id, url)) for _id, url in self.urls_list]:
        #     await task

    def close(self):
        self.db.commit()
        self.cursor.close()
        self.db.close()
        print("no_checked_list", len(self.no_checked_list))
