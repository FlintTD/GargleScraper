from selenium.common.exceptions import *
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
import io
import shutil
import json
import re
import logging
import requests
import youtube_dl
from datetime import datetime
from PIL import Image

logger = logging.getLogger('GargleScraper')

def ydlHook(d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')

class TwitterScraper():
    def __init__(self, archivepath, email, username, password):
        self.path_to_archive = archivepath
        self.email = email
        self.username = username
        self.password = password
        self.working_dir = os.path.dirname(__file__)
        self.posts_viewed = 0
        # Set up Chromedriver.
        # Old Chromedriver without undetected-chromedriver
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={os.path.join(self.working_dir, '/CustomChromeProfile')}")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) #This makes the "DevTools listening on ws://127.0.0.1" message go away.
        self.driver = webdriver.Chrome(
            #service = Service(executable_path = os.path.join(os.getcwd(), 'chromedriver')),
            options = chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10, poll_frequency=1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
    
    
    def load(self):
        logger.info("The Twitter scraper is opening a browser window...")
        # Load www.twitter.com in a web browser.
        self.driver.get("http://www.twitter.com")
        # Wait until the title of the page includes the word "Twitter".
        dummy = self.wait.until(EC.title_contains("Home / X"))

    
    def login(self):
        # Check if logging in to Twitter is necessary.
        try:
            # Check if we are already logged in
            # Does the web page have an Account button?
            accountButton = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Account menu']")))
        finally:
            # If Home header isn't found, logging in to Twitter is necessary.
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
                    logger.debug("Verified!")
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
        logger.info("The Twitter scraper module is deactivating...")
        self.driver.close()
    
    
    def goToPage(self, url):
        logger.debug("Navigating to web page at: " + str(url))
        self.driver.get(str(url))
        self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        self.posts_viewed += 1
        time.sleep(1)
    
    
    def goBackAPage(self):
        self.driver.back()
        self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        time.sleep(1)
    
    
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
            rgb_im = im.convert('RGB')
            rgb_im.save(os.path.join(dir_path, screenshot_name + ".jpg"))
        except Exception as e:
            logger.error("Error taking screenshot of web element!")
            logger.error(e)
    
    
    def isTweetDeleted(self):
        # Wait for the content column on the page to fully load.
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@aria-label='Home timeline']")))
        conversation = self.driver.find_element(By.XPATH, "//div[@aria-label='Home timeline']")
        deleted = False
        
        try:
            # Find the full "conversation" thread (e.g. tweet + comments + previous tweets).
            error_message = conversation.find_element(By.XPATH, "//div[@data-testid='error-detail']")
            return True
        except Exception as e:
            deleted = False
        
        # If the scraper cannot find Tweet text, but it can find this text string, then this Tweet has been taken down.
        try:
            tweet = conversation.find_element(By.XPATH, ".//article[@tabindex='-1']")
            text = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
            deleted = False
        except Exception as e:
            try:
                tweet = conversation.find_element(By.XPATH, ".//article[@tabindex='-1']")
                tweet.find_element(By.XPATH, ".//span[contains(text(), 'This Tweet is from an account that no longer exists.')]")
                deleted = True
            except:
                deleted = False
        
        return deleted
    
    
    # Determine if this tweet contains a quoted tweet.
    # Returns:
    # * the URL of a quoted Tweet if found,
    # * 'DELETED' if a quoted Tweet is found but deleted,
    # * or an empty string if no quoted Tweet is found.
    def checkForQuoteTweets(self, tweet):
        try:
            # Check for non-deleted Quote Tweet.
            quote_tweet = tweet.find_element(By.XPATH, ".//div[@tabindex='0'][@role='link']")
        except NoSuchElementException:
            try:
                # Check for deleted Quote Tweet.
                quote_tweet = tweet.find_element(By.XPATH, ".//article[@tabindex='-1'][@role='article']")
                return "DELETED"
            except NoSuchElementException:
                return ""
        else:
            quoteTweetUrl = quote_tweet.find_element(By.XPATH, ".//a[@href][@role='link']").get_attribute("href")
            sanitizedUrl = quoteTweetUrl.replace(r'/photo/1', '')
            #print("Quote Tweet URL:")
            #print("    " + sanitizedUrl)
        
        return sanitizedUrl
    
    
    # A recursive function looking at every parent element of the input element.
    def isElementInQuotedTweet(self, element):
        try:
            parent = element.find_element(By.XPATH, '..')
            if parent.tag_name == "article":
                return False
            
            # In the below process, we are looking for a <div> element with the attribute "role=link".
            # This element is a Quoted Tweet.
            if parent.get_attribute("role") is None:
                # If the attribute isn't present in the parent, then we cannot know if this is an element from a Quoted Tweet.
                return self.isElementInQuotedTweet(parent)
            elif parent.tag_name == "div":
                # If the attribute is present, and the element is a div, then this parent element is from a Quoted Tweet.
                return True
            else:
                return False
        except Exception as e:
            print(e)
            time.sleep(20)
    
    
    # Determine what kind of media is present in the provided Tweet.
    # Arguements: "tweet" is a Selenium driver element pointing to a specific Tweet in a page and Thread.
    def determineTweetMediaContents(self, tweet):
        #tweet.screenshot("/Logs/tweet.png")
        
        # Determine if the Tweet contains a Quote-Tweet.
        is_quoting = False
        quote_url = self.checkForQuoteTweets(tweet)
        if quote_url != "" or 'DELETED':
            is_quoting = True
        
        # Try to find a video in the tweet first.
        try:
            video = tweet.find_element(By.XPATH, ".//div[@data-testid='videoPlayer']")
            if is_quoting and (quote_url != 'DELETED'):
                if self.isElementInQuotedTweet(video):
                    #print("  Not a video post, video found inside quoted tweet!")
                    raise NoSuchElementException
        except NoSuchElementException:
            #print("Not a video!")
            pass
        else:
            return "video"
        
        # Try to find an image in the tweet second.
        try:
            image = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetPhoto']")
            if is_quoting and (quote_url != 'DELETED'):
                if self.isElementInQuotedTweet(image):
                    #print("  Not an image post, image found inside quoted tweet!")
                    raise NoSuchElementException
        except NoSuchElementException:
            #print("Not an image!")
            pass
        else:
            return "image"
            
        # Try to find text in the tweet last.
        try:
            text = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
            if is_quoting and (quote_url != 'DELETED'):
                if self.isElementInQuotedTweet(text):
                    #print("  Not a text post, text found inside quoted tweet!")
                    raise NoSuchElementException
        except NoSuchElementException:
            #print("Not text!")
            pass
        else:
            return "text"
        
        print("Error! Twitter scraper is unsure what media this Tweet contains!")
    
    
    # Look at the loaded Twitter page, and pick out the relevant Tweets from a Thread.
    # Returns a List of individual Tweets.
    def analyzeThread(self):
        # Wait for the content column on the page to fully load.
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@aria-label='Home timeline']")))
        
        # Find the full "conversation" thread (e.g. tweet + comments + previous tweets).
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@aria-label='Timeline: Conversation']")))
        conversation = self.driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Conversation']")
        # Create a list of all present tweets in the conversation (original + previous + comments).
        present_tweets = conversation.find_elements(By.XPATH, ".//article[@data-testid='tweet'][@role='article']")
        #present_tweets = conversation.find_elements(By.XPATH, ".//*[@tabindex]")
        
        # Iterate over all tweets in the thread for analysis.
        past_base_tweet = False
        base_tweet_author_link = ""
        thread_segment_to_download = []
        base_tweet = False  # Will be a web element (if it is found).
        i = 0
        for tweet in present_tweets:
            i += 1
            # Check if this Tweet is the Thread's base Tweet.
            is_base_tweet = str(tweet.get_attribute("tabindex"))
            if is_base_tweet == "0":  #not the base tweet...
                if past_base_tweet == False:
                    # Add the tweet to the List of tweets to download (the "thread segment".)
                    thread_segment_to_download.append(tweet)
                else:
                    # Check if the tweet author is the same as the base tweet's author.
                    username_block = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']")
                    author_link = username_block.find_element(By.XPATH, ".//a").get_attribute("href")
                    if author_link == base_tweet_author_link:
                        # Add the author's additional tweet to the List of tweets to download (the "thread segment").
                        thread_segment_to_download.append(tweet)
                    else:
                        # Don't add a separate person's tweet.
                        return thread_segment_to_download, base_tweet
                        #return thread_segment_to_download, base_tweet
            elif is_base_tweet == "-1":  #the base tweet!
                #print("Base Tweet found!")
                if past_base_tweet == False:
                    # Record that this is the base tweet, and move on.
                    username_block = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']")
                    author_link = username_block.find_element(By.XPATH, ".//a").get_attribute("href")
                    base_tweet_author_link = author_link
                    thread_segment_to_download.append(tweet)
                    base_tweet = tweet
                    past_base_tweet = True
                else:
                    # This should never occur.
                    raise TypeError("Two base tweets found in a Twitter thread, but there should only be one!")
            else:
                # This should never occur.
                raise TypeError("Third type of tweet found in a Twitter thread (not 'base' or 'other')!")
        
        return thread_segment_to_download, base_tweet
    
    
    # Retrieves the metadata of a Tweet, when that Tweet is already open in the webdriver.
    # Returns a dictionary of metadata, if successful.
    def scrapeMetadata(self, tweet, url, base_tweet_override = False):
        metadata = {}
        
        try:
            # Record the author's handle.
            author_names = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']")
            author = author_names.find_element(By.TAG_NAME, "a").get_attribute("href")
            metadata["author"] = author.replace("https://twitter.com/", "")
            
            # Record the time the Tweet was posted.
            timestring = tweet.find_element(By.TAG_NAME, 'time').get_attribute("datetime")
            datetime_obj = datetime.fromisoformat(timestring)
            metadata["date"] = datetime_obj
            
            # Record whether this Tweet is the base Tweet.
            if not base_tweet_override:
                is_base_tweet = str(tweet.get_attribute("tabindex"))
                if is_base_tweet == "-1":
                    # Record this as the base tweet.
                    metadata["base_tweet"] = True
                    # Record the URL the scraper was given.
                    metadata["url"] = str(url)
                else:
                    # Record this is not the base tweet.
                    metadata["base_tweet"] = False
            else:
                # Record the URL the scraper was given.
                metadata["url"] = str(url)
                # Record this is not the base tweet.
                metadata["base_tweet"] = False
            
            # Record the time the Tweet was scraped.
            metadata["time of scrape"] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        except NoSuchElementException as e:
            print("  Error scraping metadata from Twitter!")
            print(e)
            # Return a failure.
        
        # Return a success.
        return(metadata)
    
    
    # Generates a directory path for containing the data from a Thread or single Tweet.
    def generatePostDirectoryPath(self, base_tweet):
        # Get the metadata of the base Tweet.
        metadata = self.scrapeMetadata(base_tweet, "")
        
        # Get any text the base Tweet may have.
        text = ""
        try:
            # Locate the tweet in the Twitter webpage.
            media = self.driver.find_element(By.XPATH, "//article[@data-testid='tweet'][@tabindex='-1']")
            # Locate the text in the base Tweet.
            textblock = base_tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")  # The dot at the start of the xpath means "search the children of this element".
            textblock_children_list = textblock.find_elements(By.XPATH, "*")
            # Parse the text within the tweet.
            for element in textblock_children_list:
                text = text + element.text
                if element.tag_name == "img":  # Check for Emojis (which are SVG images on Twitter)
                    text = text + element.get_attribute("alt")
                elif element.text == "":
                    text = text + "\n" + "\n"
            
        except NoSuchElementException as e:
            logger.debug("  Cannot find text in the base Tweet, using placeholder for directory name.")
            text = "mediaOnly"
        
        # Generate download directory name.
        datestring = metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
        disallowed_characters = ['#','%','&','{','}','\\','<','>','*','?','/',' ','$','!','\'','\"',':','@','+','`','|','=', '\n']
        sanitized_id = "".join(filter(lambda char: char not in disallowed_characters , text))
        dir_name = datestring + "__" + sanitized_id[0:16]
        path_to_download_dir = os.path.join(self.path_to_archive, os.path.join(metadata["author"], dir_name))
        
        return path_to_download_dir
    
    
    # Saves the metadata of a Tweet to a file.
    # Helper function for all "download[postType]" functions.
    # Returns a Boolean, representing whether the download succeeded.
    def downloadMetadata(self, current_metadata, path_to_download_dir, tweet_number):
        metadata = current_metadata
            
        try:
            # Try to save the metadata.
            metadata_filename = str(tweet_number) + "__" + metadata["date"].strftime('%Y-%m-%d_%H-%M-%S') + "__" + "metadata" + ".json"
            metadata["date"] = metadata["date"].strftime('%Y-%m-%d, %HH:%MM:%SS')
            json_metadata = json.dumps(metadata)
            with open(os.path.join(path_to_download_dir, metadata_filename), 'w') as file:
                file.write(json_metadata)
            
            # Return a success.
            return(True)
        
        except NoSuchElementException as e:
            print("  Error downloading metadata to file!")
            print(e)
            # Return a failure.
            return(False)
    
    
    # Downloads a post containing only text, and its metadata.
    # Returns a Boolean, String, JSON.
    #   Boolean represents whether the download succeeded.
    #   String is the downloaded text, or None if download failed.
    #   JSON is the post metadata, or None if download failed.
    def downloadText(self, tweet, tweet_number, metadata, path_to_download_dir, SCREENSHOT):
        # Locate the text in the Tweet.
        try:
            textblock = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")  # The dot at the start of the xpath means "search the children of this element".
            textblock_children_list = textblock.find_elements(By.XPATH, "*")
        
        except NoSuchElementException as e:
            logger.error("Error finding Tweet text in Twitter's HTML!")
            logger.error(e)
            # Return a failure.
            return(False)
        
        # Parse the text within the tweet.
        text = ""
        for element in textblock_children_list:
            text = text + element.text
            if element.tag_name == "img":  # Check for Emojis (which are SVG images on Twitter)
                text = text + element.get_attribute("alt")
            elif element.text == "":
                text = text + "\n" + "\n"
    
        datestring = metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
            
        # Try to download the post.
        try:
            # Try to save the post's metadata.
            if self.downloadMetadata(metadata, path_to_download_dir, tweet_number) is False:
                return(False)
            
            # Download this post.
            filename = str(tweet_number) + "__" + datestring
            with open(os.path.join(path_to_download_dir, (filename + ".txt")), 'w', encoding="utf-8") as file:
                file.write(text)
            
        # If the Screenshot flag is set, take a screenshot of the Tweet as well.
            if SCREENSHOT:
                self.screenshot(tweet, path_to_download_dir, filename)
            
            # Return a success.
            logger.info("")
            return(True)
        
        except NoSuchElementException as e:
            print("  Error downloading text from Twitter!")
            print(e)
            # Return a failure.
            return(False)
    
    
    # Downloads a post containing image/s and/or text, and its metadata.
    # Returns a Boolean, String, JSON.
    #   Boolean represents whether the download succeeded.
    #   String is the downloaded text, or None if download failed.
    #   JSON is the post metadata, or None if download failed.
    def downloadImage(self, tweet, tweet_number, metadata, path_to_download_dir, SCREENSHOT):
        try:
        # Locate the text in the Tweet.
            textblock = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")  # The dot at the start of xpath means "search the children of this element".
            textblock_children_list = textblock.find_elements(By.XPATH, "*")
        # Parse the text within the tweet.
            text = ""
            for element in textblock_children_list:
                text = text + element.text
                if element.tag_name == "img":  # Check for Emojis (which are SVG images on Twitter)
                    text = text + element.get_attribute("alt")
                elif element.text == "":
                    text = text + "\n" + "\n"
        
        except NoSuchElementException as e:
            logger.debug("No text accompanies this image post.")
            text = ""
        
        # Locate the image/s in Twitter.
        try:
            images_to_archive = []
            self.wait.until(EC.visibility_of_element_located((By.XPATH, ".//div[@data-testid='tweetPhoto']")))
            imageblock = tweet.find_elements(By.XPATH, ".//div[@data-testid='tweetPhoto']")
            for images in imageblock:
                # TODO: Save the alt text.
                #metadata["alt_text"] = str(imageblock.get_attribute("aria-label"))
                # Cannot save alt text given the current architecture.
                # Switch to an object-oriented design with a Tweet object!
                image_url = images.find_element(By.TAG_NAME, 'img').get_attribute("src")
                max_size_image_url = re.sub('(name=)\w+', "name=orig", image_url, 1)
                # Determine image type.
                image_type = re.search('(format=)\w+', image_url).group(0).split('=')[1]
                images_to_archive.append([max_size_image_url, image_type])
        
        except NoSuchElementException as e:
            logger.error("Error finding Tweet image in Twitter's HTML!")
            logger.error(e)
            # Return a failure.
            return(False)
        
        datestring = metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
        
        # Try to download the post.
        try:
            # Record the image source URLs, if given.
            if images_to_archive != None:
                image_count = 0
                for image_source_url,image_type in images_to_archive:
                    image_count += 1
                    metadata[("image_" + str(image_count) + "_url")] = str(image_source_url)
                # Record the number of images.
                metadata["number_of_images"] = str(image_count)
            
            # Try to save the post's metadata.
            if self.downloadMetadata(metadata, path_to_download_dir, tweet_number) is False:
                return(False)
            
            filename = str(tweet_number) + "__" + datestring
            
            # Download this post's text.
            if text != "":
                with open(os.path.join(path_to_download_dir, (filename + ".txt")), 'w', encoding="utf-8") as file:
                    file.write(text)
            
            # If the Screenshot flag is set, take a screenshot of the Tweet as well.
            if SCREENSHOT:
                self.screenshot(tweet, path_to_download_dir, filename)
            
            # Download this post's image/s.
            image_count = 1
            for image_source_url,image_type in images_to_archive:
                image_filename = filename + "_" + str(image_count) + "." + image_type
                if image_type == "jpg":
                    image_type = "JPEG"
                else:
                    image_type = image_type.upper()
                
                try:
                    image_content = requests.get(image_source_url).content
                    image_file = io.BytesIO(image_content)
                    image = Image.open(image_file)
                    with open(os.path.join(path_to_download_dir, image_filename), 'wb') as file:
                        image.save(file, image_type)
                except Exception as e:
                    logger.error("  Error downloading image from Twitter!")
                    logger.error(e)
                    return(False)
                
                image_count += 1
            
            # Return a success.
            return(True)
        
        except NoSuchElementException as e:
            logger.error("  Error downloading image from Twitter!")
            logger.error(e)
            # Return a failure.
            return(False)


    # Downloads a post containing a video and/or text, and its metadata.
    # Returns a Boolean, String, JSON.
    #   Boolean represents whether the download succeeded.
    #   String is the downloaded text, or None if download failed.
    #   JSON is the post metadata, or None if download failed.
    def downloadVideo(self, tweet, tweet_number, metadata, path_to_download_dir, SCREENSHOT):
        # Locate the text in the Tweet.
        try:
            textblock = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")  # The dot at the start of xpath means "search the children of this element".
            textblock_children_list = textblock.find_elements(By.XPATH, "*")
        # Parse the text within the tweet.
            text = ""
            for element in textblock_children_list:
                text = text + element.text
                if element.tag_name == "img":  # Check for Emojis (which are SVG images on Twitter)
                    text = text + element.get_attribute("alt")
                elif element.text == "":
                    text = text + "\n" + "\n"
        
        except NoSuchElementException as e:
            logger.debug("  No text accompanies this video post.")
            text = ""
        
        # Locate the video in Twitter.
        try:
            videoblock = tweet.find_element(By.XPATH, ".//div[@data-testid='videoPlayer']")
            video = videoblock.find_elements(By.XPATH, ".//video[@aria-label='Embedded video']")
            self.wait.until(EC.visibility_of(videoblock))
            
            # Locate the direct link to the Tweet on the page, by checking the datestamp link.
            date = tweet.find_element(By.TAG_NAME, 'time').text
            direct_tweet_link = tweet.find_element(By.XPATH, ".//a[@aria-label='" + date + "']").get_attribute("href")
        
        except NoSuchElementException as e:
            logger.error("Error finding Tweet video in Twitter's HTML!")
            logger.error(e)
            # Return a failure.
            return(False)
            
        datestring = metadata["date"].strftime('%Y-%m-%d_%H-%M-%S')
        
        # Try to download the post.
        try:
            # Try to save the post's metadata.
            if self.downloadMetadata(metadata, path_to_download_dir, tweet_number) is False:
                return(False)
            
            filename = str(tweet_number) + "__" + datestring
            
            # Download this post's text.
            if text != "":
                with open(os.path.join(path_to_download_dir, (filename + ".txt")), 'w', encoding="utf-8") as file:
                    file.write(text)
            
            # If the Screenshot flag is set, take a screenshot of the Tweet as well.
            if SCREENSHOT:
                self.screenshot(tweet, path_to_download_dir, filename)
            
            # Download this post's video.
            video_filename = filename + ".mp4"
            ydl_opts = {'outtmpl': os.path.join(path_to_download_dir, video_filename)}
            y_downloader = YDLScraperHelper(ydl_opts)
            if not y_downloader.download(direct_tweet_link):
                return(False)
            
            # Return a success.
            return(True)
        
        except Exception as e:
            logger.error("Error downloading video from Twitter!")
            logger.error(e)
            # Return a failure.
            return(False)
    
    
    # Download a single Tweet and its metadata.
    # Return False if the Tweet or the metadata fails to download.
    def downloadTweet(self, tweet, tweet_count, metadata, dir_path, SCREENSHOT):
        downloaded = False
        if metadata["post type"] == "text":
            logger.info("  #" + str(tweet_count) + " in current Twitter thread - text post.")
            downloaded = self.downloadText(tweet, tweet_count, metadata, dir_path, SCREENSHOT)
        elif metadata["post type"] == "image":
            logger.info("  #" + str(tweet_count) + " in current Twitter thread - image post.")
            downloaded = self.downloadImage(tweet, tweet_count, metadata, dir_path, SCREENSHOT)
        elif metadata["post type"] == "video":
            logger.info("  #" + str(tweet_count) + " in current Twitter thread - video post.")
            downloaded = self.downloadVideo(tweet, tweet_count, metadata, dir_path, SCREENSHOT)
        else:
            return downloaded
        
        return downloaded
    
    
    # Download the full data and metadata of one Tweet, ignoring Threads and replies.
    def scrapeOnlyThisTweet(self, url, tweet_count, prior_metadata, dir_path, SCREENSHOT):
    # Navigate to the requested page on Twitter.
        #print("  Scraping quote tweet URL:")
        #print("    " + url)
        self.goToPage(url)
        # Determine the Tweets to download from a Thread on a page.
        list_of_tweets_in_thread, base_tweet = self.analyzeThread()
        tweet = base_tweet
    
    # Download just the indicated post.
        # Retrieve the post's metadata from the Twitter page.
        can_never_be_base_tweet = True
        if prior_metadata == None:
            metadata = self.scrapeMetadata(tweet, url, can_never_be_base_tweet)
        else:
            metadata = prior_metadata
        
        # Determine the type of media the post contains.
        mediaType = self.determineTweetMediaContents(tweet)
        # Record the type of post.
        metadata["post type"] = mediaType
        # Attempt to download a single Tweet and its metadata.
        if not self.downloadTweet(tweet, tweet_count, metadata, dir_path, SCREENSHOT):
            return False
        
        return True
    
    
    # Download the full data and metadata of a Tweet or Thread (whichever is found).
    # Returns two values:
    #     True or False boolean, indicating a successful scrape or not.
    #     Integer quantity of posts navigated to; counting because of the Twitter post limiter.
    def scrapeFromTwitter(self, url, SCREENSHOT):
    # Reset the local count of posts viewed.
        self.posts_viewed = 0
    # Navigate to the requested page on Twitter.
        self.goToPage(url)
        
        # Check to see if the tweet has been deleted.
        if self.isTweetDeleted():
            logger.warning("  This Tweet from Twitter has been deleted!")
            return False, self.posts_viewed
        
        # Determine the Tweets to download from a Thread on a page.
        list_of_tweets_in_thread, base_tweet = self.analyzeThread()
        
    # Create a new directory to save the Thread or Tweet to.
        dir_path = self.generatePostDirectoryPath(base_tweet)
        # If the directory already exists, this Tweet (or exact slice of a Thread tree) has already been downloaded.
        if os.path.exists(dir_path):
            # Skip downloading this post.
            logger.warning("  This Tweet or Thread from Twitter has already been downloaded!")
            return False, self.posts_viewed
        else:
            # Create the post's archive directory.
            os.makedirs(dir_path)
    
    # Download each post in the Thread.
        tweet_count = 0
        queue_to_scrape_individually = []
        for tweet in list_of_tweets_in_thread:
            tweet_count += 1
            # Retrieve the post's metadata from the Twitter page.
            metadata = self.scrapeMetadata(tweet, url)
            
            # Determine if the Tweet contains a Quote-Tweet.
            # If it does, save it for later scraping.
            # (Because we must navigate off the current page to scrape quoted Tweets.)
            quoteTweetUrl = self.checkForQuoteTweets(tweet)
            if quoteTweetUrl == 'DELETED':
                metadata["quoting a tweet"] = True
                metadata["quoted tweet url"] = quoteTweetUrl
            elif quoteTweetUrl != "":
                queue_to_scrape_individually.append({"url": quoteTweetUrl, "count": tweet_count, "metadata": None})
                metadata["quoting a tweet"] = True
                metadata["quoted tweet url"] = quoteTweetUrl
                tweet_count += 1
            
            # Determine the type of media the post contains.
            mediaType = self.determineTweetMediaContents(tweet)
            # Record the type of post.
            metadata["post type"] = mediaType
            
            # If the post contains a "Show more" link, add it to the scrape individually queue.
            # Don't do this if this is the base tweet.
            is_show_more_tweet = False
            is_base_tweet = str(tweet.get_attribute("tabindex"))
            if is_base_tweet == "0":  #not the base tweet
                # Get the URL of the tweet, as we only know the base tweet URL already.
                usernameBlock = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']")
                linksInUsernameBlock = usernameBlock.find_elements(By.XPATH, ".//a[@role='link']")
                tweet_url = None
                for link in linksInUsernameBlock:
                    # There should be three links in the username block at the top of a tweet.
                    linkAddress = link.get_attribute("href")
                    if "status" in linkAddress:
                        # We are looking for the datestamp link that directly permalinks to the tweet in question.
                        tweet_url = linkAddress
                        metadata["url"] = tweet_url
                
                # Identify if this Tweet has a "Show more" link.
                try:
                    textblock = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                    showMore = textblock.find_element(By.XPATH, ".//span[starts-with(@data-testid, 'tweet-text-show-more-link-')]")
                    # Assuming it does have a "Show more" link, add it to the queue to later scrape individually.
                    queue_to_scrape_individually.append({"url": tweet_url, "count": tweet_count, "metadata": metadata})
                    #print(showMore.get_attribute("data-testid"))
                    is_show_more_tweet = True
                except Exception as e:
                    #print(e)
                    pass
            else:
                metadata["url"] = url
            
            if not is_show_more_tweet:
                # Attempt to download a single Tweet and its metadata.
                if not self.downloadTweet(tweet, tweet_count, metadata, dir_path, SCREENSHOT):
                    # Delete the post's archive directory.
                    logger.debug("Deleting the incomplete archive directory...")
                    shutil.rmtree(dir_path)
                    return False, self.posts_viewed
                
        
    # Download each Quote tweet saved for later download.
        logger.info("  Scraping queue of deferred tweets...")
        for tweet in queue_to_scrape_individually:
            self.scrapeOnlyThisTweet(tweet["url"], tweet["count"], tweet['metadata'], dir_path, SCREENSHOT)
            self.goBackAPage()
        logger.info("  ...done!")
    
    # TODO: Attempt to download the thread's metadata.
        
        return True, self.posts_viewed


class YDLLogger(object):
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        print(msg)
    
    def error(self, msg):
        print(msg)


class YDLScraperHelper:
    def __init__(self, options={}):
        self.logger = YDLLogger()
        self.options = {'format': 'best',
                        'logger': self.logger,
                        'nooverwrites':True,
                        'progress_hooks': [ydlHook],
                        'socket_timeout': 15
                        }
        if options != {}:
            self.options.update(options)
    
    
    # Trys to download the video from the given URL, as a side effect.
    # Returns True if successful, and False if not.
    def download(self, url):
        try:
            logger.debug("Downloading video with youtube-dl, URL: " + url)
            with youtube_dl.YoutubeDL(self.options) as ydl:
                ydl.download([url])
        except Exception as e:
            logger.error(e)
            return False
        
        logger.debug("Video download successful!")
        return True


"""
elem = driver.find_element(By.NAME, "q")
elem.clear()
elem.send_keys("pycon")
elem.send_keys(Keys.RETURN)
assert "No results found." not in driver.page_source
time.sleep(1)

driver.close()
"""