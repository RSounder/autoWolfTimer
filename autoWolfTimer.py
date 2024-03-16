import os
import sys
import time
import argparse
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

username_str = "" # Unity ID
password_str = "" # Unity ID password

global_delay = 10 # seconds
clockAction = "IN"

# scan if user_data dir is present and create if it's not there.
if not os.path.exists("./user_data"):
    os.makedirs("./user_data")

chrome_options = Options()

# supress all non-fatal warnings/errors
chrome_options.add_argument('--log-level=3')

# use ./user_data folder to store/retrieve user data (useful to save cache/cookies used for duo 2FA)
s = "--user-data-dir={}".format(os.path.abspath(os.path.join(os.path.curdir, "user_data")))
raw_s = r'{}'.format(s)
chrome_options.add_argument(raw_s)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Automate WolfTime clockin and clockout before and after a given duration.')
parser.add_argument('-d', action='store_true', help='Flag to indicate if the duration is provided in total hours (e.g., 1.5 for 1 hour and 30 minutes)')
parser.add_argument('-w', action='store_true', help='Flag to indicate if chrome is to be invoked in windowed mode. (eg. default is headless, -w means windowed mode for chrome)')
parser.add_argument('hours', type=str, help='Duration in hours and minutes (e.g., 1.5 => 1 hour and 50 minutes (default) or if -d flag is used 1.5 => 1 hour and 30 minutes.)')
args = parser.parse_args()

if not args.w:
    # launch chrome in headless mode
    chrome_options.add_argument("--headless=new")

# Convert hours and minutes to seconds and then to a timedelta
try:
    if args.d:
        # If total_hours flag is used, interpret the input as total hours
        hours_part = float(args.hours)
        intended_delay = timedelta(hours=hours_part)
        print("Input format: Total Hours")
    else:
        # Default to hours.minutes format
        hours_part, mins_part = map(int, args.hours.split('.')) # considering in format <hours>.<mins>
        intended_delay = timedelta(hours=hours_part, minutes=mins_part)
        print("Input format: Hours and Minutes")
except ValueError:
    print("Error: Please provide the time in correct format.")
    sys.exit(1)

# Check for the intended total time
if intended_delay.total_seconds() < 2 * 60 or intended_delay.total_seconds() > 4 * 3600:
    print("Error: The duration must be between 0.02 and 4.00 hours.")
    sys.exit(1)

