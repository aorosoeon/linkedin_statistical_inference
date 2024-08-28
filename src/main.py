import login_info
import gspread
import random
import re
from google.oauth2.service_account import Credentials
from time import sleep
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import JavascriptException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

#here is the sequence: main.py, updating_counter.py, checking_invites.py, checking_accepts.py, removing_old_invite_requests.py
#this is the main file which acts on my behalf and sends people connection requests with random choice of connection request with or without message (a/b test). it logs everything needed, number of connections, and shared connections included

#connecting to a google spreadsheet environment, to my workbook and sheet
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

#some variables to start with: start url, connection message, current position in the list from the counter in the sheet,
#and number of profiles to process per day
url = "http://linkedin.com/" #our base url to pull up the first window
message = "PLACEHOLDER FOR MESSAGE" #simple general message. main personalization - industry
current_position = sheet.acell("K2").value #this pulls a counter from the sheet. from this point current_position will be used by the program to look at the right rows. basically it's a simple navigation method
num_of_profiles_per_day = 19 #linkedin might have a problem with you if you send more than 20 requests per day/100 per week. to be on the safe side this application will send 19 reqests per working day resulting in 95 per week

#functions not in use order, they are in a random order and I don't plan to change this :)
def get_all_connections(browser): #not sure if inserting browser object into this function is needed but let's keep it this way
    connections = browser.find_element(By.XPATH, "//span[text()=' connections' and @class='t-black--light']") #this will pull from html the line in a profile with connections number (WebElement). examples: "500+ connections", "283 connections". using xpath here. xpath gives you smart navigation in html without the need to specify exact address of an element. linkedin changes those addresses, so you need to filter elements based on properties which are least likely to change
    connections_num = connections.find_element(By.XPATH, ".//span[@class='t-bold']") #this will pull from html the number of connections specifically (WebElement as well). examples: "500+ connections" -> "500+", "283 connections" -> "283"
    return connections_num.text #extracting the number itself from WebElement (as a string)

def find_number_in_shared_connections(text): #function which pulls the number of connections from shared connections line. example: "and 12 other mutual connections" -> 12
    match = re.search(r'\b\d{1,3}\b', text) #this line specifically uses re package to find a number from 0 to 999
    if match: #if a number is found
        return int(match.group(0)) #converting to integer
    else: #if there is no number. example: "Nora Holmes is a mutual connection"
        return None 

def get_mutual_connections(browser): #function to count all mutual connections
    mutual_connection_number = 0 #counter for mutual connections
    mutual_connection = next((span for span in browser.find_elements(By.TAG_NAME, "span") if span.get_attribute("class") == "t-normal t-black--light t-14 hoverable-link-text"), None) #finds WebElement with this line "Derek Derekson, Nora Holmes, and 12 other mutual connections"
    if mutual_connection: #if is here because there might be no mutual connections and in such case there is no such html element
        mutual_connection_line = mutual_connection.find_element(By.XPATH, ".//span[@class='visually-hidden']") #goes deeper into the WebElement to get specifically this "and 12 other mutual connections"
        sleep(1) # ... i don't remember why it's here, but probably there is a reason for this. don't remove
        if "is a mutual connection" in mutual_connection_line.text: #there are 4 variations of this line: "is a mutual connection", "andare mutual connections", ",, and 1 other mutual connection", ",, and 11 other mutual connections"
            mutual_connection_number += 1 #so if it's "is a mutual connection" then we know that it's just one shared mutual connection, and add this to counter
        else: #if "is a mutual connection" is absent, then we know that there are 2 names in this line
            mutual_connection_number += 2 #adding to counter
        number_from_line = find_number_in_shared_connections(mutual_connection_line.text) #using function with re to extract number or None
        if number_from_line is not None: #if number is there, we add it to counter
            mutual_connection_number += number_from_line
        return mutual_connection_number #returns integer
    else:
        return 0 #if no mutual connections, then the number which goes into spreadsheet is 0

def js_click(browser, button, seconds): #there are different ways of "clicking" something with selenium. when you click something with click() (your see your cursor moves), linkedin can intercept this click and the program will crash. it's linkedin's way of preventing bots. that's why we need to click with javascript - it's a more reliable way of clicking
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) #making sure that the page is loaded. if it's not and you will try to click, the program will crash
    browser.execute_script("arguments[0].click();", button) #clicking the element with javascript
    sleep(seconds) #wait to ensure that there is a pause between click and next action

