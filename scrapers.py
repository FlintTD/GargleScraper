from selenium.common.exceptions import *
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import json
from datetime import datetime

class TwitterScraper():
    
    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password
        self.working_dir = os.path.dirname(__file__)
        self.relative_path_to_archive = "Archive"
        self.path_to_archive = os.path.join(self.working_dir, self.relative_path_to_archive)
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={os.path.join(os.path.dirname(__file__), '/CustomChromeProfile')}")
        self.driver = webdriver.Chrome(
            executable_path = os.path.join(os.getcwd(), 'chromedriver'),
            options = chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        
        # Load www.twitter.com in a web browser.
        self.driver.get("http://www.twitter.com")
        # Wait until the title of the page includes the word "Twitter".
        dummy = self.wait.until(EC.title_contains("Twitter"))

    
    def login(self):
        # Check if logging in is necessary.
        homeHeading = None
        try:
            # Check if we are already logged in
            # Does the web page have an Account button?
            accountButton = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Account menu']")))
        finally:
            # If Home header isn't found, logging in is necessary.
            if accountButton is None:
                # To log in, first navigate to the Twitter login page.
                self.driver.get("http://www.twitter.com/login")
                # Wait until the Login page loads.
                unusedLogInTitle = self.wait.until(EC.title_contains("Log in"))
                # Enter the login email.
                emailTextBox = self.driver.find_element(By.NAME, "text")
                emailTextBox.send_keys(self.email)
                emailTextBox.send_keys(Keys.RETURN)
                time.sleep(0.5)
                
                try:
                    # Check to see if Twitter wants username verification.
                    #usernamePopupHeading = self.wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Enter your ")))
                    verificationTextBox = self.wait.until(EC.presence_of_element_located((By.NAME, "text")))
                    #verificationTextBox = self.driver.find_element(By.NAME, "text")
                    verificationTextBox.send_keys(self.username)
                    verificationTextBox.send_keys(Keys.RETURN)
                    print("Verified!")
                finally:
                    # Enter the login password.
                    self.wait.until(EC.visibility_of_element_located((By.NAME, "password")))
                    passwordTextBox = self.driver.find_element(By.NAME, "password")
                    passwordTextBox.send_keys(self.password)
                    passwordTextBox.send_keys(Keys.RETURN)
                
                # Wait until the Home page loads.
                unusedHomeTitle = self.wait.until(EC.title_contains("Home"))
        time.sleep(1)
    
    def teardown(self):
        self.driver.close()
    
    def goToPage(self, url):
        self.driver.get(str(url))
        self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        time.sleep(1)
    
    def analyzePageMedia(self):
        # Determine what kind of media is present on the currently-open page.
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//article[@data-testid='tweet']")))
        media = self.driver.find_element(By.XPATH, "//article[@data-testid='tweet']")
        media.screenshot("/Logs/tweet.png")
        
        # Try to find an image in the tweet.
        try:
            image = media.find_element(By.XPATH, ".//div[@aria-label='Image']")
        except NoSuchElementException:
            #print("Not an image!")
            pass
        else:
            return "image"
            
        # Try to find a video in the tweet.
        try:
            video = media.find_element(By.XPATH, ".//div[@aria-label='Embedded video']")
        except NoSuchElementException:
            #print("Not a video!")
            pass
        else:
            return "video"
        
        # Try to find text in the tweet.
        try:
            text = media.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
        except NoSuchElementException:
            #print("Not text!")
            pass
        else:
            return "text"
    
    # Retrieves the metadata of a post, when that post is already open in the webdriver.
    # Helper function for "downloadText
    def downloadMetadata(self, url, postType, datetime_obj, path_to_download_dir):
        metadata = {}
        metadata["post type"] = postType
        
        try:
            # Locate the tweet in the Twitter webpage.
            media = self.driver.find_element(By.XPATH, "//article[@data-testid='tweet']")
            
            # Retrieve the author handle.
            author_names = media.find_element(By.XPATH, ".//div[@data-testid='User-Name']")
            author = author_names.find_element(By.TAG_NAME, "a").get_attribute("href")
            metadata["author"] = author.replace("https://twitter.com/", "@")
            
            # Record the time the tweet was posted.
            metadata["date"] = datetime_obj
            
            # Record the time the tweet was scraped.
            metadata["time of scrape"] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            # Record the URL the scraper was given.
            metadata["url"] = str(url)
            
            # Try to save the metadata.
            metadata_filename = metadata["date"].strftime('%Y-%m-%d_%H-%M-%S') + "__" + "metadata" + ".json"
            metadata["date"] = metadata["date"].strftime('%Y-%m-%d, %HH:%MM:%SS')
            json_metadata = json.dumps(metadata)
            with open(os.path.join(path_to_download_dir, metadata_filename), 'w') as file:
                file.write(json_metadata)
            
            # Return a success.
            return(True)
        
        except NoSuchElementException as e:
            print("Error downloading metadata from Twitter!")
            print(e)
            # Return a failure.
            return(False)
    
    
    # Returns a Boolean, String, JSON.
    #   Boolean represents whether the download succeeded.
    #   String is the downloaded text, or None if download failed.
    #   JSON is the post metadata, or None if download failed.
    def downloadText(self, url):
        try:
            # Locate the tweet in the Twitter webpage.
            media = self.driver.find_element(By.XPATH, "//article[@data-testid='tweet']")
            # Locate the text in Twitter.
            textblock = media.find_element(By.XPATH, ".//div[@data-testid='tweetText']")  # The dot at the start of xpath means "search the children of this element".
            text = textblock.find_element(By.TAG_NAME, 'span').text
            
            # Retrieve the time the tweet was posted.
            timestring = media.find_element(By.TAG_NAME, 'time').get_attribute("datetime")
            datetime_obj = datetime.fromisoformat(timestring)
            
            # Try to download the post.
            datestring = datetime_obj.strftime('%Y-%m-%d_%H-%M-%S')
            dirname = datestring + "__" + text.replace(" ", "")[0:16]
            path_to_download_dir = os.path.join(self.path_to_archive, dirname)
            
            # If the directory already exists, the post has already been downloaded.
            if os.path.exists(path_to_download_dir):
                # Skip downloading this post.
                print("This text post from Twitter has already been downloaded!")
                return(True)
            else:
                # Create the post's archive directory.
                os.makedirs(path_to_download_dir)
                
                # Try to retrieve and save the post's metadata.
                if self.downloadMetadata(url, "text", datetime_obj, path_to_download_dir) is False:
                    return(False)
            
                # Download this post.
                filename = datestring + ".txt"
                with open(os.path.join(path_to_download_dir, filename), 'w') as file:
                    file.write(text)
                
                # Return a success.
                return(True)
        
        except NoSuchElementException as e:
            print("Error downloading text from Twitter!")
            print(e)
            # Return a failure.
            return(False)
        


"""
elem = driver.find_element(By.NAME, "q")
elem.clear()
elem.send_keys("pycon")
elem.send_keys(Keys.RETURN)
assert "No results found." not in driver.page_source
time.sleep(1)

driver.close()
"""