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
import io
import shutil
import json
import markdownify
import re
import logging
import requests
import random
from datetime import datetime
from PIL import Image

logger = logging.getLogger('GargleScraper')

class DeviantartScraper():
    def __init__(self, archivepath, username, password):
        self.path_to_archive = archivepath
        self.username = username
        self.password = password
        self.working_dir = os.path.dirname(__file__)
        # Set up Chromedriver.
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={os.path.join(self.working_dir, '/CustomChromeProfile')}")
        chrome_options.add_argument("--disable-extensions")
        #chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) #This makes the "DevTools listening on ws://127.0.0.1" message go away.
        self.driver = webdriver.Chrome(
            executable_path = os.path.join(os.getcwd(), 'chromedriver'),
            options = chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
    
    
    def load(self):
        logger.info("The DeviantArt scraper is opening a browser window...")
        # Load www.deviantart.com in a web browser.
        self.driver.get("http://www.deviantart.com")
        # Wait until the title of the page includes the word "DeviantArt".
        dummy = self.wait.until(EC.title_contains("DeviantArt"))
    
    
    def mimicTyping(self, element, string):
        for char in string:
            element.send_keys(char)
            time.sleep((0.2 * random.random()))
    
    
    def login(self):
        # Check if logging in to DeviantArt is necessary.
        homeHeading = None
        try:
            # Check if we are already logged in.
            # Does the web page have a User Profile button in the top left?
            #header = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//header[@role='banner']")))
            #accountButton = header.find_element(By.XPATH, ".//a[@data-hook='user_link']")
            #accountButton = header.find_element(By.XPATH, f".//a[@data-username='{self.username}']")
            accountButton = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//a[@data-username='{self.username}']")))
        except:
            # If User Profile button isn't found, logging in to DeviantArt is necessary.
            # To log in, first navigate to the DeviantArt login page.
            self.driver.get("https://www.deviantart.com/users/login")
            # Wait until the Login page loads.
            unused_login_title = self.wait.until(EC.title_contains("Log In"))
            # Enter the login username.
            username_textbox = self.driver.find_element(By.XPATH, "//input[@name='username']")
            self.mimicTyping(username_textbox, self.username)
            time.sleep((0.5 * random.random()))
            # Enter the login password.
            password_textbox = self.driver.find_element(By.XPATH, "//input[@name='password']")
            self.mimicTyping(password_textbox, self.password)
            # Submit the form to log in.
            try:
                password_textbox.send_keys(Keys.RETURN)
                time.sleep(0.5)
            
                """
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
                """
                
                # Wait until the Home page loads.
                #input("Press Enter to continue...")
                unusedHomeTitle = self.wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Home")))
            except Exception as e:
                logger.error("The scraper has failed to log in to DeviantArt!")
                logger.error(e)
        #time.sleep(1)
    
    
    def teardown(self):
        logger.info("The DeviantArt scraper module is deactivating...")
        self.driver.close()
    
    
    def goToPage(self, url):
        logger.debug("Navigating to web page at: " + str(url))
        self.driver.get(str(url))
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@aria-label='DeviantArt - Home']")))
        #time.sleep(1)
    
    
    def goBackAPage(self):
        self.driver.back()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@aria-label='DeviantArt - Home']")))
        #time.sleep(1)
    
    
    def screenshot(self, element, dir_path, screenshot_name):
        try:
            ActionChains(self.driver).scroll_to_element(element).perform()  # focus
            location = element.location
            logger.info("Taking screenshot of element at screen coordinates: " + str(location))
            size = element.size
            self.wait.until(EC.visibility_of(element))
            png = self.driver.get_screenshot_as_png()
            im = Image.open(io.BytesIO(png))
            left = location['x']
            top = location['y'] - self.driver.execute_script('return window.pageYOffset;')
            right = left + size['width']
            bottom = top + size['height']
            im = im.crop((left, top, right, bottom))
            with open(os.path.join(dir_path, screenshot_name + ".png"), 'wb') as file:
                im.save(file, "png")
        except Exception as e:
            logger.error("Error taking screenshot of web element!")
            logger.error(e)
    
    
    def isDeviationDeleted(self):
        deleted = False
        return deleted
    
    
    def sanitizeString(self, string):
        disallowed_characters = ['#','%','&','{','}','\\','<','>','*','?','/',' ','$','!','\'','\"',':','@','+','`','|','=', '\n']
        return "".join(filter(lambda char: char not in disallowed_characters , string))
    
    
    # Generates a new directory containing the data from a Deviation.
    # Returns False, or a path to the archive directory it has created.
    def generateDeviationDirectory(self, deviation):
        # Generate download directory name.
        datestring = deviation.metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
        sanitized_id = self.sanitizeString(deviation.metadata["title"])
        dir_name = datestring + "__" + sanitized_id[0:16]
        path_to_download_dir = os.path.join(self.path_to_archive, os.path.join(deviation.metadata["author"].lower(), dir_name))
        
        # If the directory already exists, this Deviation has already been downloaded.
        if os.path.exists(path_to_download_dir):
            # Skip downloading this Deviation.
            logger.warning("  This Deviation from DeviantArt has already been downloaded!")
            return False
        else:
            # Create the post's archive directory.
            os.makedirs(path_to_download_dir)
        
        return path_to_download_dir
    
    
    def determineDeviationMediaType(self, deviation):
        try:
            art_stage = deviation.main.find_element(By.XPATH, ".//div[@data-hook='art_stage']")
            # Is it a video?
            try:
                art_stage.find_element(By.XPATH, ".//section[@data-hook='react_playable']")
            except:
                pass
            # Is it an image?
            try:
                art_stage.find_element(By.TAG_NAME, "img")
                return "image"
            except:
                # It must be text.
                return "text"
                
        except Exception as e:
            logger.error("Failed to determine Deviation type from DeviantArt!")
            logger.error(e)
            return False
    
    
    # Saves the metadata of a Deviation to a file.
    # Helper function for all "download[postType]" functions.
    # Returns a Boolean, representing whether the download succeeded.
    def downloadMetadata(self, deviation, path_to_download_dir):
        try:
            # Try to save the metadata.
            metadata_filename = self.sanitizeString(deviation.metadata["title"]) + "__" + "metadata" + ".json"
            deviation.metadata["date"] = deviation.metadata["date"].strftime('%Y-%m-%d, %HH:%MM:%SS')
            json_metadata = json.dumps(deviation.metadata)
            with open(os.path.join(path_to_download_dir, metadata_filename), 'w') as file:
                file.write(json_metadata)
            
            # Return a success.
            return(True)
        
        except NoSuchElementException as e:
            logger.error("Error downloading metadata to file!")
            logger.error(e)
            # Return a failure.
            return(False)
    
    
    # Downloads a Deviation containing only text.
    # Returns a List containing strings, one string per newline.
    def downloadText(self, deviation, dir_path, SCREENSHOT):
        try:
        # Locate the text in the Deviation.
        # There are actually two near-identical "legacy-journal" elements, one for the text body and one for the author comments.
            text_bodies = deviation.main.find_elements(By.CSS_SELECTOR, "div[class^='legacy-journal']")
            deviation_text = text_bodies[0]
            author_comments = text_bodies[1]
            
        # Scrape the Deviation's text.
        # There are multiple formats for all-text Deviations, hense the try-catch for "p" elements.
            text_list = []
            try:
                text_elements = deviation_text.find_elements(By.XPATH, "./p")
                for element in text_elements:
                    text_list.append(element.find_element(By.TAG_NAME, "span").text)
            except:
                text_list.append(deviation_text.text)
        
        # Scrape the author's comments.
            comments_list = []
            comments_list.append(author_comments.text)
            html_comment = author_comments.get_attribute('innerHTML')
            
        # Sanitize the text from the Deviation.
            text = "\n".join(text_list)
        
        # Sanitize the author's comments.
            markdown_comment = markdownify.markdownify(html_comment, heading_style="ATX")
            
            datestring = deviation.metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
            sanitized_title = self.sanitizeString(deviation.metadata["title"])
            
        # Try to save the Deviation's text.
            filename = f"{sanitized_title}__{datestring}"
            with open(os.path.join(dir_path, (filename + ".txt")), 'w', encoding="utf-8") as file:
                file.write(text)
            
        # Try to save the author comments.
            filename = f"{sanitized_title}__comments__{datestring}"
            with open(os.path.join(dir_path, (filename + ".md")), 'w', encoding="utf-8") as file:
                file.write(markdown_comment)
        
        #Try to save the Deviation's metadata.
            self.downloadMetadata(deviation, dir_path)
        
        # If the Screenshot flag is set, take a screenshot of the Deviation and author's comments as well.
            if SCREENSHOT:
                self.screenshot(deviation_text, dir_path, filename)
                self.screenshot(author_comments, dir_path, (filename + "__comments"))
        
        except NoSuchElementException as e:
            logger.error("  Error downloading text from DeviantArt!")
            logger.error(e)
            # Return a failure.
            return(False)
    
    
    def downloadDeviation(self, deviation, dir_path, SCREENSHOT):
        downloaded = False
        if deviation.metadata["post type"] == "text":
            logger.info("  Text Deviation.")
            downloaded = self.downloadText(deviation, dir_path, SCREENSHOT)
        elif deviation.metadata["post type"] == "image":
            logger.info("  Image Deviation.")
            downloaded = self.downloadImage(deviation, dir_path, SCREENSHOT)
        elif deviation.metadata["post type"] == "video":
            logger.info("  Video Deviation.")
            downloaded = self.downloadVideo(deviation, dir_path, SCREENSHOT)
        else:
            return downloaded
        
        return downloaded
        
    
    
    # Download the full data and metadata of a Deviation.
    # Returns one value:
    #     True or False boolean, indicating a successful scrape or not.
    def scrapeFromDeviantart(self, url, SCREENSHOT):
    # Navigate to the requested page on DeviantArt.
        self.goToPage(url)
        # Check to see if the Deviation has been deleted.
        if self.isDeviationDeleted():
            logger.warning("  This Deviation from DeviantArt has been deleted!")
            return False
    
    # Create a Deviation object to fill with data.
        try:
            deviation = Deviation(self.driver.find_element(By.TAG_NAME, "main"))
        except Exception as e:
            logger.error("Failed to generate Deviation object from web page data!")
            logger.error(e)
            return False
    
    # Determine Deviation type.
        media_type = self.determineDeviationMediaType(deviation)
    
    # Scrape the Deviation's initial metadata.
        if not deviation.fetchMetadata(media_type):
            return False
        # Record the URL the scraper was given.
        deviation.metadata["url"] = str(url)
    
    # Create a new directory to save the Deviation to.
        dir_path = self.generateDeviationDirectory(deviation)
        if dir_path == False:
            return False
    
    # Download the Deviation.
        if media_type == False:
            return False
        else:
            deviation.metadata["post type"] = media_type
        self.downloadDeviation(deviation, dir_path, SCREENSHOT)
        
    # Scrape the artist's comments.
        return True
        
    