def punch_in_or_out():
    
    sys.stdout.write("\a") # plays sound without printing a new line. 

    # Setup Chrome using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Navigate to the login page. Now you may think that this doesn't look like 'mypack.ncsu.edu', and you'd be right. This page gets called when we try to log in to mypack and since selenium is not gonna store any cache or cookies, we always need to sign in. 
    driver.get("https://portalsp.acs.ncsu.edu/Shibboleth.sso/Login?SAMLDS=1&target=ss%3Amem%3A0d279c93132bba229c8d7927f6e4910374cb4a668c6affb73803521b54774382&entityID=https%3A%2F%2Fshib.ncsu.edu%2Fidp%2Fshibboleth")

    # Wait for the username field to be present before proceeding
    WebDriverWait(driver, global_delay).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    
    # Find the username and password fields and fill them out
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    username_field.send_keys(username_str)
    password_field.send_keys(password_str)

    login_button = driver.find_element(By.ID, "formSubmit")
    login_button.click()
    
    # Hopefully, Duo 2FA will happen only once per Duo session (session length can be configured: https://duo.com/docs/policy#remembered-devices) as we store cookies.
    
    # After clicking login, we are greeted with a "Trust this device?" page. Ideally, we prefer not to receive 2FA prompt every time we log in. So we click the "This is my device" button.
    try:
        WebDriverWait(driver, global_delay*2).until(EC.presence_of_element_located((By.ID, 'trust-browser-button')))
        trust_button = driver.find_element(By.ID, "trust-browser-button")
        trust_button.click()
        print("2FA requested!")
    except:
        print("No 2FA requested!")
        pass # we assume that cookies we're used to login without Duo push request. If this 'try' failed for someother reason, we'll get fatal errors in the subsequent sections.
         
    # When mypack is loaded without cache/cookies it defaults to the first page in available forms which is "Employee self services" for all student employees.
    # since we don't navigate anywhere else from the context of this script, we can assume that we always will be routed to "Employee self services" page.

    time.sleep(global_delay) # This is a simple workaround for the page loading issue; I hope the portal loads in 15 seconds, if the connection is slower, adjust this delay.

    # to select wolfTime button, we cant take grouplet number as its dynamic. so we search using inner text
    # Use JavaScript to find and click the element with the text "WolfTime"
    javascript = """
    var elements = document.querySelectorAll('div.ps_box-group');
    for (var i = 0; i < elements.length; i++) {
        var span = elements[i].querySelector('span.ps-label');
        if (span && span.textContent === 'WolfTime') {
            elements[i].click(); // Click the parent div that contains the 'WolfTime' span
            break; // Exit the loop once the element is found and clicked
        }
    }
    """
    driver.execute_script(javascript)

    # Inside wolfTime, the buttons are arranged within div via iframe. So we can't just search for it by id and click.
    # First, switch to the iframe by its ID
    time.sleep(2)

    WebDriverWait(driver, global_delay*2).until(EC.presence_of_element_located((By.ID, 'win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe')))
    iframe_id = "win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe"
    driver.switch_to.frame(iframe_id)
    
    threeDots = WebDriverWait(driver, global_delay*2).until(
        EC.element_to_be_clickable((By.ID, "TL_RPTD_SFF_WK_GROUPBOX$PIMG"))
    )
    threeDots.click()

    viewFullSite = WebDriverWait(driver, global_delay*2).until(
        EC.element_to_be_clickable((By.ID, "TL_TIME_TILE_WK_VIEW_ALL"))
    )
    viewFullSite.click()

    # Once done with actions within the iframe, switch back to the default content
    driver.switch_to.default_content() 
    
    WebDriverWait(driver, global_delay*2).until(EC.presence_of_element_located((By.ID, 'TL_RPTD_TIME_PUNCH_TYPE$0')))
    
    # In full site, there's a drop down box, from which in/out is to be selected. 
    # <select id="TL_RPTD_TIME_PUNCH_TYPE$0" class="ps-dropdown" ...>
    # <option value="">&nbsp; </option>    # <option value="1">In</option>    # <option value="2" selected="selected">Out</option>
    # </select>

    dropdown_element = driver.find_element(By.ID, "TL_RPTD_TIME_PUNCH_TYPE$0")
    select = Select(dropdown_element)

    if clockAction=="IN":
        select.select_by_value("1")
    else:
        select.select_by_value("2")

    # click submit button; id="TL_WEB_CLOCK_WK_TL_SAVE_PB"
    submit = WebDriverWait(driver, global_delay).until(
        EC.element_to_be_clickable((By.ID, "TL_WEB_CLOCK_WK_TL_SAVE_PB"))
    )
    submit.click()

    # PT_CONFIRM_MSG
    WebDriverWait(driver, global_delay).until(EC.presence_of_element_located((By.ID, 'PT_CONFIRM_MSG')))

    time.sleep(2)
    driver.quit()

# Calculate the wake time
wake_time = datetime.now() + intended_delay

print("\n---------------------------------------Duration set for: {} hours and {} minutes----------------------------------------".format(intended_delay.total_seconds() // 3600, (intended_delay.total_seconds() % 3600) // 60))
clockAction = "IN"
punch_in_or_out()

print("\n---------------------------------------WolfTime Clock In performed. Waiting until {}---------------------".format(wake_time.strftime('%Y-%m-%d %H:%M:%S')))

# Loop until the current time is greater than or equal to the wake time
# We're checking for elapsed time this way as our program can run for at most 4 hrs and in this time if the activity is paused or the core is in CC6 mode (cause of laptop sleep?) 
# the time.sleep() alone wouldn't be enough to keep track of time elapsed.

while datetime.now() < wake_time:
    time.sleep(global_delay)  # Check every 'global_delay' seconds.

print("\n---------------------------------------Time Elapsed. Performing WolfTime Clock Out----------------------------------------")

clockAction = "OUT"
punch_in_or_out()

print("\n---------------------------------------WolfTime Clock Out Successful------------------------------------------------------")