def add_note_and_send(message): #function for adding a note and sending a request with message
    add_note_button = browser.find_element(By.XPATH, "//button[@aria-label='Add a note']") #location add a note button
    js_click(browser, add_note_button, 1) #clicking with javascript
    input_field = browser.find_element(By.XPATH, "//textarea[@id='custom-message']") #old comment: or @id="custom-message", or "//textarea[@class='ember-text-area ember-view connect-button-send-invite__custom-message mb3']". new comment: locating input field for the message
    input_field.send_keys(message) #sending our message to the input field. not sending the message to a person, but just putting it inside the box.
    sleep(1) #wait to make sure that it's there
    send_button = browser.find_element(By.XPATH, "//button[@aria-label='Send invitation']") #locating send button
    js_click(browser, send_button, 2) #click the located button via our browser instance with 2 second pause

def send_wo_note(): #function sending a connection request WITHOUT message
    send_wo_note = browser.find_element(By.XPATH, "//button[@aria-label='Send without a note']") #locating send w/o a note button in html with xpath
    js_click(browser, send_wo_note, 2) #click send_wo_note button

def get_initial_window(): #pulling up the initial window. i'm sure there are better ways to do it, but this one just works and it's enough for me
    browser.get(url) #opens just standard linkedin page
    sleep(1) #wait to make sure that it's somewhat loaded, we don't need to load it completely
    browser.add_cookie({"name": login_info.cookie_name, "value": login_info.cookie_value}) #old comment: you might need to change cookie a couple of times during the half year. new comment: inserting cookies, basically a login
    sleep(1)
    browser.get(url) #now we load it again, but the only difference is that now I'm signed in with my cookies. so instead of generic linkedin login/signup page, i see my feed
    sleep(1)
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) #waiting to make sure that it's somewhat loaded. i don't need to work with this page. body is just the highest level of html (page basically). later we will need to make sure that specific elements deep inside the page are loaded, here it's not needed.

