def get_browser(PROXY=None):
    from selenium import webdriver
    from fake_useragent import UserAgent
    ua = UserAgent()
    chrome_options = webdriver.ChromeOptions()
    if PROXY is not None:
        chrome_options.add_argument('--proxy-server=http://'+PROXY)  # PROXY
    chrome_options.add_argument("user-agent={}".format(ua.random))
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")  # 不使用sandbox
    chrome_options.add_argument("--incognito")  # 無痕模式
    chrome_options.add_experimental_option('excludeSwitches',
                                           ['enable-automation'])
    chrome_options.add_argument('--lang=zh-TW')
    chrome_options.add_experimental_option('prefs',
                                           {'intl.accept_languages': 'zh-TW'})
    chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面.
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# 取得資料庫資料
def rms_db(sql_txt):  # noqa
    import pandas as pd
    import os
    import pymysql
    import pymysql.cursors
    from dotenv import load_dotenv
    load_dotenv()
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


# input地址列表，根據地址(地標、旅遊景點)以google map搜尋其完整地址訊息
# 去除地址(地標、旅遊景點)字串中包含的括弧等無關字眼
# 回傳新地址
def get_add(add_list):
    import re
    import time
    import random
    from selenium.webdriver.common.by import By
    driver = get_browser('69.30.227.194:2000')  # webdriver.Chrome(options=options) noqa
    new_add_list = []
    for add in add_list:
        # 去除()與()內的資料
        add_nd = re.sub(u"\\（.*?）|\\{.*?}|\\[.*?]|\\【.*?】", '', add)
        add_nd = add_nd.replace("查看地圖", "")
        add_temp = ''
        # 用於查詢地址
        URL = "https://www.google.com/maps/place?q=" + add_nd
        for retry in range(3):
            print('retry = ', retry)
            # 點擊第一個地點
            try:
                driver.get(URL)
                try:
                    # google cookies確認
                    time.sleep(random.randrange(15, 30, 1))
                    driver.find_element(By.XPATH,
                        '/html/body/div[2]/div[1]/div[3]/form[2]/input[14]').click()
                except Exception:
                        print("沒有選單遮擋")
                finally:
                    time.sleep(random.randrange(15, 30, 1))
                    driver.find_element(By.CLASS_NAME, 'Nv2PK.THOPZb.CpccDe').click()  # noqa
                    time.sleep(random.randrange(15, 30, 1))
            except Exception:
                # 更換class點擊第一個地點
                try:
                    driver.find_element(By.CLASS_NAME, 'hfpxzc').click()
                    time.sleep(random.randrange(15, 30, 1))
                except Exception:
                    print("address info was not matched")
            finally:
                try:
                    add_temp = driver.find_element(By.CLASS_NAME, 'Io6YTe.fontBodyMedium').text  # noqa
                    time.sleep(random.randrange(15, 30, 1))
                    if add_temp == '傳送到你的手機' or add_temp == '確認或修正這個位置' or add_temp == '':  # noqa
                        print(1/0)
                # 若無資料, 則更換class
                except Exception:
                    try:
                        add_temp = driver.find_element(By.CLASS_NAME, 'DkEaL').text  # noqa
                        time.sleep(random.randrange(15, 30, 1))
                        if add_temp == '傳送到你的手機' or add_temp == '確認或修正這個位置' or add_temp == '' or add_temp == '旅遊景點':  # noqa
                            print(1/0)
                    # 若無資料, 則更換class
                    except Exception:
                        try:
                            add_temp = driver.find_element(By.CLASS_NAME, 'Io6YTe.fontBodyMedium.kR99db ').text  # noqa
                            time.sleep(random.randrange(15, 30, 1))
                            if add_temp == '傳送到你的手機' or add_temp == '確認或修正這個位置' or add_temp == '' or add_temp == '旅遊景點':  # noqa
                                print(1/0)
                        except Exception:
                            print("address info was not matched")
                            driver.quit()
                            # time.sleep(random.randrange(60, 180, 1))
                            time.sleep(random.randrange(15, 30, 1))
                            # driver = get_browser('46.4.73.88:2000')
                            driver = get_browser('69.30.227.194:2000')

                if add_temp != '':
                    add = add_temp
                    break
        new_add_list.append(add)
    try:
        driver.quit()
    except Exception:
        print("browser不正常關閉")

    return new_add_list


