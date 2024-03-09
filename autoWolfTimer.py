import argparse
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

username_str = "" # Unity ID
password_str = "" # Unity ID password

webDriverDelay = 1000

# If you want you can suppress some minor warnings/logs/errors you can uncomment below
# chrome_options = Options()
# chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # This line helps to suppress the DevTools messages

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Automate WolfTime clockin and clockout before and after a given duration.')
parser.add_argument('hours', type=str, help='Duration in hours and minutes (e.g., 1.5 => 1 hour and 50 minutes (default) or if --dur flag is used 1.5 => 1 hour and 30 minutes.)')
parser.add_argument('--dur', action='store_true', help='Flag to indicate if the duration is provided in total hours (e.g., 1.5 for 1 hour and 30 minutes)')
args = parser.parse_args()

# Convert hours and minutes to seconds
try:
    if args.dur:
        # If the total_hours flag is used, interpret the input as total hours
        hours_part = float(args.hours)
        mins_part = (hours_part - int(hours_part)) * 60
        total_seconds = int(hours_part) * 3600 + int(mins_part) * 60
        print("Input format: Total Hours")
    else:
        # Default to hours.minutes format
        hours_part, mins_part = args.hours.split('.') # considering in format <hours>.<mins>
        total_seconds = int(hours_part) * 3600 + int(mins_part) * 60
        print("Input format: Hours and Minutes")
except ValueError:
    print("Error: Please provide the time in correct format.")
    sys.exit(1)

# make sure the total time can't be more than 4 hours, or else Bianca is gonna mail you again. if time is less than 2 mins, the portal will likely throw a tantrum. 
if total_seconds < 2 * 60 or total_seconds > 4 * 3600:
    print("Error: The duration must be between 0.02 and 4.00 hours.")
    sys.exit(1)    

def punch_in_or_out():
    
    sys.stdout.write("\a") # plays a sound to alert us without printing a new line # works only in cmd promt(Windows)/terminal(Unix)
    
    # Setup Chrome using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # Navigate to the login page. Now you may think that this doesn't look like 'mypack.ncsu.edu', and you'd be right. This page gets called when we try to log in to mypack and since selenium is not gonna store any cache or cookies, we always need to sign in. 
    driver.get("https://portalsp.acs.ncsu.edu/Shibboleth.sso/Login?SAMLDS=1&target=ss%3Amem%3A0d279c93132bba229c8d7927f6e4910374cb4a668c6affb73803521b54774382&entityID=https%3A%2F%2Fshib.ncsu.edu%2Fidp%2Fshibboleth")

    # Wait for the username field to be present before proceeding
    WebDriverWait(driver, webDriverDelay).until(
        EC.presence_of_element_located((By.ID, "username"))
    )

    # Find the username and password fields and fill them out
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    username_field.send_keys(username_str)
    password_field.send_keys(password_str)

    login_button = driver.find_element(By.ID, "formSubmit")
    login_button.click()
    
    sys.stdout.write("\a") # plays sound without printing new line
    
    # After clicking login, we are greeted with a "Trust this device?" page. It doesn't matter which button we click; here we click the 'I trust' button, saying this is your device, not some shared system.
    WebDriverWait(driver, webDriverDelay).until(EC.presence_of_element_located((By.ID, 'trust-browser-button')))
    trust_button = driver.find_element(By.ID, "trust-browser-button")
    trust_button.click()

    # When mypack is loaded without cache/cookies it defaults to the first page in available forms which are "Employee self-services" for all student employees.

    time.sleep(12) # This is a simple workaround for the page loading issue; I hope the portal loads in 12 seconds, if the connection is slower, adjust this delay.
    wolf_time_button = driver.find_element(By.ID, "win0divPTNUI_LAND_REC_GROUPLET$7")
    driver.execute_script("arguments[0].click();", wolf_time_button)

    # Inside wolfTime, the buttons are arranged within div via iframe. So we can't just search for it by id and click.
    # First, switch to the iframe by its ID
    time.sleep(2)
    try:
        WebDriverWait(driver, webDriverDelay).until(EC.presence_of_element_located((By.ID, 'win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe')))
        iframe_id = "win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe"
        driver.switch_to.frame(iframe_id)

        # Now that you're within the iframe, you can find and interact with the element
        link = WebDriverWait(driver, webDriverDelay).until(
            EC.element_to_be_clickable((By.ID, "TL_RPTD_SFF_WK_TL_PUNCH_1"))
        )
        link.click()

    finally:
        # Once done with actions within the iframe, switch back to the default content
        driver.switch_to.default_content() 
        time.sleep(2)
        driver.quit()

punch_in_or_out()

print("WolfTime Clock In performed. Waiting for {:.2f} hours...".format(total_seconds / 3600))

time.sleep(total_seconds)

print("Time Elapsed. Performing WolfTime Clock Out...")

punch_in_or_out()

print("WolfTime Clock Out Successful")