import pandas as pd
import datetime as dt
from datetime import datetime
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
URL = "http://www.k-arena.com.tw/calendar-list.php"  # noqa


for retry in range(3):
    try:
        driver.get(URL)
        time.sleep(random.randrange(3, 5, 1))
        # 取得不同年份的頁面資訊
        items = driver.find_element(By.ID, 'flag-tit').text.split('\n')
    except Exception:
        print('網頁載入失敗')
    else:
        if len(items) != 0:
            break


show_list = pd.DataFrame()
# 根據不同年份，列出活動
for item in range(1, len(items)+1):
    # 避免網頁阻擋，retry3次
    for retry in range(3):
        try:
            driver.find_element(
                By.XPATH, '//*[@id="flag-tit"]/li[' + str(item) + ']').click()
            time.sleep(random.randrange(5, 10, 1))
            shows = driver.find_elements(By.CLASS_NAME, 'cItem-sub')
            # 取得活動名稱、地點、以及時間
            for show in shows:
                list_temp = pd.DataFrame(
                    {'name': [show.text.split('\n')[3]],
                     'start_date': [show.text.split('\n')[0]],
                     'end_date': [show.text.split('\n')[2]]})
                show_list = pd.concat([show_list, list_temp]).reset_index(drop=True)  # noqa
        except Exception as e:
            print(e)
            print("失敗次數： ", retry+1)
            driver.quit()
            time.sleep(random.randrange(10, 15, 1))
            driver = get_browser(proxy_ip)
            driver.get(URL)
            time.sleep(random.randrange(3, 5, 1))
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
df['resource'] = '高雄小巨蛋'
df['created_date'] = today

# 移除包含特定文本的行
keywords = ['場館施工日', '春節', '取消', '延期']
df = df[~df['name'].str.contains('|'.join(keywords))]

# 将字符串日期转换为 datetime.date 格式
df['start_date'] = pd.to_datetime(df['start_date']).dt.date
df['end_date'] = df['start_date']

address = '81355高雄市左營區博愛二路757號'
df['address'] = address
df['city'], df['area'] = get_ct(address)[0], get_ct(address)[1]
df = df.dropna(subset=['start_date']).reset_index(drop=True)
insert_data(df)
