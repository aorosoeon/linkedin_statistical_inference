import login_info
import csv
from time import sleep
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
#from selenium.common.exceptions import NoSuchElementException
#from selenium.common.exceptions import ElementClickInterceptedException
#from selenium.common.exceptions import JavascriptException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

#here is the sequence: main.py, updating_counter.py, checking_invites.py, checking_accepts.py, removing_old_invite_requests.py
#this program removes old connection requests from page 7. linkedin does not allow to have more than 700 sent connection requests, so when you automatically send thousands of requests over a long period of time you need to have a program which withdraws old invitation requests. page 7 of "https://www.linkedin.com/mynetwork/invitation-manager/sent/" contains requests number 600-700 (old requests), so we clean it daily

#setting up selenium
options = Options()
options.add_argument("--headless")
#options.add_argument("--start-maximized") #probably not the right choice
#options.add_argument("--no-sandbox") #check if this safe
service = Service(executable_path="/usr/bin/chromedriver") #creating Service object for handling the browser driver
browser = webdriver.Chrome(options=options, service=service) #creating a new instance of chromedriver
browser.set_window_size(1400, 900) #raspberry specific - didn't need to have this line on mac. mac opens the window in a horizontal mode by default which makes html work how it's supposed to. raspberry however opens those windows in a strange vertical format which messes html big time. this line ensures that the window will be opened in the right format

url = "https://www.linkedin.com/mynetwork/invitation-manager/sent/" #url to invitations I sent

def get_initial_window(): #pulling up the initial window
    browser.get(url) #will probably redirect to generic linkedin welcome page
    sleep(3) #wait to make sure that it's somewhat loaded, we don't need to load it completely
    browser.add_cookie({"name": login_info.cookie_name, "value": login_info.cookie_value}) #old comment: you might need to change cookie a couple of times during the half year. new comment: inserting cookies, basically a login
    sleep(1)
    browser.get(url) #now we load it again, but the only difference is that now I'm signed in with my cookies. so instead of generic linkedin login/signup page, i see my invitations
    sleep(10) #waiting to make sure that it's loaded
    WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) #double check

def remover():
    get_initial_window()

    #clicking page number 7
    page_7_button = browser.find_element(By.XPATH, "//button[@aria-label='Page 7' and @type='button']")
    browser.execute_script("arguments[0].click();", page_7_button)
    sleep(10)

    #checking if we are on page 7
    page_7_check = browser.find_element(By.XPATH, "//button[@aria-label='Page 7' and @type='button']")
    if page_7_check.get_attribute('aria-current') == "true":

        #collecting withdraw buttons
        withdraw_buttons = [btn for btn in browser.find_elements(By.TAG_NAME, "button") if btn.get_attribute("class") == "artdeco-button artdeco-button--muted artdeco-button--3 artdeco-button--tertiary ember-view invitation-card__action-btn" and "Withdraw invitation" in btn.get_attribute("aria-label")]

        #clicking them
        for button in withdraw_buttons:
            browser.execute_script("arguments[0].click();", button)
            sleep(2)
            withdraw = browser.find_element(By.XPATH, "//button[@class='artdeco-button artdeco-button--2 artdeco-button--primary ember-view artdeco-modal__confirm-dialog-btn']")
            browser.execute_script("arguments[0].click();", withdraw)
            sleep(2)
        
        with open("remover_log.csv", "a", newline='') as file: #opening access to csv, append mode to not mess up previous records accidentally
            writer = csv.writer(file) #creating writer object
            writer.writerow([len(withdraw_buttons), dt.now().strftime('%d-%m-%Y')])

    browser.quit()

if __name__ == '__main__':
    remover()