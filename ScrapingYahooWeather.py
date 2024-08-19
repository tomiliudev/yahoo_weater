import datetime
import requests
from bs4 import BeautifulSoup
# from dotenv import load_dotenv
import os
import pytz

# 日本時間のタイムゾーンを設定
jst = pytz.timezone('Asia/Tokyo')
# 現在の日時を日本時間で取得
current_time_jst = datetime.datetime.now(jst)

def fetch_weather_data(url):
    response = requests.get(url)
    return response.content

def parse_weather_data(html_content, date_id_str):
    soup = BeautifulSoup(html_content, 'html.parser')
    weather_html = soup.find('div', id=date_id_str)
    weather_table = weather_html.find('table', class_='yjw_table2')
    weather_table_tr_list = weather_table.find_all('tr')

    title = []
    time_data = [[] for _ in range(8)]

    count = 0
    for tr in weather_table_tr_list:
        if count >= 3:
            break

        td_list = tr.find_all('td')
        for i, td in enumerate(td_list):
            text = td.text.replace('\n', '').replace(' ', '')
            if i == 0:
                title.append(text)
            else:
                time_data[i-1].append(text)

        count += 1

    return title, time_data

def parse_week_weather_data(html_content, date_id_str):
    soup = BeautifulSoup(html_content, 'html.parser')
    weather_html = soup.find('div', id=date_id_str)
    weather_table = weather_html.find('table', class_='yjw_table')
    weather_table_tr_list = weather_table.find_all('tr')

    title = []
    time_data = [[] for _ in range(6)]

    for tr_idx, tr in enumerate(weather_table_tr_list):
        td_list = tr.find_all('td')
        for td_idx, td in enumerate(td_list):
            text = td.text.replace('\n', '').replace(' ', '')
            if td_idx == 0:
                title.append(text)
            else:
                if tr_idx == 2:
                    temps = td.find_all('font')
                    time_data[td_idx-1].append(f"{temps[0].text}/{temps[1].text}")
                else:
                    time_data[td_idx-1].append(text)

    return title, time_data

def format_weather_data(title, time_data, date_info=None):
    weather_title =""
    if date_info is None:
        weather_title = "<週間天気>"
    else:
        date_str = date_info.strftime('%Y/%m/%d')
        week = ['月', '火', '水', '木', '金', '土', '日']
        week_jp = week[date_info.weekday()]
        weather_title = f"<{date_str}({week_jp})の天気>"

    time_data_str = ""
    # time_dataをfor文で回して、文字列を作成
    for i, data in enumerate(time_data):
        time_data_str += f"{' '.join(data)}\n"

    weather_str = f"""
{weather_title}
{' '.join(title)}
{'==========='}
{time_data_str}
"""
    return weather_str

def send_line_notify(notification_message, access_token_list):
    for access_token in access_token_list:
        # HTTPリクエストのヘッダー
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # メッセージデータ
        data = {
            'message': notification_message
        }

        # LINE NotifyのAPIエンドポイント
        url = 'https://notify-api.line.me/api/notify'

        # POSTリクエストを送信してメッセージを送る
        response = requests.post(url, headers=headers, data=data)

        # 結果の確認
        if response.status_code == 200:
            print('メッセージが送信されました！')
        else:
            print(f'エラーが発生しました: {response.status_code}')
            print(response.text)



def send_weather_data_to_line(html_content, access_token, date_info, access_token_list):
    title, time_data = parse_weather_data(html_content, access_token)
    weather_str = format_weather_data(title, time_data, date_info)
    send_line_notify(weather_str, access_token_list)

def send_week_weather_data_to_line(html_content, access_token, access_token_list):
    title, time_data = parse_week_weather_data(html_content, access_token)
    weather_str = format_weather_data(title, time_data)
    send_line_notify(weather_str, access_token_list)

def main():
    # .env ファイルをロード
    # load_dotenv()

    url = f'https://weather.yahoo.co.jp/weather/jp/11/4310/11223.html'
    html_content = fetch_weather_data(url)

    access_token_list = os.getenv('LINE_NOTIFY_ACCESS_TOKEN_LIST').split(",")

    # 今日の天気を送信
    today = current_time_jst.date()
    send_weather_data_to_line(html_content, 'yjw_pinpoint_today', today, access_token_list)

    # 明日の天気を送信
    tomorrow = today + datetime.timedelta(days=1)
    send_weather_data_to_line(html_content, 'yjw_pinpoint_tomorrow', tomorrow, access_token_list)

    # 週間天気を送信
    send_week_weather_data_to_line(html_content, 'yjw_week', access_token_list)


if __name__ == "__main__":
    main()
