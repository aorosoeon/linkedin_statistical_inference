import login_info
import urllib.parse
import csv
from time import sleep
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

#here is the sequence: main.py, updating_counter.py, checking_invites.py, checking_accepts.py, removing_old_invite_requests.py
#this file runs shortly after checking_invites.py. it puts people ids from linkedin links who accepted my invitation into a csv so in the end of experiment we have this information (which is fundamental for the experiment, you need to know conversion rates)

#setting up selenium
options = Options()
options.add_argument("--headless")
#options.add_argument("--start-maximized") #probably not the right choice
#options.add_argument("--no-sandbox") #check if this safe
service = Service(executable_path="/usr/bin/chromedriver") #creating Service object for handling the browser driver
browser = webdriver.Chrome(options=options, service=service) #creating a new instance of chromedriver
browser.set_window_size(1400, 900) #raspberry specific - didn't need to have this line on mac. mac opens the window in a horizontal mode by default which makes html work how it's supposed to. raspberry however opens those windows in a strange vertical format which messes html big time. this line ensures that the window will be opened in the right format

url = "http://linkedin.com/" #our base url to pull up the first window
url_connections = "https://www.linkedin.com/mynetwork/invite-connect/connections/" #page with connections, on it we can see who accepted our invites (those people became connections)

def get_initial_window(second_url): #slightly modified version of this function from main.py
    browser.get(url) #opens just standard linkedin page
    sleep(3) #wait to make sure that it's somewhat loaded, we don't need to load it completely
    browser.add_cookie({"name": login_info.cookie_name, "value": login_info.cookie_value}) #old comment: you might need to change cookie a couple of times during the half year. new comment: inserting cookies, basically a login
    sleep(1)
    browser.get(second_url) #since it accepts an argument, this page will be opened. in our case it will be url_invites
    sleep(10)

def accepts_checker():
    list_of_links = [] #empty list for links from linkedin
    get_initial_window(url_connections) #pulling up connections page
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))) #makes sure that it's loaded
    con_linkedin_links = [ln for ln in browser.find_elements(By.TAG_NAME, "a") if "/in/" in ln.get_attribute("href")] #pulls all the WebElements with links which lead to profiles
    for link in con_linkedin_links: #looping through the list of WebElements
        list_of_links.append(link.get_attribute("href")) #pulling specifically links text
        list_of_links.append(urllib.parse.unquote(link.get_attribute("href"))) #adds formated versions of them
    sleep(2) #this was probably for testing or smth, but I'm not going to remove it
    list_of_links = list(dict.fromkeys(list_of_links)) #removing duplicates

    ids_from_linkedin = [] #now we need to extract ids specifically ("https://linkedin.com/in/mark-hvylyovyi" -> "mark-hvylyovyi")
    for link in list_of_links: #looping through the list
        if link[-1] == "/": #if the last character is "/", we remove it (sometimes it is, sometimes it's not)
            link = link[:-1] #removing it in place
        link_from_linkedin_parts = link.split('/') #splitting each string into parts with "/" as a separator
        persons_id_from_linkedin = link_from_linkedin_parts[-1] #choosing specifically the last part
        ids_from_linkedin.append(persons_id_from_linkedin) #adding the new id to the new list

    sleep(2) #this was probably for testing or smth, but I'm not going to remove it
    browser.quit() #exiting the browser, we don't need it anymore, since all of the links we pulled are right here

    #putting the ids we pulled into csv
    with open("accepts_ids_from_linkedin.csv", "a", newline='') as file: #opening access to csv, append mode to not mess up previous records accidentally
        writer = csv.writer(file) #creating writer object
        for id in ids_from_linkedin: #looping through ids list
            writer.writerow([id, dt.now().strftime('%d-%m-%Y')]) #appending each id (example: "mark-hvylyovyi") in a new row

if __name__ == '__main__':
    accepts_checker()