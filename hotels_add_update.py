#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 10:16:38 2023

@author: iriswei
更新hotels city & area
"""

import pandas as pd
from act_clean import get_add, get_ct, check_ct
import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from datetime import datetime
today = datetime.today()
load_dotenv()

def get_db(data_base, sql_txt):  # noqa
    if data_base == 'pms':
        db = pymysql.connect(host=os.getenv('DB_HOST_pms'), port=3307,
                             user=os.getenv('DB_USERNAME_pms'),
                             passwd=os.getenv('DB_PASSWORD_pms'),
                             db=os.getenv('DB_NAME_pms'), charset='utf8')
    elif data_base == 'rms':
        db = pymysql.connect(host=os.getenv('DB_HOST'), port=3306,
                             user=os.getenv('DB_USERNAME'),
                             passwd=os.getenv('DB_PASSWORD'),
                             db=os.getenv('DB_NAME'), charset='utf8')
    cursor = db.cursor()
    cursor.execute(sql_txt)
    result = cursor.fetchall()
    db.close()
    field_names = [i[0] for i in cursor.description]
    dt = pd.DataFrame(list(result), columns=field_names)
    return dt


def reverse_string(input_str):
    # 以逗號分割字串成列表
    str_list = input_str.split(',')

    # 移除列表中的空格
    str_list = [s.strip() for s in str_list]

    # 將列表反轉並以空字串連接
    reversed_str = ''.join(str_list[::-1])

    return reversed_str


hotels_null = get_db('rms', "select * from hotels " +
                     "where area_id is null and is_closed = 0 ")
hotels_null_2 = get_db('rms', "select * from hotels where city_id is null " +
                       "and area_id is not null and is_closed = 0")
all_null = pd.concat([hotels_null, hotels_null_2])
all_null = all_null.drop_duplicates(subset=['id'])
df = all_null.reset_index(drop=True)

city_list = get_db('rms', "select id, name from city")
town_list = get_db('rms', "select id, city_id, name from areas")
df['city'] = None
df['area'] = None
df['new_city_id'] = None
df['new_area_id'] = None
df['new_add'] = None
df['Type'] = None

for i in range(len(df)):
    print('i = ', i)
    print('hotel:', df['name'][i])
    getadd = df['address'][i]
    # 以現有地址判斷
    getCity, gettown = check_ct(
        [get_ct(df['address'][i])[0]], [get_ct(df['address'][i])[1]])
    if getCity != ['']:
        df.loc[i, ["city"]] = getCity[0]
        print('city:', getCity[0])
    # 如果仍無area, 且有地址的情況，拆分area、city
    # 1.
    if gettown == [''] and df['address'][i] is not None and df['agoda_tag_id'][i] is not None: # noqa
        try:
            city, area = get_ct(reverse_string(df['address'][i]))
            # 未知縣市情況
            if len(city) == 2:
                # 獲得縣市
                try:
                    getCity, gettown = check_ct([city + '市'], [area])
                    if getCity != ['']:
                        df.loc[i, ["new_add"]] = getadd
                        df.loc[i, ["city"]] = getCity[0]
                        org_type = 1
                    else:
                        print(1/0)
                except Exception:
                    getCity, gettown = check_ct([city + '縣'], [area])
                    if getCity != ['']:
                        df.loc[i, ["new_add"]] = getadd
                        df.loc[i, ["city"]] = getCity[0]
                    else:
                        print(1/0)
            else:
                getCity, gettown = check_ct([city], [area])
                if getCity != ['']:
                    df.loc[i, ["new_add"]] = getadd
                    df.loc[i, ["city"]] = getCity[0]
                    df.loc[i, ["Type"]] = 1
        except Exception:
            print("Not matched split")
            getCity = ['']
    else:
        df.loc[i, ["area"]] = gettown
        df.loc[i, ["Type"]] = 0
    # 如果仍無area，則用address重新搜尋
    # 2.
    if gettown == [''] and df['address'][i] is not None:
        getadd = get_add([df['address'][i]])[0]
        getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])
        df.loc[i, ["new_add"]] = getadd
        if getCity != ['']:
            df.loc[i, ["new_add"]] = getadd
            df.loc[i, ["city"]] = getCity[0]
    else:
        df.loc[i, ["new_add"]] = getadd
        df.loc[i, ["area"]] = gettown
        df.loc[i, ["Type"]] = 1
    # 如果無area，則重新用coordinate判斷
    # 3.
    if gettown == [''] and df['coordinate'][i] is not None and df['coordinate'][i] != '0,0' and df['coordinate'][i] != '1111,1111': # noqa
        getadd = get_add([df['coordinate'][i]])[0]
        getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])
        if getCity != '':
            df.loc[i, ["new_add"]] = getadd
            df.loc[i, ["city"]] = getCity[0]
    else:
        df.loc[i, ["area"]] = gettown
        df.loc[i, ["Type"]] = 2
    # 如果仍無area，則用名稱重新搜尋
    # 4.
    if gettown == ['']:
        getadd = get_add([df['name'][i]])[0]
        getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])
        if getCity != ['']:
            df.loc[i, ["new_add"]] = getadd
            df.loc[i, ["city"]] = getCity[0]
            df.loc[i, ["Type"]] = 4
            df.loc[i, ["area"]] = gettown
    else:
        df.loc[i, ["area"]] = gettown
        df.loc[i, ["Type"]] = 3

    # 若有city, 則判斷city_id
    if df['city'][i] is not None or df['city'][i] != '':
        try:
            df.loc[i, ['new_city_id']] = int(city_list[city_list['name'] == df['city'][i]]['id'])  # noqa
        except Exception:
            print("Not matched city")
        # 若有area, 則判斷area_id
    if df['area'][i] is not None and df['area'][i] != '':
        try:
            df.loc[i, ['new_area_id']] = int(
                town_list[(town_list['name'] == df['area'][i]) &
                          (town_list['city_id'] == df['new_city_id'][i])]['id'])  # noqa
        except Exception:
            print("Not matched area")


# 更新資料庫
for i in range(len(df)):
    if df['new_city_id'][i] != '' or df['new_city_id'][i] is not None:

        db = pymysql.connect(host=os.getenv('DB_HOST'), port=3306,
                             user=os.getenv('DB_USERNAME'),
                             passwd=os.getenv('DB_PASSWORD'),
                             db=os.getenv('DB_NAME'), charset='utf8')
        cursor = db.cursor()

        sql = ("update`hotels` set city_id=%s, area_id=%s where id=%s")
        temp = pd.DataFrame({'new_city_id': [df['new_city_id'][i]],
                             'new_area_id': [df['new_area_id'][i]],
                             'id': [df['id'][i]]})
        cursor.executemany(sql, temp.values.tolist())
        db.commit()
        db.close()
