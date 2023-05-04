import requests

TEXT_URL_INDEX = "https://raw.fastgit.org/biancangming/wtv/master/txt/index.txt"


def getRaw(url):
    try:
        return requests.get(url).text.split("\n")
    except Exception as e:
        return []


def getM3us():
    urls = []
    # 链接合集
    tv_urls = getRaw(TEXT_URL_INDEX)
    # 逐个解析url
    for url in tv_urls:
        print(url)
        m3u = filter(bool, getRaw(url))
        urls.extend(m3u)
    return urls