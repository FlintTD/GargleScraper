from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import base64
import email
import logging
#from bs4 import BeautifulSoup

logger = logging.getLogger('GargleScraper')
# Define the SCOPES. If modifying it, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailAccount():
    def __init__(self, creds):
        self.creds = creds
        self.service = None
    
    def login(self):
        try:
            # Connect to the Gmail API.
            self.service = build('gmail', 'v1', credentials=self.creds)
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred logging in to Gmail: {error}')
    
    def getLabels(self):
        try:
            # Request a dict of all the labels.
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            if not labels:
                return None
            else:
                return labels

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred getting Gmail labels: {error}')
    
    # Returns a list containing all unread emails with the chosen label.
    def getUnreadMessageIds(self, label, limit):
        messages = []
        # The max_results value is the maximum number of emails which will be retrieved.
        # The API default value is 100.
        max_results = 200
        try:
            # Fetch the user profile, to determine the maximum number of emails to search.
            user_profile_query = self.service.users().getProfile(userId='me').execute()
            max_results = user_profile_query.get("messagesTotal")
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred when getting the maximum email count: {error}')
        
        # Limit the number of emails to search to the maximum provided scraping limit.
        if limit != -1:
            max_results = limit
        
        logger.debug(f"Fetching {max_results} emails from Gmail...")
        next_page_token = ""
        results_count = 500
        messagesResult = self.service.users().messages().list(  maxResults=max_results,
                                                                userId='me',
                                                                q=f'in:{label} is:unread'
                                                             ).execute()
        next_page_token = messagesResult.get('nextPageToken')
        results_count = messagesResult.get('resultSizeEstimate')
        messages.extend(messagesResult.get('messages', []))
        while results_count >= 500:
            try:
                messagesResult = self.service.users().messages().list(  maxResults=max_results,
                                                                        pageToken=next_page_token,
                                                                        userId='me',
                                                                        q=f'in:{label} is:unread'
                                                                     ).execute()
                next_page_token = messagesResult.get('nextPageToken')
                results_count = messagesResult.get('resultSizeEstimate')
                messages.extend(messagesResult.get('messages', []))
            except HttpError as error:
                # TODO(developer) - Handle errors from gmail API.
                print(f'An error occurred when getting all unread email IDs: {error}')
        
        logger.info("Gmail emails retrieved: " + str(len(messages)))
        return messages

    def getEmailFromMessageId(self, message_id):
        message = None
        
        try:
            # Get the message itself from Gmail, using the message ID.
            message = self.service.users().messages().get(userId='me', id=message_id['id']).execute()
            # message['snippet'] is the body of the message.
            return message
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred when getting an email using an email ID: {error}')
        
        return message
    
    def getEmailBodyFromEmail(self, message):
        return message['snippet']
    
    #def markEmailAsRead(self, message_id):
    

    
"""
    def getEmails():
        # Connect to the Gmail API
        service = build('gmail', 'v1', credentials=self.creds)
      
        # request a list of all the messages
        result = service.users().messages().list(userId='me').execute()
      
        # We can also pass maxResults to get any number of emails. Like this:
        # result = service.users().messages().list(maxResults=200, userId='me').execute()
        messages = result.get('messages')
      
        # messages is a list of dictionaries where each dictionary contains a message id.
      
        # iterate through all the messages
        for msg in messages:
            # Get the message from its id
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
      
            # Use try-except to avoid any Errors
            try:
                # Get value of 'payload' from dictionary 'txt'
                payload = txt['payload']
                headers = payload['headers']
      
                # Look for Subject and Sender Email in the headers
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']
      
                # The Body of the message is in Encrypted format. So, we have to decode it.
                # Get the data and decode it with base 64 decoder.
                parts = payload.get('parts')[0]
                data = parts['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
      
                # Now, the data obtained is in lxml. So, we will parse 
                # it with BeautifulSoup library
                soup = BeautifulSoup(decoded_data , "lxml")
                body = soup.body()
      
                # Printing the subject, sender's email and message
                print("Subject: ", subject)
                print("From: ", sender)
                print("Message: ", body)
                print('\n')
            except:
                pass
  
  
getEmails()
"""