'''
# activity json憑證檔 :
"activity-googlesheet.json"
# PMS大師 calendar api :
tokenfile = "PMS_account/token.json"
jsonfile = "PMS_account/pmscalendar.json"
'''

# 讀取/新增/刪除/更新google sheet
class GoogleSheetHandler:
    from google.oauth2.service_account import Credentials as sa_Credentials
    import gspread
    import pandas as pd
    def __init__(self, jsonfile, url, page):
        self.jsonfile = jsonfile
        # 定義存取的Scope(範圍)，也就是Google Sheets(試算表)
        self.scope = ['https://www.googleapis.com/auth/spreadsheets']
        # 將JSON憑證檔(檔名可自行重新命名)與Scope(範圍)傳入google-auth套件的Credentails模組(Module)，來建立憑證物件
        self.creds = sa_Credentials.from_service_account_file(
            self.jsonfile, scopes=self.scope)
        # 將憑證物件傳入gspread模組(Module)的authorize()方法(Method)進行驗證
        self.gs = gspread.authorize(self.creds)
        # 呼叫gspread模組(Module)的open_by_url()方法(Method)，傳入Google Sheets試算表的網址，來執行開啟的動作 # noqa
        self.sheet = self.gs.open_by_url(url)
        # 透過gspread模組(Module)的get_worksheet()方法(Method)來開啟
        self.worksheet = self.sheet.get_worksheet(page)

    # 讀取資料
    def get_sheet_df(self):
        records = self.worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df

    # 新增資料
    def append_value(self, new_values):
        self.worksheet.append_row(new_values)
        print("新值已成功新增到工作表。")

    # 刪除資料
    def delete_row(self, index):
        self.worksheet.delete_rows(index)
        print("資料已成功刪除。")

    # 更新資料
    def update_cell(self, row, col, new_value):
        self.worksheet.update_cell(row, col, new_value)
        print("儲存格值已成功更新。")


# calendar 取得token.json &  連線
def get_calendar(tokenfile, jsonfile):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    import os
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    if os.path.exists(tokenfile):
        creds = Credentials.from_authorized_user_file(tokenfile, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(jsonfile, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service

    except HttpError as error:
        print('An error occurred: %s' % error)


# calendar connect
service = get_calendar("PMS_account/token.json", "PMS_account/pmscalendar.json")  # noqa
# print(dir(service))


# calendar list
def get_calendar_list(calendar_name):
    import pandas as pd
    response = service.calendarList().list(
        maxResults=250,
        showDeleted=False,
        showHidden=False
        ).execute()
    calendarItems = pd.DataFrame(response.get('items'))
    calendar_list = calendarItems[calendarItems['summary'].str.contains(calendar_name)]  # noqa
    return calendar_list


# list events
def get_events(calendar_id):
    import pandas as pd
    service = get_calendar("PMS_account/token.json", "PMS_account/pmscalendar.json")  # noqa
    event_list = pd.DataFrame()
    page_token = None
    while True:
        events = service.events().list(calendarId=calendarId, pageToken=page_token).execute()  # noqa
        for event in events['items']:
            event_temp = pd.DataFrame({'summary': event['summary'],
                                       'event_id': event['id'],
                                       'calendar_id': [calendar_id],
                                       'location': event['location'],
                                       'Description': None,
                                       'start_date': event['start'],
                                       'end_date': event['end']})
            event_list = event_list.append(event_temp)
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    return event_list


# event
# 1.#a4bdfc淺藍色、2.#7ae7bf淺綠色、3.#dbadff淡粉色、4.#ff887c橘色、5.#fbd75b黃色、
# 6.#ffb878黃橘色、7.#46d6db藍綠色、8.#e1e1e1淺灰色、9.#5484ed藍色、
# 10.#51b749綠色、11.#dc2127紅色
# 新增event
def add_event(data, calendar_id, importance=0):
    if importance == 1:  # 表示重要
        color_id = '11'  # 紅色
    else:
        color_id = None  # 原本行事曆顏色
    event = {
      'summary': data['name'],  # '測試中',
      'colorId': color_id,
      'location': data['city'] + data['area'],  # '台中市新社區',
      'description': data['address'],  # '426台中市新社區協興街30號',
      'start': {
        # 'dateTime': '2022-11-01'
        'date': data['start_date']  # '2022-11-01'
      },
      'end': {
        # 'dateTime': '2022-12-31'
        'date': data['end_date']  # '2022-12-31'
      },
    }

    event = service.events().insert(calendarId=calendar_id, body=event).execute()  # noqa
    event_id = event['id']
    print('Event created: %s' % (event.get('htmlLink')))

    return event_id


# 變更event
def change_event(data, calendar_id, event_id, importance=0):
    if importance == 1:  # 表示重要
        color_id = '11'  # 紅色
    else:
        color_id = None
    event = {
      'summary': data['name'],  # '測試中',
      'colorId': color_id,  # '1',
      'location': data['city'] + data['area'],  # '台中市新社區',
      'description': data['address'],  # '426台中市新社區協興街30號',
      'start': {
        # 'dateTime': '2022-11-01'
        'date': data['start_date']  # '2022-12-31'
      },
      'end': {
        # 'dateTime': '2022-12-31'
        'date': data['end_date']  # '2022-12-31'
      },
    }
    service.events().update(
        calendarId=calendar_id, eventId=event_id, body=event).execute()

    print("finished changes")


# 刪除event
def del_event(calendar_id, event_id):
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    print("finished changes")


# 新增calendar
def add_calendar(calendar_name):
    request_body = {
        'summary': calendar_name,  # 日曆名稱
        'timeZone': 'Asia/Taipei'
    }
    response = service.calendars().insert(body=request_body).execute()
    calendar_id = response['id']

    return calendar_id


# 刪除calendar
def del_calendar(calendar_id):
    service.calendars().delete(calendarId=calendar_id).execute()

    print("finished changes")
