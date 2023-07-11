import gmail
import scrapers
import credentials_manager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import sys
import os
import csv
import json
import getopt
import re
import logging

VERBOSE = False
SCREENSHOT = False
ACTIVE_PLATFORMS = {"twitter": False, "deviantart": False, "pixiv": False, "imgur": False}
USE_GMAIL = False
USE_URL = False
working_dir = os.path.dirname(__file__)
relative_path_to_archive = "Archive"
path_to_archive = os.path.join(working_dir, relative_path_to_archive)


# Identify if a string appears to be a valid URLs.
def looksLikeAURL(string):
    regex = r"(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
    if re.search(regex, string) is not None:
        return True
    else:
        return False


def sanitizeEmailBody(emailBody):
    # Identify all URLs in a provided string.
    # Return a list of all URLs found.
    regex = r"(https?://[^\s]+)"
    urls = re.findall(regex, emailBody)
    # Remove empty strings from list of URLs.
    urls = [s for s in urls if s]
    return urls


def whichPlatformIsUrl(url):
    # Identify which scraper to use for this URL.
    regexTwitter = r"(https?://[^\s]*twitter.com[^\s]*)" # Works for https://www.twitter.com and https://twitter.com
    regexShortTwitter = r"(https?://t.co[^\s]+)"
    regexDeviantart = r"(https?://[^\s]+deviantart.com[^\s]*)"
    
    if re.match(regexTwitter, url) is not None:
        return "twitter"
    elif re.match(regexShortTwitter, url) is not None:
        return "twitter"
    elif re.match(regexDeviantart, url) is not None:
        return "deviantart"
    else:
        return None


# Checks the archive for a post matching the provided URL.
def isThisPostArchived(url):
    author_name = url.replace("https://", "").split("/")[1]
    path_to_author_archive = os.path.join(path_to_archive, ("@" + author_name))
    if os.path.exists(path_to_author_archive):
        for directory_name in os.listdir(path_to_author_archive):
            directorypath = os.path.join(path_to_author_archive, directory_name)
            for file_name in os.listdir(directorypath):
                filepath = os.path.join(directorypath, file_name)
                if os.path.isfile(filepath):
                    if "metadata.json" in file_name:
                        json_file = open(filepath)
                        post_metadata = json.load(json_file)
                        if post_metadata["url"] == url:
                            return True
    else:
        return False
    return False 

   
#def scrapeFromDeviantart: 
    # Use the DeviantArt Scraper.


