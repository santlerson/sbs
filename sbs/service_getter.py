from __future__ import print_function
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.transport.requests as requests

import pkg_resources

from sbs.config import *

creds = None



# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

# If modifying these scopes, delete the file token.pickle.
def get_service(config: Config):
    SCOPES = ["https://www.googleapis.com/auth/drive.appdata",
              "https://www.googleapis.com/auth/drive.file"]
    token_file = os.path.join(config.credentials_dir, "token.pickle")
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    else:
        creds = None
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(requests.Request())
        else:
            stream: TextIO = pkg_resources.resource_stream(__name__, 'credentials.json')
            client_config = json.loads(stream.read())
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)
