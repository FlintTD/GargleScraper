import gmail
import scrapers
import credentials_manager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import sys
import getopt
import re
import logging

VERBOSE = False
SCREENSHOT = False
ACTIVE_PLATFORMS = {"twitter": False, "deviantart": False, "pixiv": False, "imgur": False}
USE_GMAIL = False
USE_URL = False

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
    
#def scrapeFromDeviantart: 
    # Use the DeviantArt Scraper.


def main(argv):
    opts, args = getopt.getopt(argv,"hu:gl:vs",["help","url=","gmail","postlimit=","verbose","screenshot"])
    urls = []
    USE_URL = False
    USE_GMAIL = False
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
            print('  __main__.py -g      (engages Gmail integration)')
            print('  __main__.py -l <Post limit>')
            print('  __main__.py -v      (enables verbose logging)')
            print('  __main__.py -s      (enables screenshots of posts)')
            # Exit the Gargle Scraper.
            sys.exit()
        
        elif opt in ('-u', '--url'):
            USE_URL = True
            # Pass in the URL from the arguement.
            urls.append(arg)
        
        elif opt in ('-g', '--gmail'):
            USE_GMAIL = True
        
        elif opt in ('-l', '--postlimit'):
            POST_LIMIT = int(arg)
        
        elif opt in ('-v', '--verbose'):
            VERBOSE = True
        
        elif opt in ('-s', '--screenshot'):
            SCREENSHOT = True
    
    # Ingest a list of URLs to scrape.
    if USE_URL is True:
        print("Scraping URL from command-line arguement...")
    elif USE_GMAIL is True:
        print("Scraping emails from Gmail...")
        # Prep Gmail account.
        gmail_credentials = credentials_manager.get_gmail_credentials()
        gmail_account = gmail.GmailAccount(gmail_credentials)

        # Log in to Gmail account and get the emailed links.
        gmail_account.login()
        if gmail_account.service == None:
            exit()

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
            print("  No unread messages found!")
        else:
            #for id in unread_message_ids:
            email = gmail_account.getEmailFromMessageId(unread_message_ids[0])
            #print(email)
            emailBody = gmail_account.getEmailBodyFromEmail(email)
            if emailBody is not None:
                urls = sanitizeEmailBody(emailBody)
    
    if POST_LIMIT == -1:
        print("Warning!  Scraping without a post limit risks exceeding your daily post cap!")
    
    # Scrape the list of URLs.
    # For each URL, attempt scraping and archiving.
    for url in urls:
        if (POST_LIMIT == -1) or (POSTS_VIEWED < POST_LIMIT):
            # Determine which platform the link is for.
            platform = whichPlatformIsUrl(url)
            if platform == "twitter":
                if ACTIVE_PLATFORMS[platform] is True:
                    success = twitter_scraper.scrapeFromTwitter(url)
                    if not success:
                        logger.log(url, "FAILED", "Twitter Scraper failed to get the post.")
                else:
                    ACTIVE_PLATFORMS[platform] = True
                    # Prep Twitter account and scraper.
                    twitter_credentials = credentials_manager.get_twitter_credentials()
                    twitter_scraper = scrapers.TwitterScraper(
                                        twitter_credentials['email'],
                                        twitter_credentials['username'],
                                        twitter_credentials['password']
                                        )
                    twitter_scraper.login()
                    # Scrape the Twitter post.
                    success, additional_posts_viewed = twitter_scraper.scrapeFromTwitter(url)
                    POSTS_VIEWED += additional_posts_viewed
                    if not success:
                        #logger.log(url, "FAILED", "Twitter Scraper failed to get the post.")
                        pass
                    
            else:
                logger.log(url, "SKIPPED", "Website has no associated scraper.")
        else:
            post_limit_reached = True
            pass
    
    # Cleanup
    if post_limit_reached:
        print("Post limit reached!  Some posts remain unscraped!")
    else:
        print("Posts viewed: " + str(POSTS_VIEWED))
    if ACTIVE_PLATFORMS["twitter"] is True:
        twitter_scraper.teardown()
    
    # Exit the Gargle Scraper once the main function is complete, even if no other exit conditions are met.
    print("  Gargle Scraper is now closing...")
    sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])