def main(argv):
    opts, args = getopt.getopt(argv,"hu:f:gp:v:s",["help","url=","file=","gmail","postlimit=","verbosity=","screenshot"])
    urls = []
    USE_URL = False
    USE_GMAIL = False
    USE_CSV = False
    FILEPATH = ""
    POST_LIMIT = -1
    POSTS_VIEWED = 0
    VERBOSE = False
    SCREENSHOT = False
    post_limit_reached = False
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            # Print out the help text.
            print('HELP TEXT:')
            print('  __main__.py -u <URL to media>    (overrides Gmail integration)')
            print('  __main__.py -f <path to file>    (overrides Gmail integration)')
            print('  __main__.py -g      (engages Gmail integration)')
            print('  __main__.py -p <Post limit>')
            print('  __main__.py -v      (sets the verbosity of the logs printed to console)')
            print('  __main__.py -s      (collects screenshots of posts)')
            # Exit the Gargle Scraper.
            sys.exit()
        
        elif opt in ('-u', '--url'):
            USE_URL = True
            # Pass in the URL from the arguement.
            urls.append(arg)
        
        elif opt in ('-g', '--gmail'):
            USE_GMAIL = True
        
        elif opt in ('-f', '--file'):
            USE_CSV = True
            if os.path.exists(arg):
                FILEPATH = arg
            else:
                print("The given file cannot be found!")
                sys.exit()
        
        elif opt in ('-p', '--postlimit'):
            POST_LIMIT = int(arg)
        
        elif opt in ('-v', '--verbose'):
            VERBOSE = arg.lower()
            if VERBOSE not in ("debug", "info", "warning", "error", "critical"):
                print("The given logging level '" + arg + "' is not valid. Please select one of the following options:")
                print("    DEBUG, INFO, WARNING, ERROR, CRITICAL")
                # Exit the Gargle Scraper.
                sys.exit()
        
        elif opt in ('-s', '--screenshot'):
            SCREENSHOT = True
    
    # Configure logging.
    # Create logger.
    # (Make sure to tell all future loggers across all modules to "GargleScraper" as below.)
    logger = logging.getLogger('GargleScraper')
    # Set log formatting.
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Create log file handler.
    log_file_handler = logging.FileHandler("GargleScraper.log", 'w', 'utf-8')
    log_file_handler.setFormatter(log_format)
    logger.addHandler(log_file_handler)
    # Set logging level.
    if VERBOSE == "debug":
        logger.setLevel('DEBUG')
    elif VERBOSE == "info":
        logger.setLevel('INFO')
    elif VERBOSE == "warning":
        logger.setLevel('WARNING')
    elif VERBOSE == "error":
        logger.setLevel('ERROR')
    elif VERBOSE == "critical":
        logger.setLevel('CRITICAL')
    else:
        logger.setLevel('WARNING')
    
    # Ingest a list of URLs to scrape.
    if USE_URL is True:
        logger.info("Scraping URL from command-line arguement...")
    elif USE_CSV is True:
        file_extension = os.path.splitext(FILEPATH)
        if file_extension[1] == ".csv":
            logger.info("Scraping URLs from a file...")
            urls = []
            with open(FILEPATH, mode='r') as csv_file:
                csv_reader = csv.reader(csv_file)
                for line in csv_reader:
                    for entry in line:
                        if looksLikeAURL(entry):
                            urls.append(entry)
        else:
            print("ERROR: Bad file type! The given file must be a CSV file!")
            sys.exit()
    elif USE_GMAIL is True:
        logger.info("Scraping emails from Gmail...")
        # Prep Gmail account.
        gmail_credentials = credentials_manager.get_gmail_credentials()
        gmail_account = gmail.GmailAccount(gmail_credentials)

        # Log in to Gmail account and get the emailed links.
        gmail_account.login()
        if gmail_account.service == None:
            sys.exit()

        # Get the IDs of all unread emails with the label: The Gargle.
        unread_message_ids = gmail_account.getUnreadMessageIds("The Gargle")

        #print(unread_message_ids[0])
        
        # For each email:
        #   Determine if that email contains a Twitter link.
        #   If so, go to that Twitter link:
        #     If the content is available, download it.
        #     If the content is not available, mark the email as Read (and flag it Red somehow).
        #   Move on to the next email.
        if not unread_message_ids:
            logger.warning("  No unread messages found!")
        else:
            #for id in unread_message_ids:
            email = gmail_account.getEmailFromMessageId(unread_message_ids[0])
            logger.info(email)
            emailBody = gmail_account.getEmailBodyFromEmail(email)
            if emailBody is not None:
                urls = sanitizeEmailBody(emailBody)
    
    if POST_LIMIT == -1:
        logger.error("Warning! Scraping without a post limit risks exceeding your daily post cap!")
    
    # Scrape the list of URLs.
    # For each URL, attempt scraping and archiving.
    for url in urls:
        if (POST_LIMIT == -1) or (POSTS_VIEWED < POST_LIMIT):
            # Determine which platform the link is for.
            platform = whichPlatformIsUrl(url)
            if platform == "twitter":
                if not isThisPostArchived(url):
                    if ACTIVE_PLATFORMS[platform] is True:
                        success, additional_posts_viewed = twitter_scraper.scrapeFromTwitter(url, SCREENSHOT)
                        POSTS_VIEWED += additional_posts_viewed
                        if success:
                            logger.info("Twitter Scraper archived the post at: " + url)
                        else:
                            logger.error("Twitter Scraper failed to archive the post at: " + url)
                    else:
                        ACTIVE_PLATFORMS[platform] = True
                        # Prep Twitter account and scraper.
                        twitter_credentials = credentials_manager.get_twitter_credentials()
                        twitter_scraper = scrapers.TwitterScraper(
                                            path_to_archive,
                                            twitter_credentials['email'],
                                            twitter_credentials['username'],
                                            twitter_credentials['password']
                                            )
                        # Open the Twitter home page.
                        twitter_scraper.load()
                        twitter_scraper.login()
                        # Scrape the Twitter post.
                        success, additional_posts_viewed = twitter_scraper.scrapeFromTwitter(url, SCREENSHOT)
                        POSTS_VIEWED += additional_posts_viewed
                        if success:
                            logger.info("Twitter Scraper archived the post at: " + url)
                        else:
                            logger.error("Twitter Scraper failed to archive the post at: " + url)
                else:
                    logger.warning("This Tweet has already been scraped and archived!")
            else:
                logger.error("This website has no associated scraper: " + url)
        else:
            post_limit_reached = True
            pass
    
    # Cleanup
    if post_limit_reached:
        logger.warning("Post limit reached! Some posts remain unscraped!")
    else:
        logger.info("Posts viewed: " + str(POSTS_VIEWED))
    if ACTIVE_PLATFORMS["twitter"] is True:
        twitter_scraper.teardown()
    
    # Exit the Gargle Scraper once the main function is complete, even if no other exit conditions are met.
    logger.info("Gargle Scraper is now closing...")
    sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])