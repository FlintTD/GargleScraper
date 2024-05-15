from selenium.common.exceptions import *
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as secretdriver
import time
import os
import io
import tempfile
import shutil
import json
import markdownify
import re
import logging
import requests
import random
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from PIL import Image

logger = logging.getLogger('GargleScraper')

class DeviantartScraper():
    def __init__(self, working_directory, username, password):
        self.working_dir = working_directory
        self.path_to_archive = os.path.join(self.working_dir, "Archive")
        self.username = username
        self.password = password
        self.download_dir = os.path.join(self.working_dir, "Tempdownloads")
        
        # Set up Chromedriver.
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        # Argument to disable the AutomationControlled flag.
        #chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
        # Exclude the collection of enable-automation switches. 
        #chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # Turn-off userAutomationExtension 
        #chrome_options.add_experimental_option("useAutomationExtension", False)
        #chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) #This makes the "DevTools listening on ws://127.0.0.1" message go away.
            # Create an user_data_dir and add its path to the options
        #user_data_dir = os.path.normpath(tempfile.mkdtemp())
        user_data_dir = os.path.join(self.working_dir, 'CustomChromeProfile')
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Initialize Chromedriver.
        self.driver = secretdriver.Chrome(
            executable_path = os.path.join(os.getcwd(), 'chromedriver'),
            options = chrome_options
        )
        # Changing the property of the navigator value for webdriver to undefined 
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 5, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
    
    
    def load(self):
        logger.info("The DeviantArt scraper is opening a browser window...")
        # Load www.deviantart.com in a web browser.
        self.driver.get("http://www.deviantart.com")
        # Set the download directory
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': self.download_dir}}
        self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        self.driver.execute("send_command", params)
        if not os.path.isdir(self.download_dir):
            os.makedirs(self.download_dir)
        # Wait until the title of the page includes the word "DeviantArt".
        dummy = self.wait.until(EC.title_contains("DeviantArt"))
        time.sleep(2 + 2 * random.random())
    
    
    def mimicTyping(self, element, string):
        for char in string:
            element.send_keys(char)
            time.sleep(0.1 + (0.4 * random.random()))
    
    
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
            time.sleep(1 + 2 * random.random())
        except:
            # If User Profile button isn't found, logging in to DeviantArt is necessary.
            # To log in, first navigate to the DeviantArt login page.
            login_button = self.driver.find_element(By.XPATH, ".//a[@href='https://www.deviantart.com/users/login']")
            login_button.click()
            # Wait until the Login page loads.
            unused_login_title = self.wait.until(EC.title_contains("Log In"))
            # Enter the login username.
            time.sleep(1 + 1.5 * random.random())
            username_textbox = self.driver.find_element(By.XPATH, "//input[@name='username']")
            self.mimicTyping(username_textbox, self.username)
            username_textbox.send_keys(Keys.RETURN)
            time.sleep((1 + 1.5 * random.random()))
            # Enter the login password.
            password_textbox = self.driver.find_element(By.XPATH, "//input[@name='password']")
            self.mimicTyping(password_textbox, self.password)
            # Submit the form to log in.
            try:
                time.sleep(0.5 + 0.5 * random.random())
                password_textbox.send_keys(Keys.RETURN)
            
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
                accountButton = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//a[@data-username='{self.username}']")))
            except Exception as e:
                logger.error("The scraper has failed to log in to DeviantArt!")
                logger.error(e)
        #time.sleep(1)
    
    
    def teardown(self):
        logger.info("The DeviantArt scraper module is deactivating...")
        self.driver.close()
    
    
    def goToPage(self, url):
        logger.debug("Navigating to web page at: " + str(url))
        time.sleep(3 + 2.5 * random.random())
        self.driver.get(str(url))
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@aria-label='DeviantArt - Home']")))
        time.sleep(0.5 + 1.5 * random.random())
    
    
    def goToImagePage(self, url):
        logger.debug("Navigating to web page at: " + str(url))
        time.sleep(3 + 2.5 * random.random())
        self.driver.get(str(url))
        self.wait.until(EC.visibility_of_element_located((By.XPATH, ".//img")))
        time.sleep(0.5 + 1.5 * random.random())
    
    
    def goBackAPage(self):
        logger.debug("Going back to the previous web page.")
        time.sleep(0.5 + 0.5 * random.random())
        self.driver.back()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@aria-label='DeviantArt - Home']")))
        time.sleep(0.5 + 1.5 * random.random())
    
    
    def scrollToElement(self, element):
        try:
            self.driver.execute_script("return arguments[0].scrollIntoView(true);", element)  # Scroll to web element
            #ActionChains(self.driver).move_to_element(element).perform()  # Scroll to web element
            self.wait.until(EC.visibility_of(element))
            logger.debug("Scrolled to element.")
        except Exception as e:
            logger.error("Error scrolling to web element!")
            logger.error(e)
    
    
    def screenshot(self, element, dir_path, screenshot_name):
        try:
            self.scrollToElement(element)
            location = element.location
            logger.debug("Taking screenshot of element at screen coordinates: " + str(location))
            size = element.size
            png = self.driver.get_screenshot_as_png()
            im = Image.open(io.BytesIO(png))
            left = location['x']
            top = location['y'] - self.driver.execute_script('return window.pageYOffset;')
            right = left + size['width']
            bottom = top + size['height']
            im = im.crop((left, top, right, bottom))
            rgb_im = im.convert('RGB')
            rgb_im.save(os.path.join(dir_path, screenshot_name + ".jpg"))
        except Exception as e:
            logger.error("Error taking screenshot of web element!")
            logger.error(e)
    
    
    def sanitizeString(self, string):
        disallowed_characters = ['#','%','&','{','}','\\','<','>','*','?','/',' ','$','!','\'','\"',':','.','@','+','`','|','=', '\n']
        return "".join(map(lambda c: c if c not in disallowed_characters else "_", string))
        #return "".join(filter(lambda char: char not in disallowed_characters, string))
    
    
    # TODO
    def isDeviationDeleted(self):
        deleted = False
        return deleted
        
    
    def isDeviantartGallery(self, url):
        match = re.match('https?:\/\/www.deviantart.com\/[^\s]*\/gallery\/[^\s]*', url)
        if match is None:
            logger.debug("Identified this DeviantArt URL as a single deviation!")
            return False
        else:
            logger.debug("Identified this DeviantArt URL as a gallery of deviations!")
            return True
    
    
    # Generates a new directory for containing the archive of a Deviation or gallery of Deviations.
    # Returns False, or a path to the archive directory it has created.
    def generateDeviationDirectory(self, deviation):
        if "series" in deviation.metadata.keys():
        # Generate gallery download directory name.
            sanitized_id = self.sanitizeString(deviation.metadata["series"])
            dir_name = sanitized_id
            path_to_download_dir = os.path.join(self.path_to_archive, os.path.join(deviation.metadata["author"].lower(), dir_name))
        else:
        # Generate Deviation download directory name.
            datestring = deviation.metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
            sanitized_id = self.sanitizeString(deviation.metadata["title"])
            dir_name = datestring + "__" + sanitized_id[0:16]
            path_to_download_dir = os.path.join(self.path_to_archive, os.path.join(deviation.metadata["author"].lower(), dir_name))
        
        # If the directory already exists, but the Deviation is not downloaded (Gargle Scraper checks before this point), don't make a new directory.
        if not os.path.exists(path_to_download_dir):
            # Create the post's archive directory.
            os.makedirs(path_to_download_dir)
        
        return path_to_download_dir
    
    
    def determineDeviationMediaType(self, deviation):
        try:
            art_stage = deviation.main.find_element(By.XPATH, "//div[1]")
            # Is it a video?
            try:
                art_stage.find_element(By.XPATH, ".//section[@data-hook='react_playable']")
                logger.debug("Deviation identified as a video.")
                logger.error("Video deviations are not yet suported for archival from DeviantArt!")
            except:
                pass
            # Is it an image?
            try:
                art_stage.find_element(By.XPATH, "//div[@typeof='ImageObject']")
                logger.debug("Deviation identified as an image.")
                return "image"
            except:
                # It must be text.
                logger.debug("Deviation identified as text.")
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
    # Returns a Boolean indicating success or failure.
    def downloadText(self, deviation, archive_path, SCREENSHOT):
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
            
        # Sanitize the text from the Deviation.
            text = "\n".join(text_list)
        
        # Try to save the Deviation's text.
            filename = f"{sanitized_title}__{datestring}"
            with open(os.path.join(archive_path, (filename + ".txt")), 'w', encoding="utf-8") as file:
                file.write(text)
        
        # Scrape and archive the author's comments in a separate file.
            if author_comments != None:
            # Scrape the author's comments.
                html_comment = author_comments.get_attribute('innerHTML')
        
            # Sanitize the author's comments.
                markdown_comment = markdownify.markdownify(html_comment, heading_style="ATX")
                
                datestring = deviation.metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
                sanitized_title = self.sanitizeString(deviation.metadata["title"])
                
            # Try to save the author comments.
                filename = f"{sanitized_title}__comments__{datestring}"
                with open(os.path.join(archive_path, (filename + ".md")), 'w', encoding="utf-8") as file:
                    file.write(markdown_comment)
            else:
                logger.debug("No author comments found for this deviation.")
        
        #Try to save the Deviation's metadata.
            self.downloadMetadata(deviation, archive_path)
        
        # If the Screenshot flag is set, take a screenshot of the Deviation and author's comments as well.
            if SCREENSHOT:
                self.screenshot(deviation_text, archive_path, filename)
                self.screenshot(author_comments, archive_path, (filename + "__comments"))
            
            return True
        
        except NoSuchElementException as e:
            logger.error("Error downloading text from DeviantArt!")
            logger.error(e)
            # Return a failure.
            return(False)
    
    
    # Downloads a Deviation containing an image.
    # Returns a Boolean indicating success or failure.
    def downloadImage(self, deviation, archive_path, SCREENSHOT):
        has_tags = False
        try:
        # Try to locate the deviation's size text.
        # The number of divs in the deviation's information block can change by one, depending on if tags are used or not.
            deviation_information_blocks = deviation.main.find_elements(By.XPATH, "./div/div[2]/div/div")
            logger.debug("Found the deviation's information blocks!")
            logger.debug("Found " + str(len(deviation_information_blocks)) + " info blocks!")
        except Exception as e:
            logger.error("Failed to find the deviation's matadata information blocks!")
            logger.error(e)
            return False
        
        # Be careful here, python lists are zero-indexed, but XPATH is one-indexed...
        try:
            author_comments = None
            deviation_size_data_string = None
            tags_list = []
            additional_details = {}
            
        # Hunt down author comments, deviation size data, tags, and other information by iterating through all of the information blocks.
            for info_block in deviation_information_blocks:
            # This finds the description block!
                if "description" in str(info_block.get_attribute("id")):
                    # Save the description/author comments for later.
                    author_comments = info_block
            # This finds the tags block.
                try:
                    tags_maybe = info_block.find_elements(By.XPATH, "./div/a")
                    for tag in tags_maybe:
                        raw_tag_url = tag.get_attribute('href')
                        if "/tag/" in raw_tag_url:
                            split_tag_url = raw_tag_url.split("/")
                            tags_list.append(split_tag_url[-1])
                except Exception as e:
                    print(e)
            # This finds additional metadata detail blocks, which may exist to identify depicted characters.
            # TODO: This feature is not edge-tested!
                try:
                    detail_title = info_block.find_element(By.XPATH, "./span/span").text
                    detail_description = info_block.find_element(By.XPATH, "./span/a").text
                    additional_details[detail_title] = detail_description
                except:
                    pass
            # This finds the deviation's size data string.
                try:
                    deviation_size_data_string = info_block.find_element(By.XPATH, "./div[1]/div[1]/div[1]/div[1]/div[1]/div[2]").text
                    logger.debug("Deviation size data string: " + str(deviation_size_data_string))
                except:
                    pass
            
            if deviation_size_data_string is None:
                logger.error("Failed to find the HTML location of the deviation's size data text within the size-data block!")
                logger.error("DeviantArt probably shuffled their divs around again!")
                raise Exception("Deviation size data string was not found in web page!")
            else:
                logger.info("The deviation's size data string: " + str(deviation_size_data_string))
            
        except Exception as e:
            logger.error("Failed to find the deviation's size-data block!")
            logger.error(e)
            return False
        
        # Try to parse the deviation's original size from the size text.
        try:
            sanitized_size_data_string = deviation_size_data_string.split(" ")[0].split("p")[0]
            deviation.metadata["original_width"] = sanitized_size_data_string.split("x")[0] + "px"
            deviation.metadata["original_height"] = sanitized_size_data_string.split("x")[1] + "px"
        except Exception as e:
            logger.error("Failed to read the image deviation's original size!")
            logger.error(e)
            return False
        
        # Save the deviation's tags to metadata.
        if tags_list:
            deviation.metadata["tags"] = tags_list
            logger.debug("Scraped the deviation's tags.")
        else:
            logger.debug("No tags were found for this deviation.")
        
        # Save the deviation's additional details as additional metadata.
        if additional_details:
            deviation.metadata["additional_details"] = additional_details
        
        try:
        # Try to locate and download the Deviation.
            downloadable = False
            try:
                # Try to locate the deviation.
                xpath_string = './/img[@alt="' + deviation.metadata['title'] + '"]'
                deviation_image = deviation.main.find_element(By.XPATH, xpath_string)
            except Exception as e:
                logger.error("The deviation itself could not be found on the page!")
                logger.error(e)
                return False
                
            try:
                # Try to locate and analyze the download button on the Deviation's page.
                download_button = deviation.main.find_element(By.XPATH, ".//a[@data-hook='download_button']")
                if download_button.get_attribute("aria-label") == "Free download":
                    try:
                # Download the full resolution image.
                        logger.debug("Full resolution image is available! Downloading...")
                        download_button.click()
                        # Wait for the image to download.
                        end_time = datetime.now() + timedelta(seconds = 20)
                        time.sleep(0.5)
                        download_incomplete = True
                        while download_incomplete:
                            images = os.listdir(self.download_dir)
                            if not images == []:
                                for file in images:
                                    if file.endswith('.crdownload'):
                                        time.sleep(1)
                                        if datetime.now() > end_time:
                                            logger.error("Image mover got caught in an infinite loop! Aborting scrape of this Deviation!")
                                            return False
                                    else:
                                        download_incomplete = False
                            else:
                                if datetime.now() > end_time:
                                    logger.error("Image mover got caught in an infinite loop! Aborting scrape of this Deviation!")
                                    return False
                        # Move the image from Tempdownloads to the archive directory.
                        for image_name in images:
                            shutil.move(os.path.join(self.download_dir, image_name), os.path.join(archive_path, image_name))
                            deviation.metadata["full_resolution"] = True
                    except Exception as e:
                        logger.error("Deviation could not be moved from Tempdownloads folder!")
                        logger.error(e)
                        return False
                else:
                    pass
                    
            except:
            # Download the image the unconventional way.
            # If the deviation is older than 2022, there is a good chance it can still be downloaded in full resolution.
            # This requires a separate method, detailed here: https://gist.github.com/micycle1/735006a338e4bea1a9c06377610886e7
                logger.debug("Full resolution image deviation unavailable through direct means!")
                if deviation.metadata["date"] > datetime(2022, 1, 1, tzinfo=timezone.utc):
                # Try to download the publically-available low-rez version.
                    logger.debug("Downloading the publically-available low-rez image version...")
                    try:
                        image_source_url = deviation_image.get_attribute("src")
                        # Download the image via URL.
                        image_content = requests.get(image_source_url).content
                        image_file = io.BytesIO(image_content)
                        image = Image.open(image_file)
                        # Sanitize out an image filename.
                        image_filename = re.match('https?://[^\s]*\?token=', image_source_url).group().split('/')[-1]
                        image_filename = image_filename.replace('?token=', '')
                        # Determine image type.
                        image_type = image_filename.split('.')[1]
                        # Save the image to a file.
                        url_ized_name = re.sub("\W", "_", deviation.metadata["title"].lower())
                        guessed_original_name = url_ized_name + "_by_" + deviation.metadata["author"].lower()
                        image_filename = re.sub('[\w\d]{7}-[\w\d]{8}-[\w\d]{4}-[\w\d]{4}-[\w\d]{4}-[\w\d]{12}', guessed_original_name, image_filename)
                        with open(os.path.join(archive_path, image_filename), 'wb') as file:
                            image.save(file)
                            logger.debug("Saved deviation image as: " + image_filename)
                    except Exception as e:
                        logger.error("Error downloading low-rez image from DeviantArt!")
                        logger.error(e)
                        return(False)
                else:
                # Try to tweak the URL to download the original full-rez version.
                    logger.debug("Sneakily downloading the full-rez (jpg only 😢) image version...")
                    try:
                        image_source_url = deviation_image.get_attribute("src")
                        # Check the image URL to see if it is a machine-code alphanumeric ("obfuscated') filename, or a sanitized version of the original title.
                        # These obfuscated filenames need to be handled differently than the more standard sanitized title URLs.
                        detokenized_image_url = image_source_url.split('?')[0]
                        obfuscation_pattern = "\w{8}-\w{4}-\w{4}-\w{4}-\w{12}.jpg"
                        obfuscated_image_match = re.search(obfuscation_pattern, detokenized_image_url)
                        if obfuscated_image_match:
                            logger.debug("Identified this deviation's source URL as obfuscated! Undoing...")
                            # Modify the image URL.
                            modified_image_url = detokenized_image_url.replace("/f/", "/intermediary/f/")
                            width = deviation.metadata["original_width"][:-2]
                            height = deviation.metadata["original_height"][:-2]
                            html_dimensions_string = f"/v1/fill/w_{width},h_{height},q_100/"
                            url_ized_name = re.sub("\W", "_", deviation.metadata["title"].lower())
                            guessed_original_name = url_ized_name + "_by_" + deviation.metadata["author"].lower()
                            secret_da_code = detokenized_image_url.split('/')[-1].split('-')[0]
                            guessed_original_URL_name = guessed_original_name + "_" + secret_da_code + "-fullview.png"
                            highrez_image_url = modified_image_url + html_dimensions_string + guessed_original_URL_name
                            logger.debug("High resolution unobfuscated image URL: " + highrez_image_url)
                        else:
                            logger.debug("This deviation's source URL appears to be unobfuscated.")
                            # Modify the image URL.
                            modified_image_url = image_source_url.split("?token=")[0].replace("/f/", "/intermediary/f/")
                            width = deviation.metadata["original_width"][:-2]
                            height = deviation.metadata["original_height"][:-2]
                            html_dimensions_string = f"/v1/fill/w_{width},h_{height},q_100/"
                            highrez_image_url = re.sub("/v1/fill/.+/", html_dimensions_string, modified_image_url)
                            logger.debug("High resolution image URL: " + highrez_image_url)

                        # Download the image via URL.
                        image_content = requests.get(highrez_image_url).content
                        image_file = io.BytesIO(image_content)
                        image = Image.open(image_file)
                        # Sanitize out an image filename.
                        if obfuscated_image_match:
                            image_filename = guessed_original_URL_name
                        else:
                            image_filename = re.match('https?://[^\s]*\?token=', image_source_url).group().split('/')[-1]
                            image_filename = image_filename.replace('?token=', '')
                        # Determine image type.
                        image_type = image_filename.split('.')[1]
                        # Save the image to a file.
                        with open(os.path.join(archive_path, image_filename), 'wb') as file:
                            image.save(file)
                            logger.debug("Saved deviation image as: " + image_filename)
                    except Exception as e:
                        logger.error("Error sneaky-downloading the full-rez image from DeviantArt!")
                        logger.error(e)
                        return(False)
        
        # Scrape and archive the author's comments in a separate file.
            if author_comments != None:
            # Scrape the author's comments.
                html_comment = author_comments.get_attribute('innerHTML')
        
            # Sanitize the author's comments.
                markdown_comment = markdownify.markdownify(html_comment, heading_style="ATX")
                
                datestring = deviation.metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
                sanitized_title = self.sanitizeString(deviation.metadata["title"])
                
            # Try to save the author comments.
                filename = f"{sanitized_title}__comments__{datestring}"
                with open(os.path.join(archive_path, (filename + ".md")), 'w', encoding="utf-8") as file:
                    file.write(markdown_comment)
            else:
                logger.debug("No author comments found for this deviation.")
                
        #Try to save the Deviation's metadata.
            self.downloadMetadata(deviation, archive_path)
        
        # If the Screenshot flag is set, take a screenshot of the Deviation and author's comments as well.
            if SCREENSHOT:
                self.screenshot(deviation_image, archive_path, f"{sanitized_title}__screenshot__{datestring}")
                self.screenshot(author_comments.find_element(By.XPATH, ".."), archive_path, f"{sanitized_title}__comments_screenshot__{datestring}")
            
            return True
        
        except NoSuchElementException as e:
            logger.error("Error downloading text from DeviantArt!")
            logger.error(e)
            # Return a failure.
            return(False)
    
    
    def downloadDeviation(self, deviation, dir_path, SCREENSHOT):
        downloaded = False
        if deviation.metadata["post_type"] == "text":
            logger.info("  Text Deviation.")
            downloaded = self.downloadText(deviation, dir_path, SCREENSHOT)
        elif deviation.metadata["post_type"] == "image":
            logger.info("  Image Deviation.")
            downloaded = self.downloadImage(deviation, dir_path, SCREENSHOT)
        elif deviation.metadata["post_type"] == "video":
            logger.info("  Video Deviation.")
            downloaded = self.downloadVideo(deviation, dir_path, SCREENSHOT)
        else:
            return downloaded
        
        return downloaded
    
    
    # Download the full data and metadata of a Deviation.
    # Returns two values:
    #     True or False boolean, indicating a successful scrape or not.
    #     Integer, indicating how many deviations were viewed.
    def scrapeFromDeviantart(self, url, SCREENSHOT, gallery_data=[]):
        # Navigate to the requested page on DeviantArt.
        self.goToPage(url)
        # Check to see if the Deviation has been deleted.
        if self.isDeviationDeleted():
            logger.warning("  This Deviation from DeviantArt has been deleted!")
            return False, 1, 0
        
        # Check if the URL is a DeviantArt gallery or a single Deviation.
        if self.isDeviantartGallery(url):
            # Try to find the gallery title.
            try:
                gallery_div = self.driver.find_element(By.ID, "sub-folder-gallery")
                gallery_title = gallery_div.find_element(By.XPATH, "//div[@role='button']/div[1]").get_attribute("innerHTML").split('<')[0]
                gallery_deviation_count = int(gallery_div.find_element(By.XPATH, "//div[@role='button']/div[1]/span").text)
                logger.debug("DeviantArt gallery title: " + gallery_title)
            except Exception as e:
                logger.error("Failed to locate DeviantArt gallery title!")
                logger.error(e)
                return False, 1, 0
            
            # Try to compile a list containing a URL to each work in the gallery.
            try:
                gallery_list = []
                gallery_content_row_list = []
                # Scroll to the bottom of the gallery over time, to load every deviation.
                row = 0
                last_scroll_height = 0
                scrolled_to_bottom = False
                while scrolled_to_bottom == False:
                    gallery_content_row_list = gallery_div.find_elements(By.XPATH, ".//div[@data-testid='content_row']")
                    
                    # Go through the full gallery to get every deviation URL.
                    for gallery_content_row in gallery_content_row_list:
                        deviation_anchors = gallery_content_row.find_elements(By.XPATH, ".//a[@aria-label]")
                        for deviation_anchor in deviation_anchors:
                            url_string = deviation_anchor.get_attribute('href')
                            if url_string not in gallery_list:
                                gallery_list.append(url_string)
                            else:
                                logger.debug("Found duplicate deviation URL: " + str(url_string))
                    
                    # Scroll
                    self.scrollToElement(gallery_content_row_list[-2])
                    time.sleep(1)
                    
                    # Check to see if we need to keep scrolling.
                    new_scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_scroll_height == last_scroll_height:
                        scrolled_to_bottom = True
                    else:
                        last_scroll_height = new_scroll_height
                
                # Check if we've found all of the deviations.
                if len(gallery_list) < gallery_deviation_count:
                    logger.warning("Scraper found fewer deviations than the nominal quantity claimed by DeviantArt!")
                    logger.warning("  Found: " + str(len(gallery_list)))
                    logger.warning("  Expected: " + str(gallery_deviation_count))
                    #logger.warning("  Found deviations start with: " + gallery_list[0] + "...")
                    #logger.warning("  ...and end with: " + gallery_list[-1])
                    #raise Exception("Scraper found fewer deviations than the nominal quantity claimed by DeviantArt!")
                logger.info("Found " + str(len(gallery_list)) + " deviations in this gallery!")
                
            except Exception as e:
                logger.error("Failed to parse the DeviantArt gallery!")
                logger.error(e)
                return False, 1, 0
            
            if gallery_list == []:
                logger.error("Failed to find any deviation URLs from the gallery!")
                return False, 1, 0
            
            # Go through the listed deviations one by one.
            logger.info("Scraping DeviantArt Gallery...")
            total_passed = False
            total_pages = 0
            additional_pages = len(gallery_list) - 1
            for deviation_url in gallery_list:
                passed, pages, unused = self.scrapeFromDeviantart(deviation_url, SCREENSHOT, [url, gallery_title])
                total_passed = passed
                total_pages += pages
            
            return total_passed, total_pages, additional_pages
            
        else:
            # Create a Deviation object to fill with data.
            try:
                deviation = Deviation(self.driver.find_element(By.TAG_NAME, "main"))
            except Exception as e:
                logger.error("Failed to generate Deviation object from web page data!")
                logger.error(e)
                return False, 1, 0
            
            # Determine Deviation type.
            media_type = self.determineDeviationMediaType(deviation)
        
            # Scrape the Deviation's initial metadata.
            if not deviation.fetchMetadata(media_type):
                return False, 1, 0
            
            # Record the URL the scraper was given.
            deviation.metadata["url"] = str(url)
            
            # If this deviation is part of a gallery, put the gallery name into the metadata.
            if gallery_data != []:
                deviation.metadata["series_url"] = gallery_data[0]
                deviation.metadata["series"] = gallery_data[1]
                
            
            # Create a new directory to save the Deviation to, if needed.
            dir_path = self.generateDeviationDirectory(deviation)
            if dir_path == False:
                return False, 1, 0
            
            # Check if this deviation has already been scraped.
            metadata_files = [file_name for file_name in os.listdir(dir_path) if file_name.endswith('metadata.json')]
            for file in metadata_files:
                with open(os.path.join(dir_path, file)) as json_metadata:
                    metadata_directory = json.load(json_metadata)
                    if url == metadata_directory["url"]:
                        logger.debug("This deviation has already been scraped! Moving on.")
                        return True, 1, 0
                        
            
            # Download the Deviation and author comments.
            if media_type == False:
                return False, 1, 0
            else:
                deviation.metadata["post_type"] = media_type
            if (not self.downloadDeviation(deviation, dir_path, SCREENSHOT)) and (len(os.listdir(dir_path)) < 1):
                # Delete the post's archive directory, unless it's a gallery containing at least one other archived work.
                logger.debug("Deleting the incomplete archive directory...")
                shutil.rmtree(dir_path)
                return False, 1, 0
            
            time.sleep(2 + 2 * random.random())
        return True, 1, 0
        
    


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
                art_stage = self.main.find_element(By.XPATH, "//div[1]")
                # Record the Deviation's title.
                self.metadata["title"] = art_stage.find_element(By.TAG_NAME, "h1").text
                # Record the author's handle.
                non_header_content = self.main.find_element(By.XPATH, "/html/body/div/main/div/div[2]")
                self.metadata["author"] = non_header_content.find_element(By.XPATH, ".//a[@data-hook='user_link']").get_attribute("data-username")
                # Record the time the Deviation was posted.
                timestring = self.main.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                datetime_obj = datetime.fromisoformat(timestring)
                self.metadata["date"] = datetime_obj
                # Record the time the Deviation was scraped.
                self.metadata["time_of_scrape"] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                logger.debug("...fetching complete!")
                return True
            except Exception as e:
                logger.error("Error scraping metadata from a text-only Deviation on DeviantArt!")
                logger.error(e)
                return False
        else:
            try:
                title_info_bar = self.main.find_element(By.XPATH, "./div/div[2]")
                # Record the Deviation's title.
                self.metadata["title"] = title_info_bar.find_element(By.XPATH, ".//h1").text
                # Record the author's handle.
                self.metadata["author"] = title_info_bar.find_element(By.XPATH, ".//a").get_attribute("data-username")
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
            
            
            