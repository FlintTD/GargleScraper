# Welcome to the Gargle Scraper
This program spent a decade as a "project to get around to" in my head, and then Q4 2022 rolled around and Twitter appeared signifigantly less survivable than it had in all previous years.  That got me off my butt, and here we are.  An actual scraper!


## Intent
The goal of this software is to scrape many individual works of media from multiple major websites which host user-generated media.  The primary method of determining what to scrape is looking at Gmail.

Specifically, the scraper goes through all of the emails with a specific Gmail Label.  It then reads those emails for URLs, attempts to navigate to that URL, uses the appropriate Selenium-driven website scraper, and finally stores the scraped media in a logical directory structure.


## Description
The Gargle Scaper is a program which runs locally on a computer.  It was made entirely in Python.  It was coded with the expectation of running in a non-virtualized Windows 10 environment, and serving a single user.


## Getting Started
Firstly, you will need to download **Git**.  Then download this program from **GitHub** using Git.

This program runs on **Python 3**, so you will need to download and install Python 3.

It is best practice to create a Python virtual environment to run this program in.  I use **venv** because it is convenient.

Python virtual environment or not, you will need to download the required Python packages using the command: ```python pip install requirements.txt```

In order to get this program up and running, you will need to install Google Chrome onto your computer, and also download the appropriate version of [Chromedriver](https://chromedriver.chromium.org/downloads).  The appropriate version of Chromedriver is whichever version matches the version of Chrome you have installed.  When you download *chromedriver.exe*, put it in the directory: *GargleScraper/*.

Lastly, you will need to provide the Gargle Scraper with a bunch of login information.  That information will live in the *GargleScraper/Credentials* directory.


### The information you need is:
- The email, username, and password of a functioning Twitter account (if you are scraping Twitter).  These must be stored in the file: *twitter_credentials.txt*
- A User Access Token (UAT) for a working Gmail account.  This will be generated for you by this program, and stored in the file: *gmail_token.json*
- A set of Google secrets for the Google account associated with the above Gmail account.  The "secrets" referred to here are also known as "credentials" and "Client IDs".  They must be downloaded, and stored as a file named: *google_secrets.json*

### How to Provide Google Secrets
This is the most complicated part of setting up this project.  If you do not intend to use the Gmail-related features of the Gargle Scraper, you do not need to set up these secrets.

**Please do not post your Google Secrets or OAuth Client IDs anywhere, especially in online forums or social media!**  If you are having difficulties setting up the Gargle Scraper, do not raise a GitHub issue which includes your Google Secrets or OAuth Client IDs!

This guide will: use Google Cloud to generate Google secrets, enable the Gmail API for your personal use, and as a result permit the Gargle Scraper to use the Gmail API.

1. Sign in to the Google account associated with your desired Gmail account (using your web browser of choice).
2. Using your Google account, sign in to the [Google Cloud console](https://console.cloud.google.com/).
3. Create a **New Project** which will be used by the Gargle Scraper.  You may name this project whatever you wish, but I suggest naming it "GargleScraper" or something else descriptive.
  * If you have already created a project for use with the Gargle Scraper in the past, you may use the existing project.  Ensure that all of the following steps have been taken.
4. Once you are in your Google Cloud project's web console, open the left-hand Navigation Menu sidebar and click on **APIs and Services**.  This will take you to the APIs and Services page.
5. Once you are in the APIs and Services page, click on the **+ Enable APIs and Services** button at the top.  Then select **Gmail API** from the list of options.
6. Next, in the left-hand APIs and Services Navigation Menu sidebar, click on **OAuth consent screen**.  This will take you to the OAuth Consent Screen.
  * In the OAuth Consent Screen you can permit the Gargle Scraper access to information on your Google account.  Please note that you are only permitting the instance of the Gargle Scraper program on your computer access to your account.  The Gargle Scraper has no centralized server, and does not report anything to anyone other that you.
7. Enter an application name into the OAuth Consent Screen.  You may name this application whatever you wish, but I suggest naming it "GargleScraper" or something else descriptive.
  * This "application" is the way Google Cloud will contextualize and validate Gmail API requests coming from the Gargle Scraper.  Please note that the Gargle Scaper will not be running as "an application" in the cloud.
8. Once the application has been created, remain in the OAuth Consent Screen for the application and find the **Test users** section of the page.  Click the **+ Add Users** button, and create a new user with a name that is *the exact Gmail address* of your desired Gmail account.
  * Note: This is a "test user" because this Google Cloud application will not be "published" for public use.  That costs money!
9. Next, in the left-hand APIs and Services Navigation Menu sidebar, click on **Credentials**.  This will take you to the Credentials page.
10. Click on the **+ Create Credentials** button near the top of the page, and select **OAuth client ID** from the drop-down menu.
11. When prompted for an Application Type, select **Desktop Application**.
12. When prompted for an Application Name, provide the same name that you gave to your Google Cloud application in Step 7.
13. Click the **Create** button.  You should be redirected back to the Credentials page, and be shown a pop-up with information about the application credentials you just created.  It is safe to close this pop-up by clicking the **OK** button.
14. Remain on the Credentials page, and look for the **OAuth 2.0 Client IDs** section.  In this section, look for an OAuth Client ID with the same name as your Google Cloud application in Step 7.  Click the Download button for this OAuth Client ID (it will be one of the "Actions" buttons).
15. A pop-up will appear, bearing the name of your Google Cloud application, and displaying a Client ID and Client Secret.  In this pop-up, click the **Download JSON** button.  Save this file as "google_secrets.json", and save it to the *GargleScraper/Credentials* directory.


## Using the Gargle Scraper
Once the Gargle Scraper has been set up on your computer, it can be commanded to scrape information in various ways.  The Gargle Scraper was intended to be used via command line.

To invoke the Gargle Scaper, type navigate to the Gargle Scraper's directory and type "`python __main__.py <commands>`".

### Commands
**-h**, or **--help**: Prints some help text to the terminal.

**-u**, or **--url**: Scrapes a single post from a single URL.

**-g**, or **--gmail**: Scrapes ALL posts contained in emails with a specific Label in your Gmail server.

**-f**, or **--file**: Scrapes all URLs contained within a provided file. Currently only supports CSV files.

**-p**, or **--postlimit**: Sets a limit on how many posts the scraper can view before deactivating. This is *not* how many posts the scraper will download. For example, a Twitter thread requires navigating to multiple individual posts to scrape an single thread.

**-v**, or **--verbosity**: Tells the scraper to be more or less detailed in its logging. Log file is GargleScraper.log.

**-s**, or **--screenshot**: Tells the scraper to take a screenshot of every Tweet it scrapes. Screenshots are saved in the post's archive directory as a PNG image file.

### Unimplemented Commands
**-o**, or **--overwrite**: Modifier which will cause the scaper to overwrite any posts found to be already downloaded.