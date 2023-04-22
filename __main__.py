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

def scrapeFromTwitter(url, twitter_scraper):
    # Navigate to the requested page on Twitter.
    twitter_scraper.goToPage(url)
    # Determine the type of media the post contains.
    mediaType = twitter_scraper.analyzePageMedia()
    # Attempt to download the post.
    if mediaType == "text":
        print("  Text post!")
        return twitter_scraper.downloadText(url)
    elif mediaType == "image":
        print("  Image post!")
        return twitter_scraper.downloadImage(url)
    elif mediaType == "video":
        print("  Video post!")
        return twitter_scraper.downloadVideo(url)
    else:
        return False
    
#def scrapeFromDeviantart: 
    # Use the DeviantArt Scraper.


def main(argv):
    opts, args = getopt.getopt(argv,"hu:g:vs",["help","url=","gmail=","verbose","screenshot"])
    urls = []
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            # Print out the help text.
            print('__main__.py -u <URL to media>')
            print('__main__.py -g')
            # Exit the Gargle Scraper.
            sys.exit()
        
        elif opt in ('-u', '--url'):
            USE_URL = True
            # Pass in the URL from the arguement.
            urls.append(arg)
        
        elif opt in ('-g', '--gmail'):
            USE_GMAIL = True
        
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
    
    
    # Scrape the list of URLs.
    # For each URL, attempt scraping and archiving.
    for url in urls:
        # Determine which platform the link is for.
        platform = whichPlatformIsUrl(url)
        if platform == "twitter":
            if ACTIVE_PLATFORMS[platform] is True:
                success = scrapeFromTwitter(url, twitter_scraper)
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
                success = scrapeFromTwitter(url, twitter_scraper)
                if not success:
                    logger.log(url, "FAILED", "Twitter Scraper failed to get the post.")
        else:
            logger.log(url, "SKIPPED", "Website has no associated scraper.")
    
    # Cleanup
    if ACTIVE_PLATFORMS["twitter"] is True:
        twitter_scraper.teardown()
    
    # Exit the Gargle Scraper once the main function is complete, even if no other exit conditions are met.
    print("  Gargle Scraper is now closing...")
    sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])