def main(): #our main function
    #getting the initial window: linkedin, add cookies, reload, and eventually it's my news feed
    get_initial_window()

    #main loop with exception handling
    for i in range(int(current_position)+1, int(current_position)+num_of_profiles_per_day+1): #19 repeats which tied up to num_of_profiles_per_day. loop goes through 19 linkedin profiles starting from current position + 1 (current position in the sheet is marked as last_row_processed, so when the loop picks it up from last session, it needs to add 1 to it)
        try: #try except block for exception handling. who knows what linkedin will come up with next to prevent bots. they intercept clicks, change addresses and stuff like this. as of start of the experiment everything seems to work, but this is a safeguard which ensures that on a weird profile it will not crash and just move on to the next profile. some functions are built on this exception handling, for example if a person has a privacy setting which states that i can add them only with their work email, it will throw a nosuchelementfound exception and move to the next profile
            link = sheet.acell(f"A{i}").value #getting link to profile
            exceptions_list = [] #initial idea was to put exceptions in a list in case there are a couple of them, but i guess it's not possible? whenever exception occures it is caught by except statement and there is no time for another to occure? anyway, not gonna change it, it just works, though might be silly practice
            browser.get(link) #this is when our linkedin feed pulled up by get_initial_window() changes to the profile of a person
            sleep(5) #we will work with profile page closely so need to make sure that it's properly loaded
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) #double check if it's loaded. it either gives another 5 seconds to load, or if it's loaded just does nothing
            all_connections = get_all_connections(browser) #getting number of connections
            all_connections_int = int(all_connections.replace("+", "")) #the number we pulled is a string. if somebody has 500+ connections, it's marked as 500+ (wow, mindblown). int() cannot convert "500+"" string to 500, so we are removing "+"
            sheet.update_cell(i, 3, all_connections) #what we actually put in the cell is a string, example: "500+". integer we made in the previous line is needed in the next line
            if all_connections_int < 10: #here we use integer we made to see if a profile has less than 10 connections. usually such profiles are people who registered, added a couple of people to their network and forgot about it. there are 2 reasons why there is no sense in adding those people: 1. their profiles are dead, they will not accept, and it's just noise in the statistical test (the experiment itself). 2. adding somebody you don't know who has 9 connections just feels weird
                continue #so if that's the case, the loop moves on to the next profile. we will see if it was proccessed because there should be a number of connections (like 8 for example)
            sleep(1) #to not overwhelm google api. too many update_cell() in short period will result in crash. it's not necessary here, but i'm not changing stuff, it works!!!
            sheet.update_cell(i, 4, get_mutual_connections(browser)) #inserting mutual connections into spreadsheet. to bucket them conversion rates based on the number of shared connections
            option = random.choice([0, 1]) #assigning randomly 0 or 1. 0 corresponds to null hypothesis (message is better), 1 to alternative hypothesis (no message is better). so if it's 0, it sends a message, if 1, it doesn't. very unintuitive from coding perspective (we will have a column where 0 is message and 1 is no message), but very intuitive from statistics perspective (null hypothesis is 0, alternative is 1). still think it might have been a bad choice but NO. CHANGES. AT. THIS. POINT.
            sheet.update_cell(i, 5, option) #putting the option in a cell
            connect_button = next((btn for btn in browser.find_elements(By.TAG_NAME, "button") if btn.text == "Connect" and "artdeco-button--primary" in btn.get_attribute("class")), None) #very weird way to locate connect button, but it works without throwing an exception. it's a generator that searches for it and next() pulls either the button or None. the reason for such design is that people have 2 different outlines of their profiles. in some cases their connect button is on the main panel and we can simply press it without additional steps. but in other cases the connect button is hidden in the dropdown menu which opens when you press "more". so connect button might be there and it might not
            if connect_button: #if it's there, we click
                js_click(browser, connect_button, 2)
                if option == 0: #if message option, we add note and send message
                    add_note_and_send(message) #putting our message as an argument
                    continue #and the continue keyword moves us to the start of the loop so we can work with the next profile (we did everything we wanted with this profile so we can move on to the next one)
                else: #if option is 1 which means no message, we do exactly this
                    send_wo_note() #no note here, so no argument
                    continue #we're done, next profile
            else: #here we cover this weird scenario when the connect button is hidden in the dropdown
                more_button = next((btn for btn in browser.find_elements(By.TAG_NAME, "button") if btn.text == "More"), None) #location more button using generator
                js_click(browser, more_button, 2) #click
                more_connect_button = browser.find_element(By.XPATH, "//span[contains(@class, 'display-flex') and text()='Connect']") #some xpath magic here to locate connect in dropdown
                js_click(browser, more_connect_button, 2) #click
                if option == 0: #same logic as in the previous block we just needed to get to this step through another location for connect button
                    add_note_and_send(message)
                    continue
                else:
                    send_wo_note()
                    continue
        except NoSuchElementException: #exceptions! i saw 4 main exceptions during my testing stage. we put them in the list and then into corresponding cell in spreadsheet. this is for filtering results later. for example if i see nosuchelement exception it's probably email restriction, which means that the connection request wasn't send. or it might mean that this person was my connection before. i will use them with some additional checking steps to ensure that the person was added. there is a small popup "connection request sent" which sometimes pops up after sending request, however i don't use it to confirm the action, because i didn't find a reliable way for that
            exceptions_list.append("NoSuchElementException") #i tried to find (or maybe also click) an element which doesn't exist. if it is, putting it in the list
        except ElementClickInterceptedException: #linkedin found weird click and intercepted it
            exceptions_list.append("ElementClickInterceptedException") #appeding to the list
        except JavascriptException: #in this context, something similar to no such element, i see them in spreadsheet when the element wasn't found
            exceptions_list.append("JavascriptException") #appeding to the list
        except StaleElementReferenceException: #something with wait times I think, happened only once
            exceptions_list.append("StaleElementReferenceException") #appeding to the list
        finally: #keyword which makes the following code must to execute
            if not exceptions_list:
                exceptions_list.append("no") #if no exceptions, put no in the list
            exceptions_str = ','.join(map(str, exceptions_list)) #just making a nice string, but i guess it's not neccessary because it's probably not possible to have 2 exceptions at the same time. anyway don't remove this
            sheet.update_cell(i, 6, exceptions_str) #putting exception string in the cell in google spreadsheet
            sheet.update_cell(i, 7, str(dt.now())) #putting timestamp, so I know when the profile was proccessed
    #before the last changes there was a counter updater "sheet.update_cell(2, 13, int(current_position)+num_of_profiles_per_day)". However it was moved to another python file (just updater, couple of lines of code) for safer architecture. If this program fails for any fo gazilion possible reasons, on the next day the counter is updated and the new profiles will be processed. The program will not be stuck in an endless loop.
    browser.quit() #quiting the browser because we are doing everything right and with honour

if __name__ == '__main__': #safeguard - makes sure that the program will not execute if something from it is imported
    main() #basically main() runs only when called directly