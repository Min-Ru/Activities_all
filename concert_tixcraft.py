import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime
import os
import random
import pymysql
import pymysql.cursors
import time
import sys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from act_clean import rms_db, get_add, get_ct, check_ct, drop_repeated_data
from act_clean import get_browser, explode_date, insert_data
from bs4 import BeautifulSoup
from connectgoogleapi import add_event, get_calendar
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
        URL = "https://tixcraft.com/activity#selling"  # noqa
        driver.get(URL)
        time.sleep(random.randrange(3, 5, 1))
        # 列出所有url清單
        concerts = pd.DataFrame()
        con_len = len(driver.find_elements(
            By.CLASS_NAME, 'thumbnails'))
        for i in range(con_len):
            try:
                concert_url = ('https://tixcraft.com' + BeautifulSoup(
                    driver.find_elements(
                        By.CLASS_NAME, 'thumbnails')[i].get_attribute(
                            'innerHTML'), 'html.parser').find('a')['href'])
                temp = driver.find_elements(
                    By.CLASS_NAME, 'thumbnails')[i].text
                concert_time = temp.split('\n')[0]
                concert_name = temp.split('\n')[1]
            except Exception as e:
                print('no url')
                print(e)
            else:
                concert_temp = pd.DataFrame({'name': [concert_name],
                                             'url': [concert_url]})
                concerts = pd.concat([concerts, concert_temp],
                                     ignore_index=True)
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
            driver.get(concerts['url'][item])
            time.sleep(random.randrange(10, 15, 1))
            try:
                driver.find_element(
                    By.ID, 'onetrust-accept-btn-handler').click()
            except Exception:
                print('無選單遮擋')
            try:
                driver.find_element(By.CLASS_NAME, 'buy').click()
            except Exception:
                print('無購票選單')
                print(1/0)
            finally:
                time.sleep(random.randrange(3, 5, 1))
                temp = driver.find_element(
                    By.CLASS_NAME, 'table.table-bordered').text.split("\n")
                # 取得活動個場次的地點、以及時間
                for i in range(int((len(temp)-1)/2)):
                    location_temp = driver.find_elements_by_xpath(
                        '//*[@id="gameList"]/table/tbody/tr/td[3]')[i].text
                    date_temp = driver.find_elements_by_xpath(
                        '//*[@id="gameList"]/table/tbody/tr/td[1]')[i].text
                    df_temp = pd.DataFrame(
                        {'name': [concerts['name'][item]],
                         'start_date': [dt.datetime.strptime(date_temp[:10], "%Y/%m/%d").date()],  # noqa
                         'end_date': [dt.datetime.strptime(date_temp[:10], "%Y/%m/%d").date()],  # noqa
                         'address': [location_temp]})
                    df = pd.concat([df, df_temp]).reset_index(drop=True)
        except Exception as e:
            print("失敗次數： ", retry+1)
            print(e)
            driver.quit()
            time.sleep(random.randrange(10, 15, 1))
            driver = get_browser(proxy_ip)
        else:
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
df['resource'] = '拓元售票'
df['created_date'] = today

df = mapping_address(df)

for i in range(len(df)):
    if df['city'][i] is None or df['area'][i] is None:
        getadd = get_add([df['address'][i]])[0]
        getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])
        df.loc[i, ['city']], df.loc[i, ['area']] = getCity[0], gettown[0]

insert_data(df)
