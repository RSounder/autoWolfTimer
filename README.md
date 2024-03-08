# autoWolfTimer
Hey, fellow NC State student worker! Have you ever forgotten to clock out after clocking into WolfTime? Have you ever gone over the 4-hour period at a stretch without a break, and received emails from the accounts dept telling your supervisor to change the timing for you? Escape the reworks with this autoWolfTimer script.
Just make sure you have python (I used version 3.11.1), chrome (I used version 122.0.x.x, but anything beyond 115.0.x.x must work), selenium (pip install selenium), webdriver-manager (pip install webdriver-manager
), and the script should work like a charm.
1. Enter your Unity ID and password in the script (for vars username_str and password_str)
2. Invoke script "python autoWolfTimer.py <hours>.<mins>" Please note that hours.mins is compatible. mins can't be more than 59 and total time can't exceed 4 hrs.
3. That's pretty much it. I know there are some warnings, but I didn't want to fix a working code. Please raise change requests in-case you'd like to propose changes.

It is to be noted that in-case 2 factor authentication is enabled on your account, you may be prompted twice (once when clocking in and once when clocking out). Be wary of the 2FA prompts, it has a time-out. If you want, you can also use it after turning off the 2FA from mypack account settings (not recommended, but the scipt is fully automated that way). 
