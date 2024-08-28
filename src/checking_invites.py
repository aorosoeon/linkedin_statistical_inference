import login_info
import gspread
import urllib.parse
from google.oauth2.service_account import Credentials
from time import sleep
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

#here is the sequence: main.py, updating_counter.py, checking_invites.py, checking_accepts.py, removing_old_invite_requests.py
#this file runs shortly after updating_counter.py to double check if the invitation was actually sent. there are many reasons for that, example: somebody has a privacy restriction which means that we can send them a connection request, only if we know their work email and type it into a box. main.py will just move on to the next profile, so in order to make sure that we will work only with those people in our a/b test whom we sent an invitation, we need to pull recent people from invetes-sent and connections section and reference them with our original target list

#standard lines to connect to the spreadsheet
scopes = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"] #think of this as levels/areas of access. for multiple reasons, 4 scopes work better than one (it's a very rough explanation, but it just connects faster with "wider" access)
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes) #creating a Credentials instance
client = gspread.authorize(creds) #authorization to google api
workbook = client.open_by_key(login_info.sheet_id) #connecting to our workbook
sheet = workbook.worksheet(login_info.sheet_name) #connecting to a specific sheet in this workbook

#setting up selenium
options = Options()
options.add_argument("--headless")
#options.add_argument("--start-maximized") #probably not the right choice
#options.add_argument("--no-sandbox") #check if this safe
service = Service(executable_path="/usr/bin/chromedriver") #creating Service object for handling the browser driver
browser = webdriver.Chrome(options=options, service=service) #creating a new instance of chromedriver
browser.set_window_size(1400, 900) #raspberry specific - didn't need to have this line on mac. mac opens the window in a horizontal mode by default which makes html work how it's supposed to. raspberry however opens those windows in a strange vertical format which messes html big time. this line ensures that the window will be opened in the right format

url = "http://linkedin.com/" #our base url to pull up the first window
url_invites = "https://www.linkedin.com/mynetwork/invitation-manager/sent/" #page with invites i sent which includes only people who haven't accepted yet (sent invites but they are not connections yet or never will be)
url_connections = "https://www.linkedin.com/mynetwork/invite-connect/connections/" #page with connections

def get_initial_window(second_url): #slightly modified version of this function from main.py
    browser.get(url) #opens just standard linkedin page
    sleep(3) #wait to make sure that it's somewhat loaded, we don't need to load it completely
    browser.add_cookie({"name": login_info.cookie_name, "value": login_info.cookie_value}) #old comment: you might need to change cookie a couple of times during the half year. new comment: inserting cookies, basically a login
    sleep(1)
    browser.get(second_url) #since it accepts an argument, this page will be opened. in our case it will be url_invites
    sleep(10)

def invites_checker():
    #this code is a bit more messy than main.py, but still works
    list_of_links = [] #list with links we will pull
    get_initial_window(url_invites) #opens invites page
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))) #makes sure that it's loaded
    inv_linkedin_links = [ln for ln in browser.find_elements(By.TAG_NAME, "a") if "linkedin.com/in/" in ln.get_attribute("href")] #pulls all the WebElements with links which lead to profiles
    for link in inv_linkedin_links: #looping through the list of WebElements
        list_of_links.append(link.get_attribute("href")) #pulling specifically links text
        list_of_links.append(urllib.parse.unquote(link.get_attribute("href"))) #this has to do something with formatting, it basically adds formated versions of them
    browser.get(url_connections) #after the last step we have all of the links from our invites section (1st page, so somewhere between 20 and 60 probably, don't remember exactly). now we load connections. the logic here is simple - what if somebody accepted my request instantly, the very minute i sent it? then they will not be in invite sent section, they will be in connections section, so we need to check it as well
    sleep(10) #waiting to load
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))) #double ckeck if the page is loaded
    con_linkedin_links = [ln for ln in browser.find_elements(By.TAG_NAME, "a") if "/in/" in ln.get_attribute("href")] #pulls all the WebElements with links which lead to profiles
    for link in con_linkedin_links: #looping through the list of WebElements
        list_of_links.append(link.get_attribute("href")) #pulling specifically links text
        list_of_links.append(urllib.parse.unquote(link.get_attribute("href"))) #add formated versions of them
    list_of_links = list(dict.fromkeys(list_of_links)) #remove duplicates

    ids_from_linkedin = [] #https://linkedin.com/in/mark-hvylyovyi and https://linkedin.com/in/mark-hvylyovyi are not the same string, but we want to treat them as same. because in some places the links we pulled look like first option and in other places it's second option. the part which makes sense to work with is "mark-hvylyovyi". the following code extracts it from the links
    for link in list_of_links: #looping through the list
        if link[-1] == "/": #if the last character is "/", we remove it (sometimes it is, sometimes it's not)
            link = link[:-1] #removing it in place
        link_from_linkedin_parts = link.split('/') #splitting each string into parts with "/" as a separator
        persons_id_from_linkedin = link_from_linkedin_parts[-1] #choosing specifically the last part, example: "https://linkedin.com/in/mark-hvylyovyi" -> "mark-hvylyovyi". this is basically our new id for a person
        ids_from_linkedin.append(persons_id_from_linkedin) #adding the new id to the new list
    
    sleep(2) #this was probably for testing or smth, but I'm not going to remove it
    browser.quit() #exiting the browser, we don't need it anymore, since all of the links we pulled are right here

    current_position = int(sheet.acell("K2").value) + 1 #pulling the counter value
    i = current_position - 19 #the counter is already updated at this point, so we need to step back (-19 profiles)
    while i < current_position:
        link_from_sheet = sheet.acell(f"A{i}").value #pulling the link from sheet
        if link_from_sheet[-1] == "/":
            link_from_sheet = link_from_sheet[:-1] #removing this last character is it's there, so they all are in the same format
        link_from_sheet_parts = link_from_sheet.split('/') #splitting each string into parts with "/" as a separator
        persons_id_from_sheet = link_from_sheet_parts[-1] #choosing specifically the last part
        if persons_id_from_sheet in ids_from_linkedin: #we just pulled the link from sheet (persons_id_from_sheet), now if it's in the list of links we pulled from linkedin we put yes in the spreadsheet (which means that we successfuly sent connection request to them)
            sheet.update_cell(i, 8, "yes") #putting yes in the sheet
            sheet.update_cell(i, 9, str(dt.now())) #putting timestamp as well
        else: #if it's not in the list, it's a no
            sheet.update_cell(i, 8, "no") #putting no in the sheet
            sheet.update_cell(i, 9, str(dt.now())) #putting timestamp as well
        sleep(5) #waiting because google api can be overwhelmed with too many calls in a short time
        i += 1 #moving to the next link, until the 19 profiles processed

if __name__ == '__main__':
    invites_checker()