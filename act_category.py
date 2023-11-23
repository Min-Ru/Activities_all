def get_keywords_and_category(df):
    """
    類別共計17種，主要分為藝文活動、戶外活動、展覽活動以及其他
    藝文活動分為：演唱會、音樂會、戲劇電影、文學講座、舞蹈表演、宗教慶典、節日慶典、地方慶典
    戶外活動分為：馬拉松、自行車、水上活動、山岳登山
    展覽活動分為：花卉展覽、藝術展覽、商業展覽
    output資料為未整理欄位
    需注意source為台中國家歌劇院，其keywords為標籤，若無標籤則會被分為其他
    """
    # 分類字典-for all
    category_keywords = {
        "藝文活動-演唱會": ["演唱會", "TOUR", "CONCERT", "五月天", "草東沒有派對",
                     "宇宙人", "王力宏", "盧廣仲"],
        "戶外活動-音樂節":  ["音樂節", "音樂季", "音樂祭", "搖滾台中", "搖滾臺中",
                      "MEGAPORT FESTIVAL", "樂器節"],
        "藝文活動-音樂會": ["獨奏會", "管樂節", "演奏會", "音樂會", "音樂町", "樂團"],
        "展覽活動-花卉展覽":  ["鬱金香", "蘭展", "櫻花", "雙溪荷", "繡球花", "魯冰花",
                       "賞桐", "蝶戀季", "蓮花", "蜀葵花", "新社花海", "菊展",
                       "紫薇花", "棉花季", "梅花", "海芋季", "桐花", "桃金孃",
                       "柚花", "金針花", "花毯節", "花彩節", "花季", "花卉嘉年華",
                       "花卉節", "花卉市集", "花卉博覽會", "豆梨季", "芒花季",
                       "杜鵑花", "百合花", "仙草花", "木棉花", "紫微花"],
        "展覽活動-藝術展覽": ["攝影展", "藝術節", "藝術展", "藝術季", "藝術秀",
                      "藝術巡演", "藝文季", "雙年展", "邀請展", "聯展", "聯合策展",
                      "模型展", "寫生展", "碧潭水舞", "畫展", "創作展", "陶藝展",
                      "畢業展", "書畫展", "書法展", "個展", "美術館", "畢業展",
                      "成果展", "美展", "周年展", "典藏展", "沙雕展", "巡迴展",
                      "作品展", "回顧展", "名畫展", "光雕展", "光雕秀", "光影藝術",
                      "光影季", "交流展", "台東光祭", "文學展", "工藝展", "三人展"],
        "戶外活動-馬拉松":  ["二鐵", "三鐵", "小鐵人", "鐵人賽", "鐵人三項", "鐵人兩項",
                      "田徑", "夜跑", "馬拉松", "超馬", "路跑", "越野", "跑水節",
                      "舒跑杯"],
        "戶外活動-自行車": ["騎輪節", "單車", "自行車"],
        "戶外活動-水上活動": ["衝浪", "長泳", "泳渡", "東浪", "帆船生活節"],
        "戶外活動-山岳登山": ["谷關七雄", "登山"],
        "藝文活動-戲劇電影": ["戲劇", "戲曲", "劇團", "劇場", "舞台劇", "歌劇",
                      "歌仔戲團", "電影節", "電影院", "電影放映季", "創意劇",
                      "音樂劇"],
        "藝文活動-文學講座": ["講堂", "講座", "研討會", "論壇", "演講", "課程",
                      "工作坊"],
        "藝文活動-舞蹈表演": ["舞蹈", "舞團", "歌舞展演"],
        "藝文活動-宗教慶典": ["義民祭", "媽祖", "哈瑪星濱線祭", "佛祖", "平安鹽祭",
                      "謝鹽祭", "王船祭", "天后宮", "內門宋江陣", "中元祭", "平安祭",
                      "保生文化祭"],
        "藝文活動-節日慶典": ["鹽水蜂炮", "龍舟", "燈節", "燈會", "聖誕", "燈展",
                      "端午", "跨年", "萬聖", "聖誕", "新春", "新年", "情人節",
                      "耶誕", "春節", "迎曙光", "年貨", "天燈", "元宵", "中秋",
                      "端陽"],
        "藝文活動-地方節慶": ["藝穗節", "豐年節", "豐年祭", "聯合年祭", "燈藝節",
                      "踩舞祭", "踩舞嘉年華", "蝶舞光節", "熱氣球嘉年華", "溫泉季",
                      "歲時祭儀", "新丁粄節", "菱角季", "最美星空", "魚鱻節",
                      "啤酒嘉年華", "啤酒節", "偶戲節", "海灣節", "捕魚祭", "射耳祭",
                      "夏戀嘉年華", "夏日狂歡祭", "風箏節", "風車節", "紅藜季",
                      "秋收祭", "星空季", "星光節", "花蛤季", "花火節",
                      "花火音樂嘉年華", "枇杷節", "東石海之夏", "奔羊節", "夜祭",
                      "芒果季", "芋頭季", "米干節", "竹筏季", "竹筍節", "收穫祭",
                      "地瓜季", "月食季", "文化觀光季", "文化節", "文化祭", "文化季",
                      "天燈", "天穿", "五彩祈福節", "好湯", "溫泉"],
        "展覽活動-商業展覽": ["漫畫節", "資安大會", "博覽會", "動漫節", "文博會", "展"]
        }

    # 分類字典-台中國家歌劇院
    category_keywords_ntt = {
        '藝文活動-戲劇電影': ["音樂劇", "歌劇", "劇場", "戲劇", "戲曲"],
        '藝文活動-音樂會': ["音樂"],
        '藝文活動-舞蹈表演': ['舞蹈'],
        '藝文活動-文學講座': ["講座", "課程"]
        }

    # 定義resource到category的映射，該resource只有單一類別情況
    resource_to_category_mapping = {
        "自行車筆記": "戶外活動-自行車",
        "自行車展會": "展覽活動-商業展覽",
        "跑步筆記": "戶外活動-馬拉松",
        "寬宏售票": "藝文活動-演唱會"
        }

    # 當resource是“台中國家歌劇院”時，category依據category_keywords_ntt進行分類
    def categorize_by_keywords(name):
        for k, v in category_keywords_ntt.items():
            if any(keyword in name for keyword in v):
                return k
        return "其他"

    # 取得關鍵字
    def get_keywords(df):
        # 將name的英文轉為大寫
        df['name_upper'] = df['name'].str.upper()
        # 遍歷每一行資料，查找關鍵字並添加到keywords列中
        for index, row in df.iterrows():
            event_name = row["name_upper"]
            keywords_list = []
            # 台中國家歌劇院本身已有標籤，不需要找關鍵字
            if row['resource'] not in ['台中國家歌劇院']:
                for category, keywords in category_keywords.items():
                    for keyword in keywords:
                        if keyword in event_name:
                            keywords_list.append(keyword)
                # 在DataFrame中的相應位置添加已找到的關鍵字
                df.at[index, "keywords"] = ", ".join(keywords_list)

        df = df.drop('name_upper', axis=1)
        return df

    # 根據第一個關鍵字，取得類別
    def get_category(df):
        # 遍歷每一行資料，從keywords列中提取第一個關鍵字，並確定類別並寫入category列
        for index, row in df.iterrows():
            resource = row['resource']
            # 檢查resource是否在映射字典中，如果是則將對應的類別分配給該行
            if resource in resource_to_category_mapping:
                df.at[index, "category"] = resource_to_category_mapping[resource]  # noqa
            # 如果資源不在特定的排除列表中，則處理關鍵字以確定類別
            elif resource not in ['台中國家歌劇院', '自行車筆記', '自行車展會', '跑步筆記', '寬宏售票']:
                keywords = row["keywords"].split(", ")
                # 檢查是否有找到關鍵字
                if keywords:
                    first_keyword = keywords[0]
                    # 遍歷類別和對應的關鍵字列表，以查找匹配的類別
                    for category, category_keywords_list in category_keywords.items():  # noqa
                        if first_keyword in category_keywords_list:
                            df.at[index, "category"] = category
                            break
        return df

    df = get_category(get_keywords(df))
    try:
        df.loc[df['resource'] == '台中國家歌劇院', 'category'] = df[
            df['resource'] == '台中國家歌劇院']['keywords'].apply(categorize_by_keywords)  # noqa
    except Exception:
        print("There are no keywords in the columns")
    # 將未匹配到的類別設為“其他”
    df['category'].fillna("其他", inplace=True)

    return df
