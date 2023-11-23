import pandas as pd
import datetime as dt
from datetime import datetime
import json
import codecs
import requests
import os
import pymysql
import pymysql.cursors
from connectgoogleapi import get_calendar, add_event
from act_clean import rms_db, get_add, get_ct, check_ct, drop_repeated_data
from act_clean import explode_date, insert_data
from dotenv import load_dotenv
load_dotenv()
today = dt.datetime.today().date()


# 讀取政府公開平台資料-json
def get_json(link):
    act_request = requests.get(link)
    decoded_data = codecs.decode(act_request.text.encode(), 'utf-8-sig')
    data = json.loads(decoded_data)

    return data


# 政府資料開放平臺-活動 - 觀光資訊資料庫
link = 'https://media.taiwan.net.tw/XMLReleaseALL_public/activity_C_f.json'
data = get_json(link)
data = data['XML_Head']['Infos']['Info']
df = pd.DataFrame(data)
# 移除暫停辦理的活動
r = len(df)
for i in range(r):
    if df['Cycle'][i] is not None and '暫停辦理' in df['Cycle'][i]:
        df = df.drop([i])
    else:
        df.loc[i, ['Start']] = dt.datetime.strptime(df['Start'][i][0:10], "%Y-%m-%d").date()  # noqa
        df.loc[i, ['End']] = dt.datetime.strptime(df['End'][i][0:10], "%Y-%m-%d").date()  # noqa
df = df.reset_index(drop=True)
df = df[(df['End'] >= today)].reset_index(drop=True)
# calendar connect
service = get_calendar("PMS_account/token.json", "PMS_account/pmscalendar.json")  # noqa
# 政府資料開放平台-活動 - 觀光資訊資料庫
city_list = rms_db("select id, name from city")
town_list = rms_db("select id, city_id, name from areas")
calendar_list = rms_db("select * from calendars")
calendar_list['city'] = calendar_list['name'].str.split("活動-").str.get(1)
df["new_add"] = None
df['category'] = None
df['importance'] = None
df['correlation'] = None
df['city_id'] = None
df['area_id'] = None
df['calendar_id'] = None
df['event_id'] = None
df['resource'] = '政府資料開放平台_觀光資訊資料庫'
df['created_date'] = today
df['city'], df['area'] = check_ct(df['Region'], df['Town'])

for i in range(len(df)):
    # 地址處理
    add = df['Add'][i]  # 地址
    city = df['city'][i]  # 縣市
    area = df['area'][i]  # 行政區
    location = df['Location'][i]  # 縣市+行政區
    # 以location為主, 判斷縣市與行政區
    getCity, gettown = check_ct([get_ct(location)[0]], [get_ct(location)[1]])
    # 若為空, 則以Add判斷
    if gettown == [''] and add is not None:
        getCity, gettown = check_ct([get_ct(add)[0]], [get_ct(add)[1]])
        # 仍為空, 且add為空或為全國
        if gettown == ['']:
            if add == '' or add == '全國':
                getCity, gettown = [city], [area]
                df.loc[i, ["new_add"]] = city + area
            # 仍為空, 且add不為空, 則用add搜尋新地址
            else:
                getadd = get_add([add])[0]
                getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])  # noqa
                if gettown == ['']:
                    getCity, gettown = [city], [area]
                    df.loc[i, ["new_add"]] = city + area
                # 不為空, 則新地址為新取得的地址
                else:
                    df.loc[i, ["new_add"]] = add
        # 不為空, 則新地址為add
        else:
            df.loc[i, ["new_add"]] = add
    # 不為空, 則新地址為location
    else:
        df.loc[i, ["new_add"]] = location
    # 最終city, area欄位
    df.loc[i, ['city']], df.loc[i, ['area']] = getCity[0], gettown[0]

    # 若地址為空白
    if df["new_add"][i] == '' or df["new_add"][i] is None:
        if city != '' and city is not None:
            df.loc[i, ["new_add"]] = city + area
        elif add != '' and add is not None:
            df.loc[i, ["new_add"]] = add
        else:
            df.loc[i, ["new_add"]] = location

insert_data(df)
