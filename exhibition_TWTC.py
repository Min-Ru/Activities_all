#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 15 11:33:32 2023

@author: iriswei
"""

import pandas as pd
import datetime as dt
from datetime import datetime
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from act_clean import rms_db, get_ct, check_ct, drop_repeated_data
from act_clean import explode_date, insert_data
from connectgoogleapi import add_event, get_calendar
from bs4 import BeautifulSoup
import sys
import requests
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
        exhibition = pd.DataFrame()
        html = requests.get("https://www.twtc.com.tw/exhibition?p=home")
        try:
            soup = BeautifulSoup(html.text, 'html.parser')
            table = soup.find('table',
                              class_='table table-striped fixed date_table')
            tbody = table.find('tbody')
            rows = tbody.find_all('tr')
        except Exception as e:
            print(e)
        else:
            for row in rows:
                columns = row.find_all('td')
                exhibition_date = columns[0].text.strip()
                exhibition_name = columns[1].text.strip()
                exhibition_hall = columns[4].text.strip()
                start_date = dt.datetime.strptime(
                    str(dt.datetime.today().year) + '-' +
                    exhibition_date[:5].replace('/', '-'), "%Y-%m-%d").date()
                end_date = dt.datetime.strptime(
                    str(dt.datetime.today().year) + '-' +
                    exhibition_date[-5:].replace('/', '-'), "%Y-%m-%d").date()
                exhibition_temp = pd.DataFrame(
                    {'name': [exhibition_name.replace('\nmore', '')],
                     'location': [exhibition_hall],
                     'start_date': [start_date],
                     'end_date': [end_date]})
                exhibition = pd.concat([exhibition, exhibition_temp],
                                       ignore_index=True)
            break
    except Exception as e:
        print("網頁載入失敗： ", retry+1)
        print(e)

exhibition = exhibition.reset_index(drop=True)


# 將一展覽在多館展出，拆分至各館
new_data = []
# 遍歷原始數據中的每一行
for index, row in exhibition.iterrows():
    # 拆分 "location" 列的字符串
    locations = row["location"].split("南港展覽館")
    for location in locations:
        try:
            if location == '':
                print(1/0)
        except Exception as e:
            print(e)
        else:
            new_row = {
                "name": row["name"],
                "location": location  if location == "世貿一館" or location == '' else "南港展覽館" + location,  # noqa
                "start_date": row["start_date"],
                "end_date": row["end_date"]}
            new_data.append(new_row)

df = pd.DataFrame(new_data).dropna(subset=["location"])

# mapping各館地址
address_dict = {
    "世貿一館": "110台北市信義區信義路五段5號",
    "南港展覽館1館": "115台北市南港區經貿二路1號",
    "南港展覽館2館": "115台北市南港區經貿二路2號"
}
df["address"] = df["location"].map(address_dict)


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
df['resource'] = '台北世貿中心'
df['created_date'] = today
df['city'], df['area'] = '', ''

df = mapping_address(df)

insert_data(df)
