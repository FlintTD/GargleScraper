import gmail
import scrapers
import credentials_manager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import sys
import getopt
import re


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
        return twitter_scraper.downloadText(url)
    elif mediaType == "image":
        print("Image media from Twitter is not yet supported!")
        return False
    elif mediaType == "video":
        print("Video media from Twitter is not yet supported!")
        return False
    else:
        return False
    
#def scrapeFromDeviantart: 
    # Use the DeviantArt Scraper.


def main(argv):
    opts, args = getopt.getopt(argv,"hu:g:",["help","url=","gmail="])
    
    for opt, arg in opts:
    
        if opt in ('-h', '--help'):
            # Print out the help text.
            print('__main__.py -u <URL to media>')
            print('__main__.py -g')
            
            # Exit the Gargle Scraper.
            sys.exit()
        
        elif opt in ('-u', '--url'):
            # Determine which platform the link is for.
            platform = whichPlatformIsUrl(arg)
            if platform == "twitter":
                # Start the Twitter scraper.
                twitterCredentials = credentials_manager.get_twitter_credentials()
                twitter_scraper = scrapers.TwitterScraper(
                                    twitterCredentials['email'],
                                    twitterCredentials['username'],
                                    twitterCredentials['password']
                                    )
                twitter_scraper.login()
                
                # Scrape the link.
                scrapeFromTwitter(arg, twitter_scraper)
                
                # Cleanup.
                twitter_scraper.teardown()
            else:
                # Skip archiving if the site has no scraper.
                logger.log(url, "SKIPPED", "Website has no associated scraper.")
            
            # Exit the Gargle Scraper.
            sys.exit()
        
        elif opt in ('g', '--gmail'):
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

            # Prep Twitter account and scraper.
            twitter_credentials = credentials_manager.get_twitter_credentials()
            twitter_scraper = scrapers.TwitterScraper(
                                twitter_credentials['email'],
                                twitter_credentials['username'],
                                twitter_credentials['password']
                                )
            twitter_scraper.login()

            # For each email:
            #   Determine if that email contains a Twitter link.
            #   If so, go to that Twitter link:
            #     If the content is available, download it.
            #     If the content is not available, mark the email as Read (and flag it Red somehow).
            #   Move on to the next email.
            if not unread_message_ids:
                print("No unread messages found!")
            else:
                #for id in unread_message_ids:
                email = gmail_account.getEmailFromMessageId(unread_message_ids[0])
                #print(email)
                emailBody = gmail_account.getEmailBodyFromEmail(email)
                if emailBody is not None:
                    urls = sanitizeEmailBody(emailBody)
                    for url in urls:
                        # For each URL, attempt scraping and archiving.
                        platform = whichPlatformIsUrl(url)
                        if platform == "twitter":
                            success = scrapeFromTwitter(url, twitter_scraper)
                            if not success:
                                logger.log(url, "FAILED", "Twitter Scraper failed to get the post.")
                        else:
                            logger.log(url, "SKIPPED", "Website has no associated scraper.")
            
            # Cleanup
            twitter_scraper.teardown()
        
            # Exit the Gargle Scraper.
            sys.exit()
    
    # Exit the Gargle Scraper once the main function is complete, even if no other exit conditions are met.
    sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])