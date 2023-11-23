import pandas as pd
import datetime as dt
from datetime import datetime
import re
import random
import time
import sys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from act_clean import get_ct
from act_clean import get_browser, insert_data
load_dotenv()
today = dt.datetime.today().strftime("%Y-%m-%d")

try:
    proxy_ip = sys.argv[1]
except Exception:
    print("輸入代理IP：")
    sys.exit()

run_list = pd.DataFrame()
driver = get_browser(proxy_ip)
URL = "https://www.npac-ntt.org/program/events"  # noqa

for retry in range(3):
    try:
        driver.get(URL)
        time.sleep(random.randrange(3, 5, 1))
        show_name = driver.find_elements(By.CLASS_NAME, 'card-title')
    except Exception:
        print('網頁載入失敗')
    else:
        if len(show_name) != 0:
            break


# 列出所有url清單
url_list = []
p1 = re.compile(r'["](.*?)["]', re.S)
for name_element in show_name:
    try:
        url = ('https://www.npac-ntt.org/' +
                   re.findall(p1, name_element.get_attribute('innerHTML'))[0].replace('amp;', '')) # noqa
    except Exception:
        print('no url')
    else:
        url_list.append(url)

show_list = pd.DataFrame()
# 根據url清單爬取頁面
for url in url_list:
    time.sleep(random.randrange(3, 5, 1))
    # 網頁阻擋，retry3次
    for retry in range(3):
        try:
            driver.get(url)
            time.sleep(random.randrange(3, 5, 1))
            show_name = driver.find_element(By.CLASS_NAME, 'post-title').text
            show_type = driver.find_element(By.CLASS_NAME, 'post-type').text
            show_place = driver.find_element(By.CLASS_NAME, 'post-place').text
            show_time = driver.find_element(
                By.XPATH, '//*[@id="programDetail"]/div/div[3]/div/div[2]/div/div[1]/div[1]/div[3]/div[2]/div').text.split('\n')  # noqa
            # 取得活動名稱、地點、以及時間
            list_temp = pd.DataFrame(
                {'name': [show_name],
                 'keywords': [show_type],
                 'location': [show_place],
                 'start_date': [show_time]})
            list_temp = list_temp.explode('start_date')
            show_list = pd.concat([show_list, list_temp]).reset_index(drop=True)  # noqa
        except Exception as e:
            print(e)
            print("失敗次數： ", retry+1)
            driver.quit()
            time.sleep(random.randrange(10, 15, 1))
            driver = get_browser(proxy_ip)
        else:
            if list_temp.empty is False:
                break
try:
    driver.quit()
except Exception:
    print("browser不正常關閉")

# 資料格式調整
df = show_list.copy()
df["new_add"] = None
df['category'] = None
df['importance'] = None
df['correlation'] = None
df['city_id'] = None
df['area_id'] = None
df['calendar_id'] = None
df['event_id'] = None
df['resource'] = '台中國家歌劇院'
df['created_date'] = today

# 處理延期
df['start_date'] = df.apply(
    lambda row: row['start_date'].split('至')[-1] if '延期' in row['name'] else row['start_date'], axis=1)  # noqa
# 提取日期部分
df['start_date'] = df['start_date'].str.extract(r'(\d{4}/\d{1,2}/\d{1,2})')
# 將字符串日期轉換為 datetime.date 格式
df['start_date'] = pd.to_datetime(df['start_date']).dt.date
df['end_date'] = df['start_date']

address = '407025台中市西屯區惠來路二段101號'
df['address'] = address + '(' + df['location'] + ')'
df['city'], df['area'] = get_ct(address)[0], get_ct(address)[1]

insert_data(df)
