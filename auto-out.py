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

# supress some minor warnings/logs/errors that I hate seeing on my console
# chrome_options = Options()
# chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # This line helps to suppress the DevTools messages

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Automate WolfTime clockin and clockout before and after a given duration.')
parser.add_argument('hours', type=str, help='Duration in hours and minutes (e.g., 3.25 for 3 hours and 25 minutes)')
args = parser.parse_args()

# Convert hours and minutes to seconds
try:
    hours_part, mins_part = args.hours.split('.') # considering in format <hours>.<mins>
    total_seconds = int(hours_part) * 3600 + int(mins_part) * 60
except ValueError:
    print("Error: Please provide the time in correct format (e.g., 3.25 for 3 hours and 25 minutes)")
    sys.exit(1)

# make sure total time cant be more than 4 hours, or else Bianca is gonna mail you again. if time is less than 2 mins, the portal is likely to throw a tantrum. 
if total_seconds < 2 * 60 or total_seconds > 4 * 3600:
    print("Error: The duration must be between 0.05 and 4.00 hours.")
    sys.exit(1)


def punch_in_or_out():

    # Setup Chrome using webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # Navigate to the login page. Now you may think that this doesn't look like 'mypack.ncsu.edu', and you'd be right. This page gets called when we try to login to mypack and since selenium is not gonna store any cache or cookies, we always need to sign in. 
    driver.get("https://portalsp.acs.ncsu.edu/Shibboleth.sso/Login?SAMLDS=1&target=ss%3Amem%3A0d279c93132bba229c8d7927f6e4910374cb4a668c6affb73803521b54774382&entityID=https%3A%2F%2Fshib.ncsu.edu%2Fidp%2Fshibboleth")

    # Wait for the username field to be present before proceeding
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )

    # Find the username and password fields and fill them out
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    username_field.send_keys(username_str)
    password_field.send_keys(password_str)

    login_button = driver.find_element(By.ID, "formSubmit")
    login_button.click()

    # After clicking login, we are greeted with a "Trust this device?" page. It doesn't matter which button we click; here we're click 'I trust' button, saying this is your device, and not some shared system.
    WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.ID, 'trust-browser-button')))
    trust_button = driver.find_element(By.ID, "trust-browser-button")
    trust_button.click()

    # the following actions are redundant as when mypack is loaded without cache/cookies it defaults to first page in available forms which is "Employee self services" for all student employees.

    ## we wont know if we are in student homepage or in employee self service page or in the other two tabs that no one uses. 
    ## it is arranged in terms of an unordered list that has divs>>spans>>ahref. we search for the ahref to be loaded and click it.

    #home_pg_sel = WebDriverWait(driver, 10).until(
    #    EC.element_to_be_clickable((By.ID, "HOMEPAGE_SELECTOR$PIMG"))
    #)
    #home_pg_sel.click()
    #
    #emp_ss_sel = WebDriverWait(driver, 10).until(
    #    EC.element_to_be_clickable((By.ID, "PTNUI_SELLP_DVW_PTNUI_LP_NAME$0"))
    #)
    #emp_ss_sel.click()
    

    # in employee self service page, search for WolfTime and click it
    WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.ID, 'win0divPTNUI_LAND_REC_GROUPLET$7')))
    wolf_time_button = driver.find_element(By.ID, "win0divPTNUI_LAND_REC_GROUPLET$7")
    wolf_time_button.click()

    # inside wolfTime, the buttons are arranged within div via iframe. So we can't just search for it by id and click.
    ## First, switch to the iframe by its ID
    try:
        WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.ID, 'win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe')))
        iframe_id = "win0groupletPTNUI_LAND_REC_GROUPLET$0_iframe"
        driver.switch_to.frame(iframe_id)

        # Now that you're within the iframe, you can find and interact with the element
        link = WebDriverWait(driver, 10).until(
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