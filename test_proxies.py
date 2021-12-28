import requests
from bs4 import BeautifulSoup


def getProxies():
    r = requests.get("https://free-proxy-list.net/")
    soup = BeautifulSoup(r.content, "html.parser")
    table = soup.find("tbody")
    proxies = []
    for row in table:
        if row.find_all("td")[4].text == "elite proxy":
            proxy = ":".join([row.find_all("td")[0].text, row.find_all("td")[1].text])
            proxies.append(proxy)
        else:
            pass
    return proxies


if __name__ == "__main__":
    # print(getProxies()[1:3])

    proxy = "64.235.204.107:8080"
    resp = requests.get(
        "https://www.google.com/",
        # "https://www.ebay-kleinanzeigen.de",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        },
        proxies={"http": "http://" + proxy, "https": "https://" + proxy},
        timeout=5,
    )
    print(resp)
    # resp.body
