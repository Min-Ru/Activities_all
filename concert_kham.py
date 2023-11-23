import pandas as pd
import datetime as dt
from datetime import datetime
import re
import os
import random
import pymysql
import pymysql.cursors
import time
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from act_clean import rms_db, get_add, get_ct, check_ct, drop_repeated_data
from act_clean import get_browser, explode_date, insert_data
from connectgoogleapi import add_event, get_calendar
import sys
import urllib
load_dotenv()
today = dt.datetime.today().strftime("%Y-%m-%d")

try:
    proxy_ip = sys.argv[1]
except Exception:
    print("輸入代理IP：")
    sys.exit()

# 載入網頁
for retry in range(3):
    try:
        driver = get_browser(proxy_ip)
        # 演唱會
        URL = "https://kham.com.tw/application/UTK01/UTK0101_06.aspx?TYPE=1&CATEGORY=205"  # noqa
        driver.get(URL)
        time.sleep(random.randrange(3, 5, 1))
        # 列出所有url清單
        concerts = pd.DataFrame()
        concert_item = driver.find_elements(By.CLASS_NAME, 'd_frame')
        p1 = re.compile(r'["](.*?)["]', re.S)
        for ele in concert_item:
            try:
                concert_url = ('https://kham.com.tw/application' +
                           re.findall(p1, ele.get_attribute('innerHTML'))[0][2:]) # noqa
                concert_name = ele.text.split('\n')[0]
            except Exception as e:
                print('no url')
                print(e)
            concert_temp = pd.DataFrame({'name': [concert_name],
                                         'url': [concert_url]})
            concerts = concerts.append(concert_temp)
        break
    except Exception as e:
        print("網頁載入失敗： ", retry+1)
        print(e)
concerts = concerts.reset_index(drop=True)

df = pd.DataFrame()
# 根據url清單爬取頁面
for item in range(len(concerts)):
    df_temp = pd.DataFrame()
    # 可能被擋，retry3次
    for retry in range(3):
        try:
            time.sleep(random.randrange(3, 5, 1))
            driver.get(concerts['url'][item])
            time.sleep(random.randrange(15, 30, 1))
            concert_detail = driver.find_elements(By.CLASS_NAME, 'ShowingContent') # noqa
            # 時間、地點、價格
            num_concert = int(len(driver.find_elements(By.CLASS_NAME,
                                                       'ShowingContent'))/3)
            # 廣告阻擋, 重新載入頁面, 最多3次
            j = 0
            while concert_detail == [] and j < 3:
                driver.refresh()
                time.sleep(random.randrange(3, 5, 1))
                concert_detail = driver.find_elements(By.CLASS_NAME, 'ShowingContent') # noqa
                # 判斷有幾個場次
                num_concert = int(len(driver.find_elements(
                    By.CLASS_NAME, 'ShowingContent'))/3)
                j += 1
            # 取得活動各場次的地點、以及時間
            for num in range(num_concert):
                driver.get(concerts['url'][item])
                time.sleep(random.randrange(15, 30, 1))
                # 活動時間
                date_temp = driver.find_elements(
                    By.CLASS_NAME, 'ShowingContent')[num*3].text  # noqa
                # 活動地點(僅地點名稱，非地址)
                location = driver.find_elements(
                    By.CLASS_NAME, 'ShowingContent')[num*3 + 1].text
                try:
                    # 取得google map連結
                    url_temp = driver.find_elements(By.CLASS_NAME, 'ShowingContent')[num*3 + 1].get_attribute('innerHTML') # noqa
                    address_url = re.findall(p1, url_temp)[1].replace('amp;', '') # noqa
                    add_temp = urllib.parse.unquote(
                        address_url.replace(
                            "http://maps.google.com.tw/maps?f=q&hl=zh-TW&geocode=&t=&z=16&q=", ""))  # noqa
                except Exception as e:
                    print(e)
                else:
                    df_temp = pd.DataFrame({'name': [concerts['name'][item]],  # noqa
                                              'start_date': [dt.datetime.strptime(date_temp[:10], "%Y/%m/%d").date()],  # noqa
                                              'end_date': [dt.datetime.strptime(date_temp[-18:-8], "%Y/%m/%d").date()],  # noqa
                                              'location': [location],
                                              'address': [add_temp]})
                    df = pd.concat([df, df_temp]).reset_index(drop=True)  # noqa
        except Exception as e:
            print("失敗次數： ", retry+1)
            print(e)
            driver.quit()
            time.sleep(random.randrange(60, 180, 1))
            driver = get_browser(proxy_ip)
        else:
            if df_temp.empty is False:
                break
try:
    driver.quit()
except Exception:
    print("browser不正常關閉")


# calendar connect
service = get_calendar("PMS_account/token.json", "PMS_account/pmscalendar.json")  # noqa
city_list = rms_db("select id, name from city")
town_list = rms_db("select id, city_id, name from areas")
calendar_list = rms_db("select * from calendars")
calendar_list['city'] = calendar_list['name'].str.split("活動-").str.get(1)
# 資料格式調整
df['category'] = None
df['importance'] = None
df['correlation'] = None
df['city_id'] = None
df['area_id'] = None
df['calendar_id'] = None
df['event_id'] = None
df['resource'] = '寬宏售票'
df['created_date'] = today
df['city'], df['area'] = '', ''


for i in range(len(df)):
    # 地址處理
    add = df['address'][i]  # map url的地址
    location = df['location'][i]  # 地址
    # 判斷縣市與行政區
    getCity, gettown = check_ct([get_ct(add)[0]], [get_ct(add)[1]])
    # 若為空, 則搜尋新地址
    if gettown == ['']:
        try:
            getCity, gettown = check_ct([get_ct(location)[0]],
                                        [get_ct(location)[1]])
            if gettown == ['']:
                print(1//0)
            else:
                df.loc[i, ['address']] = location
        except Exception:
            getadd = get_add([location])[0]
            getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])  # noqa
            df.loc[i, ['address']] = location

    df.loc[i, ['city']], df.loc[i, ['area']] = getCity[0], gettown[0]

insert_data(df)
