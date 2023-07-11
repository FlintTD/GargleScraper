from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import os
import logging

logger = logging.getLogger('GargleScraper')


def get_twitter_credentials() -> dict:
    working_dir = os.path.dirname(__file__)
    relative_path_to_creds = "Credentials/twitter_credentials.txt"
    path_to_creds = os.path.join(working_dir, relative_path_to_creds)
    credentials = dict()
    
    f = open(path_to_creds, "r")
    for line in f:
        try:
            key, value = line.split(": ")
        except ValueError:
            print('Add your email, username, and password into the Twitter credentials file!')
            f.close() 
            sys.exit()
        credentials[key] = value.rstrip(" \n")
    
    if len(credentials[key]) == 0:
        raise ValueError('Add your email, username, and password into the Twitter credentials file!')
        f.close()
        sys.exit()
    
    f.close()
    return credentials


def get_gmail_credentials() -> dict:
    # Define the SCOPES. If modifying it, delete the token.pickle file.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    # Define working directories.
    working_dir = os.path.dirname(__file__)
    relative_path_to_gmail_uat = "Credentials/gmail_token.json"
    path_to_gmail_uat = os.path.join(working_dir, relative_path_to_gmail_uat)
    relative_path_to_google_secrets = "Credentials/google_secrets.json"
    path_to_google_secrets = os.path.join(working_dir, relative_path_to_google_secrets)
    # Prep an empty variable for incoming creds.
    user_access_token = None
    
    # Variable user_access_token will store the user access token.
    # If no valid token found, we will create one.
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    # Check if gmail user access token exists, in form of gmail_token.json.
    if os.path.exists(path_to_gmail_uat):
        # Read the user access token from the file.
        user_access_token = Credentials.from_authorized_user_file(path_to_gmail_uat, SCOPES)
        logger.debug("Gmail user access token found!")

    # If there is no (valid) user access token available, ask the user to log in.
    if not user_access_token or not user_access_token.valid:
        # If there is a user access token, but it expired, ask the user to log in again.
        if user_access_token and user_access_token.expired and user_access_token.refresh_token:
            # Open a browser to a Google login page.
            # If you cannot authorize yourself as a valid user via this browser screen,
            # the program will freeze and Ctrl + C won't be able to escape you!
            user_access_token.refresh(Request())
        else:
            if os.path.exists(path_to_google_secrets):
                flow = InstalledAppFlow.from_client_secrets_file(path_to_google_secrets, SCOPES)
                user_access_token = flow.run_local_server(port=0)
            else:
                # If there are no google secrets available, ask the user to log in.
                print("No Gmail user access token or Google secrets found! Check the README to see how to provide Google secrets.")
                sys.exit()
  
        # Save the user access token in gmail_token.json file for the next run.
        with open(path_to_gmail_uat, 'w') as token:
            token.write(user_access_token.to_json())
    return user_access_token