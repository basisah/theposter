import random 
from dotenv import load_dotenv
from googleapiclient.discovery import build
import openai
import requests
from google.oauth2 import service_account
import os

load_dotenv()
 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FB_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
 

SERVICE_ACCOUNT_FILE = "service_account.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

#function to get acess to the google drive folders
def get_google_drive_service():
    creds =  creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES
    )
    return build('drive', 'v3', credentials=creds)

#function to return all the images in a google drive folder
def list_subfolders(google_drive, folder_id):
    q = (
        f"'{folder_id}' in parents "          # was parent_id
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    res = google_drive.files().list(q=q, fields="files(id, name)").execute()  # was drive
    return res.get("files", [])

#function to return all the images in the google drive folder
def list_images(google_drive, folder_id):
    q = (
        f "'{folder_id}' in parents "          # was parent_id
        "and mimeType contains 'image/' "
        "and trashed = false"
    )
    res = google_drive.files().list(q=q, fields="files(id, name)").execute()
    return res.get("files", [])

# Function to pick random image from list of google drive subfolders
def pick_image(google_drive, folder_id):
    subfolders = list_subfolders(google_drive, folder_id)
    selected_folder = random.choice(subfolders)
    images = list_images(google_drive, selected_folder['id'])
    selected_image = random.choice(images)
    return selected_image

#generates caption for the image using openai's language model
def gen_caption(image_url, category):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Generate a caption for an image in the {category} category."}
        ]
    )
    return response.choices[0].message.content

# Returns hourly breakdown of when your followers are online
# Pick top 3 hours from today's day-of-week data
def get_best_posting_time(page_id,access_token):
    url = f"https://graph.facebook.com/{page_id}/insights"
    params = {
        'metric': 'page_fans_online_per_day',
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    return response.json()


Best_time = {
    0: [9, 13, 20],   # Monday
    1: [8, 12, 21],   # Tuesday
    2: [9, 14, 20],   # Wednesday
    3: [8, 13, 21],   # Thursday
    4: [11, 15, 21],  # Friday
    5: [10, 15, 22],  # Saturday
    6: [11, 14, 21],  # Sunday
}


def post_facebook():
    pass