# 由地址中擷取city以及area
# 去除字串中的不必要資訊(空格, 數字, 台灣)
def get_ct(add):
    import re
    if add is None:
        add = ''
    # 去除字串中的空格及台灣字樣
    add = add.replace(' ', '').replace('台灣', '').replace('臺灣', '').replace(',', '')
    # 去除數字(避免郵遞區號)
    add_nd = re.sub(r'[0-9]+', '', add)
    # 去除英文與數字
    add_nd = re.sub('[a-zA-Z\d]', '', add_nd)
    # 去除標點符號
    add_nd = re.sub(r'[^\w\s]','', add_nd)
    # 判斷town
    if '縣' in add:
        b = add_nd.split("縣")
        if len(b[0]) > 2:
            b[0] = b[0][:2]
            b[1] = b[0][:-2]
        getCity = b[0] + "縣"
        parsetown = re.match(r"(.*?市){0,1}(.*?鎮){0,1}(.*?鄉){0,1}", b[1])
    elif '市' in add:
        b = add_nd.split("市")
        if len(b[0]) > 2:
            b[0] = b[0][:2]
            b[1] = b[0][:-2]
        getCity = b[0] + "市"
        parsetown = re.search(r"(.*?市){0,1}(.*?區){0,1}", b[1])
    else:
        parsetown = re.match(r"(.*?市){0,1}(.*?鎮){0,1}", add)
        getCity = ''

    gettown = parsetown.group()
    if gettown == '臺東市':
        gettown = gettown.replace('臺', '台')
    
    getCity = getCity.replace('臺', '台')
    
    
    if getCity =='' or len(getCity) > 3:
        getCity = add_nd[:2]
    
    
    return getCity, gettown


# 判斷地址：縣市與鄉鎮
cities = rms_db("select name from city")['name'].tolist()
towns = rms_db("select name from areas")['name'].tolist()


# 檢查縣市以及鄉鎮是否在資料表內
# 可能原始資料的鄉鎮應為city，則將town更改為city
def check_ct(city_list, town_list):
    import re
    
    def normalize_town(town):
        town = town.replace("臺", "台")
        return town if town in towns else ''

    def get_matching_city(town):
        city_query = "select city.name from areas " + \
                     "left join city on " + \
                     "city.id = areas.city_id " + \
                     "where areas.name='" + str(town) + "'"
        matching_cities = rms_db(city_query)['name']
        return matching_cities[0] if len(matching_cities) == 1 else None

    for i in range(len(city_list)):
        if len(city_list[i]) < 3:
            if city_list[i] + '市' in cities:
                city_list[i] = city_list[i] + '市'
            else:
                city_list[i] = city_list[i] + '縣'
        city_list[i] = city_list[i] if city_list[i] in cities else ''
        town_list[i] = town_list[i] if town_list[i] else ''

        if city_list[i] not in cities:
            if town_list[i] == '' and city_list[i] in towns:
                town_list[i] = city_list[i]
            elif town_list[i] not in towns:
                town_list[i] = normalize_town(town_list[i])
                if town_list[i] == '':
                    city_list[i] = ''
            else:
                city_list[i] = ''

        if town_list[i] != '':
            city_temp = get_matching_city(town_list[i])
            if city_temp:
                city_list[i] = city_temp
            else:
                print('Not matched city')

        town_list[i] = normalize_town(town_list[i])

    return city_list, town_list

