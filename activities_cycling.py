import pandas as pd
import datetime as dt
from datetime import datetime
import re
import random
import time
import sys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from act_clean import get_add, get_ct, check_ct
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
URL = "https://cycling.biji.co/?q=competition&act=list_item&lang=zhTW&keyword=&sid=1304863593"  # noqa
for retry in range(3):
    try:
        driver.get(URL)
        time.sleep(random.randrange(3, 5, 1))
        try:
            driver.find_element(By.CLASS_NAME, 'close-btn.clz_filter').click()
        except Exception:
            print('無選單遮擋')
        finally:
            run_name = driver.find_elements(By.CLASS_NAME, 'competition-name')
            run_city = driver.find_elements(By.CLASS_NAME, 'competition-place')
    except Exception:
        print('網頁載入失敗')
    else:
        if len(run_name) != 0:
            break


# 列出所有url清單
run_url_list = pd.DataFrame()
p1 = re.compile(r'["](.*?)["]', re.S)
for name_element, city_element in zip(run_name, run_city):
    try:
        run_name = name_element.text
        run_location = city_element.text
        run_url = ('https://cycling.biji.co' +
                   re.findall(p1, name_element.get_attribute('innerHTML'))[0].replace('amp;', '')) # noqa
    except Exception:
        print('no url')
    else:
        # run_url_list.append(run_url)
        run_list_temp = pd.DataFrame({'name': [run_name],  # noqa
                                      'city': [run_location],  # noqa
                                      'url': [run_url]})
        run_url_list = pd.concat([run_url_list, run_list_temp]).reset_index(drop=True)  # noqa

# 根據url清單爬取頁面
for item in range(len(run_url_list)):
    run_list_temp = pd.DataFrame()
    time.sleep(random.randrange(3, 5, 1))
    # 網頁阻擋，retry3次
    for retry in range(3):
        try:
            driver.get(run_url_list['url'][item])
            run_detail = driver.find_elements(By.CLASS_NAME, 'data-content') # noqa
            # 廣告阻擋, 重新載入頁面, 最多3次
            j = 0
            while run_detail == [] and j < 3:
                driver.refresh()
                time.sleep(random.randrange(3, 5, 1))
                run_detail = driver.find_elements(By.CLASS_NAME, 'data-content') # noqa
                j += 1
            try:  # 取得活動名稱、地點、以及時間
                for j in range(5):
                     if driver.find_elements(By.CLASS_NAME, 'data-title')[j].text == '地點':  # noqa
                        ad_temp = run_detail[j].text.replace("查看地圖", "")
                        ad_temp = ad_temp.replace('（', '(').replace('）', ')')
                        location = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]|\\【.*?】", '', ad_temp)  # noqa
                        try:
                            address = re.findall(r'\(([^)]+)', ad_temp)[0]
                        except Exception:
                            address = ''
                        break
            except Exception:
                address = ''
                location = run_url_list['city'][item]
            run_list_temp = pd.DataFrame({'name': [driver.find_element(By.CLASS_NAME, 'comp-title').text],  # noqa
                                          'start_date': [dt.datetime.strptime(run_detail[0].text[:10], "%Y/%m/%d").date()],  # noqa
                                          'end_date': [dt.datetime.strptime(run_detail[0].text[-10:], "%Y/%m/%d").date()],  # noqa
                                          'location': [location.replace((location.split(' ')[0]+' '), '')],  # noqa
                                          'address': [address],
                                          'Region': [location.split(' ')[0]],
                                          'Town': ['']})
            run_list = pd.concat([run_list, run_list_temp]).reset_index(drop=True)  # noqa
        except Exception:
            print("失敗次數： ", retry+1)
            driver.quit()
            time.sleep(random.randrange(10, 15, 1))
            driver = get_browser(proxy_ip)
        else:
            if run_list_temp.empty is False:
                break
try:
    driver.quit()
except Exception:
    print("browser不正常關閉")

# 資料格式調整
df = run_list.copy()
# run_list_t['area'] = None
df["new_add"] = None
df['category'] = None
df['importance'] = None
df['correlation'] = None
df['city_id'] = None
df['area_id'] = None
df['calendar_id'] = None
df['event_id'] = None
df['resource'] = '自行車筆記'
df['created_date'] = today
df['city'], df['area'] = check_ct(df['Region'], df['Town'])
for i in range(len(df)):
    # 地址處理
    add = df['address'][i]  # 地址
    city = df['Region'][i]  # 縣市
    area = df['Town'][i]  # 行政區
    location = df['location'][i]  # 縣市+行政區
    # 以Add為主, 判斷縣市與行政區
    getCity, gettown = check_ct([get_ct(add)[0]], [get_ct(add)[1]])
    # 若為空, 則以location判斷
    if gettown == [''] and add is not None:
        getCity, gettown = check_ct([get_ct(location)[0]], [get_ct(location)[1]])  # noqa
        # 仍為空, 且location為空或為全國
        if gettown == [''] and (location == '' or location == '全國'):
            getCity, gettown = [city], [area]
            df.loc[i, ["new_add"]] = city + area
        # 仍為空, 且location不為空, 則用location搜尋新地址
        else:
            getadd = get_add([location])[0]
            getCity, gettown = check_ct([get_ct(getadd)[0]], [get_ct(getadd)[1]])  # noqa
            if gettown == ['']:
                getCity, gettown = [city], [area]
                df.loc[i, ["new_add"]] = city + area
            # 不為空, 則新地址為location
            else:
                df.loc[i, ["new_add"]] = location
    # 不為空, 則新地址為Add
    else:
        df.loc[i, ["new_add"]] = add
    df.loc[i, ['city']], df.loc[i, ['area']] = getCity[0], gettown[0]

    # 若地址為空白
    if df["new_add"][i] == '' or df["new_add"][i] is None:
        if location != '' and location is not None:
            df.loc[i, ["new_add"]] = location
        elif add != '' and add is not None:
            df.loc[i, ["new_add"]] = add
        else:
            df.loc[i, ["new_add"]] = city + area

df['address'] = df['new_add']
insert_data(df)
