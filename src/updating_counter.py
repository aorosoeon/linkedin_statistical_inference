import login_info
import gspread
from google.oauth2.service_account import Credentials

#here is the sequence: main.py, updating_counter.py, checking_invites.py, checking_accepts.py, removing_old_invite_requests.py
#this program runs shortly after main.py to update the counter in the google spreadsheet, so main.py will work with new profiles each time

#standard lines to connect to the spreadsheet
scopes = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"] #think of this as levels/areas of access. for multiple reasons, 4 scopes work better than one (it's a very rough explanation, but it just connects faster with "wider" access)
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes) #creating a Credentials instance
client = gspread.authorize(creds) #authorization to google api
workbook = client.open_by_key(login_info.sheet_id) #connecting to our workbook
sheet = workbook.worksheet(login_info.sheet_name) #connecting to a specific sheet in this workbook

current_position = sheet.acell("K2").value #getting the current value of counter from spreadsheet
num_of_profiles_per_day = 19 #increase of that number. main processed 19 profiles, that's why we add 19

def updater():
    sheet.update_cell(2, 11, int(current_position)+num_of_profiles_per_day) #updating the cell. this whole python file essentially comes down to this line - updating the counter cell in spreadsheet. this action is in a separate file to make the infrastructure is more independent, reliable and overall bulletproof to error

if __name__ == '__main__':
    updater()