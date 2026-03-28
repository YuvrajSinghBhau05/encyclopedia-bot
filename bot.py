import tweepy
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import json

# Twitter API credentials from environment variables
CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Google Sheets setup
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # Extract from URL
GOOGLE_CREDS = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet

def post_tweet(content):
    client = tweepy.Client(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    response = client.create_tweet(text=content)
    return response

def check_and_post():
    sheet = get_sheet()
    records = sheet.get_all_records()
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    for idx, row in enumerate(records, start=2):  # start=2 because row 1 is header
        if row['status'] == 'queued':
            scheduled = datetime.strptime(row['scheduled_time'], '%Y-%m-%d %H:%M')
            scheduled = ist.localize(scheduled)
            
            # Check if it's time to post (within 5 minute window)
            time_diff = (now - scheduled).total_seconds() / 60
            
            if -5 <= time_diff <= 5:
                try:
                    print(f"Posting: {row['content'][:50]}...")
                    post_tweet(row['content'])
                    sheet.update_cell(idx, 4, 'posted')  # Update status column
                    print(f"✓ Posted successfully")
                    return True
                except Exception as e:
                    print(f"Error posting: {e}")
                    sheet.update_cell(idx, 4, f'error: {str(e)[:50]}')
                    return False
    
    print("No posts scheduled for this time")
    return False

if __name__ == "__main__":
    check_and_post()
