from lxml import html
import requests


def get_sp500_tickers():
    url = "https://stockanalysis.com/list/sp-500-stocks/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    doc = html.fromstring(response.content)
    tickers = [doc.xpath(f'/html/body/div/div[1]/div[2]/main/div[2]/div/div/div[4]/table/tbody/tr[{i}]/td[2]/a')[0].text
               for i in range(1, 501)]

    return tickers

if __name__ == '__main__':
    ticks = get_sp500_tickers()
    print(ticks)