class Deviation():
    def __init__(self, main_element):
        self.main = main_element
        self.description = ""
        self.metadata = {}
        # Metadata aught to contain:
        # * Author
        # * Date
        # * URL
        # * Time of Scrape
        # * Post Type
        
    def fetchMetadata(self, media_type):
        logger.debug("Fetching Deviation metadata...")
        if media_type == "text":
            try:
                art_stage = self.main.find_element(By.XPATH, ".//div[@data-hook='art_stage']")
                # Record the Deviation's title.
                self.metadata['title'] = art_stage.find_element(By.TAG_NAME, "h1").text
                # Record the author's handle.
                non_header_content = self.main.find_element(By.XPATH, "/html/body/div/main/div/div[2]")
                self.metadata['author'] = non_header_content.find_element(By.XPATH, ".//a[@data-hook='user_link']").get_attribute("data-username")
                # Record the time the Deviation was posted.
                timestring = self.main.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                datetime_obj = datetime.fromisoformat(timestring)
                self.metadata["date"] = datetime_obj
                # Record the time the Deviation was scraped.
                self.metadata["time of scrape"] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                logger.debug("...fetching complete!")
                return True
            except Exception as e:
                logger.error("Error scraping metadata from a text-only Deviation on DeviantArt!")
                logger.error(e)
                return False
        else:
            try:
                title_info_bar = self.main.find_element(By.XPATH, ".//div[@data-hook='deviation_meta']")
                # Record the Deviation's title.
                self.metadata['title'] = title_info_bar.find_element(By.XPATH, ".//h1[@data-hook='deviation_title']").text
                # Record the author's handle.
                self.metadata['author'] = title_info_bar.find_element(By.XPATH, ".//a[@data-hook='user_link']").get_attribute("data-username")
                # Record the time the Deviation was posted.
                timestring = title_info_bar.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                datetime_obj = datetime.fromisoformat(timestring)
                self.metadata["date"] = datetime_obj
                # Record the time the Deviation was scraped.
                self.metadata["time of scrape"] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                logger.debug("...fetching complete!")
                return True
            except Exception as e:
                logger.error("Error scraping metadata from DeviantArt!")
                logger.error(e)
                return False
            
            
            