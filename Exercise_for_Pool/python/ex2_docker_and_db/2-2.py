# ライブラリのインポート
from time import sleep
from bs4 import BeautifulSoup
import re
import requests
import sqlalchemy as sa

# ユーザーエージェントを設定
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
header = {
    'User-Agent': user_agent
}


# 正規表現によりメールアドレスだけを取得する関数
def extract_mail(address):
    m = re.search(r'mailto:(.*)', address)
    if m:
        return m.group(1)
    else:
        return None


# 住所を正規表現により分割する関数
def divide_address(region):
    matches = re.match(
        r'(...??[都道府県])(.+?市.+?区..+?|.+?郡.+?[町村]..+?|.+?[市区町村]..+?)([0-9|-]+)',
        region)
    return matches[1], matches[2], matches[3]

# 待機時間の設定
sec = 3

# ぐるなびのURL
guru_url = 'https://r.gnavi.co.jp/eki/0008053/rs/?date=20220725&time=1900&people=2&fw=%E5%B1%85%E9%85%92%E5%B1%8B&p={}'

# 空のリストを作成
d_list = []

# 　サイトの1〜3ページをループする
for i in range(1, 4):
    target_url = guru_url.format(i)
    print(str(i) + 'ページ目:', target_url)

    # ぐるなびのURLにアクセスし解析
    res = requests.get(target_url, headers=header)
    sleep(sec)  # アクセス過多を避けるため3秒スリープ
    soup = BeautifulSoup(res.content, 'html.parser')

    # ページ内全ての店舗を取得
    contents = soup.find_all('div', class_='style_restaurant__SeIVn')

    # 店舗ページのURLタグをforループで取得
    for content in contents:
        shop_url_tags = content.find_all('a', class_='style_titleLink__oiHVJ')

        # 店舗情報をforループで取得
        for shop_url_tag in shop_url_tags:

            # タグから店舗情報ページのURLを取得
            shop_url = shop_url_tag.get('href')
            print('{}件目:{}'.format(len(d_list)+1, shop_url))

            # 店舗ページのURLを解析
            res = requests.get(shop_url, headers=header)
            sleep(sec)
            soup = BeautifulSoup(res.content, 'html.parser')

            # 店舗情報を取得
            shop_info = soup.find('table', class_='basic-table')

            # 店舗情報の取得結果を変数に格納する

            name = shop_info.find('p', id='info-name',
                                  class_='fn org summary').text
            phone_num = shop_info.find('span', class_='number').text
            # メールアドレスを取得
            try:
                mail_tag = shop_info.find_all('a')[4]  # aタグの4番目にメールアドレス
            except IndexError:
                mail = None
            else:
                mail = mail_tag.get('href')
                mail = extract_mail(mail)
            region = shop_info.find('span', class_='region').text
            # 住所を正規表現により分割する関数
            preficture, city, address = divide_address(region)  # 住所を分割
            # 建物名を取得
            try:
                building = shop_info.find('span', class_='locality').text
            except AttributeError:
                building = None

            url = None
            ssl = None

            # 取得したすべての情報をタプルに格納する
            d = (name, phone_num, mail, preficture, city,
                 address, building, url, ssl
            )


            d_list.append(d)

            # 50件取得したらループを抜け出す
            if len(d_list) == 50:
                print('50件取得しました')
                break
            else:
                continue
            break
        else:
            continue
        break

# MySQLに接続。
url = 'mysql+mysqldb://root:12345678@localhost/ex2?charset=utf8'
engine = sa.create_engine(url, echo=True)

engine.execute('DROP TABLE IF EXISTS {}'.format("ex2_2"))
# テーブルを作成
engine.execute('''
    CREATE TABLE ex2_2 (
    `店舗名` TEXT,
    `電話番号` TEXT,
    `メールアドレス` TEXT,
    `都道府県` TEXT,
    `市区町村` TEXT,
    `番地` TEXT,
    `建物名` TEXT,
    `URL` TEXT,
    `SSL` TEXT
    )
    ''')

# データを挿入。
ins = "INSERT INTO ex2_2 (`店舗名`, `電話番号`, `メールアドレス`, `都道府県`, `市区町村`, `番地`, `建物名`, `URL`, `SSL`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

for d in d_list:
    engine.execute(ins,d)
