from time import sleep

import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# アイドリングタイム
sec = 3


# ボタンを押す関数
def button_click(button_text):
    buttons = driver.find_elements_by_tag_name("button")
    for button in buttons:
        if button.text == button_text:
            button.click()
            break

# aタグの'href'を取得する関数
def get_href(a_tag_text):
    a_tags = driver.find_elements_by_tag_name('a')
    for a_tag in a_tags:
        if a_tag.text == a_tag_text:
            return a_tag.get_attribute('href')
    return ''

# 正規表現によりメールアドレスだけを取得する関数
def extract_mail(address):
    m = re.search(r'mailto:(.*)', address)
    if m:
        return m.group(1)
    else:
        return ''

# 住所を正規表現により分割する関数
def divide_address(region):
  matches = re.match(r'(...??[都道府県])(.+?市.+?区..+?|.+?郡.+?[町村]..+?|.+?[市区町村]..+?)([0-9|-]+)' , region)
  return matches[1], matches[2], matches[3]

# SSL証明書の有無を確認する関数
def ssl_check(url):
    if url == '':
        return ''
    else:
        m = re.match(r'https', url)
        if m:
            return 'TRUE'
        else:
            return 'FALSE'


# ChromeDriverの場所を指定
chrome_path = '/Users/fukunagaatsushi/Documents/Final_Answer_Scraping/chromedriver'

options = Options()

# ユーザーエージェントの設定
UA = 'Mozilla/5.0 (Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15'
options.add_argument('--user-agent=' + UA)

#Chromeの場所を指定
options.binary_location = '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta'

driver = webdriver.Chrome(executable_path=chrome_path, options=options)


# ぐるなびのURLにアクセス
url = 'https://www.gnavi.co.jp/'
driver.get(url)
sleep(sec)

# エリアとジャンルを指定して検索
query_1 = '銀座駅'
query_2 = '寿司屋'
area_search_box = driver.find_element_by_id('js-suggest-area')
area_search_box.send_keys(query_1)
shop_search_box = driver.find_element_by_id('js-suggest-shop')
shop_search_box.send_keys(query_2)
# 検索ボタンを押下
button_click('検索する')
sleep(sec)

d_list = []
i = 0

# whileループで店舗情報を取得
while True:
    shop_page_urls = driver.find_elements_by_class_name(
        'style_restaurant__SeIVn')
    shop_page_url = shop_page_urls[i]
    shop_page_url.click()
    sleep(sec)

    # 店舗情報を取得
    name = driver.find_element_by_id('info-name').text
    phone_num = driver.find_element_by_class_name('number').text
    mail = get_href('お店に直接メールする')
    mail = extract_mail(mail)
    region = driver.find_element_by_class_name('region').text
    # 住所を分割
    preficture, city, address = divide_address(region)
    # 建物名を取得
    b = driver.find_elements_by_class_name('locality')
    if len(b) > 0:
        building = b[0].text
    else:
        building = ''

    url = get_href('お店のホームページ')
    ssl = ssl_check(url)

    # 辞書に格納
    d = {
        '店舗名': name,
        '電話番号': phone_num,
        'メールアドレス': mail,
        '都道府県': preficture,
        '市区町村': city,
        '番地': address,
        '建物名': building,
        'URL': url,
        'SSL': ssl
    }

    i += 1

    # 未取得の店舗であれば取得
    if d not in d_list:
        d_list.append(d)
        print('{}件目取得'.format(len(d_list)))

    # 検索結果ページへ戻る
    driver.back()
    sleep(sec)

    # 50件取得したらループを抜け出す
    if len(d_list) == 50:
        print('50件取得しました')
        break
    # 20件取得したら'>'ボタンをクリックしてページ遷移
    elif i == 20:
        print('次のページへ遷移')
        i = 0
        next_page = driver.find_element_by_class_name('style_nextIcon__M_Me_')
        next_page.click()
        sleep(sec)
    else:
        continue

# DataFrameに格納
df = pd.DataFrame(d_list)
# データフレームをCSV出力する
df.to_csv('1-2.csv', index=None, encoding='utf-8-sig')

driver.quit()