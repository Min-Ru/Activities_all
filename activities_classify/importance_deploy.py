from importance_classify import importance_classify
import pandas as pd
import os
import sys
import pymysql
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()


# 讀取/寫入資料庫
def db_operate(sql, db_type, operate_type, df):
    if db_type == "rms":
        db = pymysql.connect(host=os.getenv('DB_HOST'), port=3306,
                             user=os.getenv('DB_USERNAME'),
                             passwd=os.getenv('DB_PASSWORD'),
                             db=os.getenv('DB_NAME'), charset='utf8')
    cursor = db.cursor()
    if operate_type == "search":
        cursor.execute(sql)
        result = cursor.fetchall()
        col_names = [name[0] for name in cursor.description]
        result_pd = pd.DataFrame(list(result), columns=col_names)
        db.close()
        return result_pd
    else:
        cursor.executemany(sql, df.values.tolist())
        db.commit()
        db.close()


# 取得已驗證重要度之日期
try:
    date = sys.argv[1]
except Exception:
    print("輸入日期：")
    sys.exit()


# 撈取檔案
all_data = db_operate("select * from activities", 'rms', 'search', None)
prev_data = all_data[
    all_data['created_date'] <= datetime.strptime(date, '%Y-%m-%d').date()]
new_data = all_data[all_data['importance'].isna()].drop('importance', axis=1)
# 定義重複欄位
features = ['name', 'city_id', 'area_id', 'address', 'start_date', 'end_date']
# 去重複後，才進行訓練
train_data = prev_data.drop_duplicates(
    subset=features)
test_data = new_data.drop_duplicates(
    subset=features).reset_index(drop=True)
# 預測重要度
test_data['importance'] = importance_classify(
    train_data, test_data, class_weights=None)

# 合併預測結果
merged_df = new_data.merge(
    test_data[['importance'] + features], on=features, how='left')
# 根據預測結果寫回資料庫
for index in range(len(merged_df)):
    sql = ("UPDATE activities SET importance = %s WHERE id = %s")
    db_operate(sql, 'rms', 'update',
               merged_df.iloc[index:index+1][['importance', 'id']])
