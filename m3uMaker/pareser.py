import requests
import random
from time import sleep
from m3u_parser import M3uParser


def sleep_random():
    """随机等待5-10秒防止IP被封"""
    sleep_s = random.randint(1, 10)
    sleep(sleep_s)


def check_url_ok(url):
    """检测连接是否可用"""
    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    print("正在检查URL %s" % url)
    try:
        result = requests.get(url, headers={"User-Agent": useragent}, timeout=10)
        return result.status_code == 200
    except requests.exceptions.ConnectionError as e:
        print("URL %s 访问超时" % url)
        return False


# URL 合集
urls = [
    "https://raw.fastgit.org/qwerttvv/Beijing-IPTV/master/IPTV-Unicom.m3u"
]

m3u_playlist = M3uParser()

for url in urls:
    m3u_playlist.parse_m3u(url)
    m3u_list = map(lambda item: {"name": item.get("name", ""), "url": item.get("url", "")}, m3u_playlist.get_list())
    for m in m3u_list:
        sleep_random()
        if not check_url_ok(m.get("url")):
            continue
        print("{name},{url}".format(name=m.get("name"), url=m.get("url", "")))