# 字串判斷相似性
# 去除空白以及數字，提升名稱相似度
def string_similar(s1, s2):
    import difflib
    import re
    s1 = re.sub(r'[0-9]+', '', s1).replace(' ', '')
    s2 = re.sub(r'[0-9]+', '', s2).replace(' ', '')
    return difflib.SequenceMatcher(None, s1, s2).quick_ratio()


# 判斷列表中資料是否重複，1.檢查自身重複、2.檢查與過往資料是否重複
# 判斷依據：名稱、位置(city)、開始時間、結束時間
# 回傳未重複資料及被移除資料
def drop_repeated_data(data, prev_data):
    import pandas as pd
    # 刪除自身重複
    data = data.drop_duplicates(subset=['name', 'city', 'area', 'start_date', 'end_date'], keep='first').reset_index(drop=True)  # noqa
    # 刪除與過往
    data_temp = data.copy()
    temp_1 = pd.DataFrame()
    temp_2 = pd.DataFrame()
    for i in range(len(data)):
        for j in range(len(prev_data)):
            if prev_data['city'][j] is None:
                prev_data.loc[j, ['city']] = ''
            # 確認相似性
            similar_prob = string_similar(data['name'][i], prev_data['name'][j])  # noqa
            if similar_prob >= 0.7:
                print(data['name'][i], prev_data['name'][j])
                print('prob:', similar_prob)
                # 判斷位置、起始時間、結束時間都相同
                if (data['city'][i] == prev_data['city'][j]) and (data['start_date'][i] == prev_data['start_date'][j]) and (data['end_date'][i] == prev_data['end_date'][j]):  # noqa
                    try:
                        data_temp = data_temp.drop([i])
                        print("drop data ", data['name'][i], prev_data['name'][j])     # noqa
                        temp_1 = pd.DataFrame({'prob:': [similar_prob],
                                               'now_name': [data['name'][i]],          # noqa
                                               'prev_name': [prev_data['name'][j]],    # noqa
                                               'location': [data['city'][i]],          # noqa
                                               'start_date': [data['start_date'][i]],  # noqa
                                               'end_date': [data['end_date'][i]]})     # noqa
                        temp_2 = temp_2.append(temp_1)
                    except Exception:
                        print("data not found")
    data_temp = data_temp.reset_index(drop=True)

    return data_temp, temp_2


def explode_date(data):
    import pandas as pd
    # 展開start_date到end_date
    data['date'] = data.apply(
        lambda x: pd.date_range(start=x['start_date'],
                                end=x['end_date']), axis=1)
    # 拆分成單行
    data = data.explode('date')
    data['date'] = pd.to_datetime(
        data['date'], format='%Y-%m-%d').dt.date
    data = data.reset_index(drop=True)
    # 調整格式
    data = data[[
        'name', 'date', 'category', 'importance', 'keywords', 'correlation',
        'city_id', 'area_id', 'address', 'start_date', 'end_date',
        'calendar_id', 'event_id', 'resource', 'created_date']]
    return data

def mapping_address(df):
    # 去除字串中的空格及台灣字樣
    df['address'] = df['address'].replace(' ', '')
    # 根據地址取得城市與區域
    df[['city', 'area']] = df['address'].apply(get_ct).apply(pd.Series)
    # 檢查城市與區域是否在資料表中，若無則回傳''
    df['city'], df['area'] = check_ct(df['city'], df['area'])
    # 讀取已有地址清單
    address_list = pd.read_csv('address_list.csv')
    df = pd.merge(df, address_list[['city_name', 'area_name', 'address']],
                  how='left', on='address')
    # 若原本city與area無值情況，根據清單更新資料
    df['city'] = df['city'].mask(
                  (df['city'].isna()), df['city_name'])
    df['area'] = df['area'].mask(
                  (df['area'].isna()), df['area_name'])
    df = df.drop(['city_name', 'area_name'], axis=1)
    # 資料表無法用np.nan寫入
    df = df.replace(np.nan, None)

    return df


