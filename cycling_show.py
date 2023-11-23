import pandas as pd
import datetime as dt
from datetime import datetime
import sys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from act_clean import get_ct, check_ct
from act_clean import get_browser, insert_data
load_dotenv()
today = dt.datetime.today().strftime("%Y-%m-%d")

try:
    proxy_ip = sys.argv[1]
except Exception:
    print("輸入代理IP：")
    sys.exit()

driver = get_browser(proxy_ip)
URL = "http://www.wheelgiant.com.tw/exhibit/exhibit.html"
driver.get(URL)

shows = pd.DataFrame()
for item in range(1, 3):
    name_temp = driver.find_elements(By.CLASS_NAME, str('s' + str(item)))
    date_temp = driver.find_elements(By.CLASS_NAME, str('s' + str(item) + 'c'))
    for show in range(len(name_temp)):
        show_temp = pd.DataFrame(
            {'name': [name_temp[show].text.replace('\n', '')],
             'start_date': [dt.datetime.strptime(
                 date_temp[show*2].text[:10], "%Y/%m/%d").date()],
             'end_date': [dt.datetime.strptime(
                 date_temp[show*2].text[-10:], "%Y/%m/%d").date()],
             'address': [date_temp[show*2-1].text.split('\n')[1]]})
        shows = pd.concat([shows, show_temp])

try:
    driver.quit()
except Exception:
    print("browser不正常關閉")

# 資料格式調整
df = shows.reset_index(drop=True)
df['category'] = None
df['importance'] = None
df['correlation'] = None
df['city_id'] = None
df['area_id'] = None
df['calendar_id'] = None
df['event_id'] = None
df['resource'] = '自行車展會'
df['created_date'] = today
df['city'], df['area'] = '', ''

for i in range(len(df)):
    city, area = get_ct(df['address'][i])
    # 未知縣市情況
    if len(city) == 2:
        try:
            getCity, gettown = check_ct([city + '市'], [area])
            if getCity != ['']:
                df.loc[i, ['city']] = getCity
                df.loc[i, ['area']] = gettown
            else:
                print(1/0)
        except Exception:
            getCity, gettown = check_ct([city + '縣'], [area])
            if getCity != ['']:
                df.loc[i, ['city']] = getCity
                df.loc[i, ['area']] = gettown
            else:
                print('Not matched city')


insert_data(df)
