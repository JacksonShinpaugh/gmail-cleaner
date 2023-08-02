import streamlit as st
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())


SCOPES = ['https://mail.google.com/']
CREDENTIALS = json.loads(os.environ['CREDENTIALS'])
GMAIL_TOKEN = json.loads(os.environ['GMAIL_TOKEN'])

email = 'jackson.shinpaugh@gmail.com'


@st.cache_resource
def get_credentials():
    creds = Credentials.from_authorized_user_info(GMAIL_TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
    return creds


@st.cache_resource
def build_service():
    service = build('gmail', 'v1', credentials=creds)
    return service


@st.cache_data
def get_senders(_service):
    messages = _service.users().messages().list(userId='me').execute()

    senders = []
    for message in messages['messages']:
        message_id = message['id']
        message = _service.users().messages().get(userId='me', id=message_id, format='metadata', metadataHeaders='From').execute()
        headers = message['payload']['headers']
        senders.append(headers[0]['value'])
    
    return list(set(senders))


@st.cache_data
def search_messages(_service, query):
    result = _service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = _service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages


def delete_messages(service, query):
    messages_to_delete = search_messages(service, query)

    return service.users().messages().batchDelete(
      userId='me',
      body={
          'ids': [ msg['id'] for msg in messages_to_delete]
      }
    ).execute()
    

if __name__ == "__main__":
    st.set_page_config(page_title="Gmail Cleaner", layout='wide')
    st.title("Gmail Cleaner")

    creds = get_credentials()
    service = build_service()

    
    with st.sidebar:
        senders = get_senders(service)
        to_delete = st.multiselect('Select senders emails to delete', options=senders)

    for sender in to_delete:
        query = sender.split("<")[0]
        messages = search_messages(service, query)
        
        st.write(query)
        st.write(len(messages))
    
    # scott = search_messages(service, "Scott's Bass Lessons")
    # st.write(len(scott))

    
    # response = delete_messages(service, )