def insert_data(df):
    from connectgoogleapi import add_event, get_calendar
    from act_category import get_keywords_and_category
    import os
    import pymysql
    import pymysql.cursors
    from dotenv import load_dotenv
    load_dotenv()
    # calendar connect
    service = get_calendar("PMS_account/token.json", "PMS_account/pmscalendar.json")  # noqa
    city_list = rms_db("select id, name from city")
    town_list = rms_db("select id, city_id, name from areas")
    calendar_list = rms_db("select * from calendars")
    calendar_list['city'] = calendar_list['name'].str.split("活動-").str.get(1)
    for i in range(len(df)):
        # 若有city, 則判斷是否有在calendar清單, 並判斷city_id
        if df['city'][i] is not None or df['city'][i] != '':
            try:
                df.loc[i, ['city_id']] = int(city_list[city_list['name'] == df['city'][i]]['id'])  # noqa
                if df['city'][i][:2] in calendar_list['city'].to_list():
                    df.loc[i, ['calendar_id']] = int(calendar_list[calendar_list['city'] == df['city'][i][:2]]['id'])  # noqa
                # 東部
                elif df['city_id'][i] == 17 or df['city_id'][i] == 18 or df['city_id'][i] == 19:  # noqa
                    df.loc[i, ['calendar_id']] = 9
            except Exception:
                print("Not matched calendar")
        # 若有area, 則判斷area_id
        if df['area'][i] is not None and df['area'][i] != '':
            try:
                df.loc[i, ['area_id']] = int(town_list[(town_list['name'] == df['area'][i]) & (town_list['city_id'] == df['city_id'][i])]['id'])  # noqa
            except Exception:
                print("Not matched")

    # 避免結束時間小於開始時間
    df.loc[df['end_date'] < df['start_date'], 'end_date'] = df['start_date']
    # 類別分類
    df = get_keywords_and_category(df)
    df_part = df[[
        'name', 'category', 'importance', 'keywords', 'correlation', 'city_id',
        'area_id', 'address', 'start_date', 'end_date', 'calendar_id',
        'event_id', 'resource', 'created_date', 'city', 'area']]

    prev_data = rms_db("select activities.name, activities.start_date, " +
                       "activities.end_date, city.name as city," +
                       "areas.name as area from `activities` " +
                       "left join `city` on activities.city_id = city.id " +
                       "left join `areas` on activities.area_id = areas.id")

    # 刪除重複資料
    data, drop_data = drop_repeated_data(
        df_part, prev_data.drop_duplicates().reset_index(drop=True))
    # 寫入行事曆
    for i in range(len(data)):
        if data['calendar_id'][i] is not None:
            calendar_id = calendar_list[calendar_list['id'] == data['calendar_id'][i]]['calendar_id'].values[0]  # noqa
            try:
                data['start_date'][i] = data['start_date'][i].strftime('%Y-%m-%d')  # noqa
                data['end_date'][i] = data['end_date'][i].strftime('%Y-%m-%d')  # noqa
                event_id = add_event(data.iloc[i], calendar_id, importance=0)
                data['event_id'][i] = event_id
            except Exception as e:
                print(e)

    # 展開至天並調整格式
    data = explode_date(data)

    # 寫入資料庫
    db = pymysql.connect(host=os.getenv('DB_HOST'), port=3306,
                         user=os.getenv('DB_USERNAME'),
                         passwd=os.getenv('DB_PASSWORD'),
                         db=os.getenv('DB_NAME'), charset='utf8')
    cursor = db.cursor()

    sql = ("INSERT  INTO `activities` (`name`, `date`, `category`, " +
           "`importance`, `keywords`, `correlation`, `city_id`, `area_id`," +
           "`address`, `start_date`, `end_date`, `calendar_id`, `event_id`," +
           "`resource`, `created_date`)VALUES " +
           "(% s,% s,% s,% s,% s,% s,% s,% s,% s,% s,% s,% s,% s,% s,% s)")
    cursor.executemany(sql, data.values.tolist())
    db.commit()
    db.close()
