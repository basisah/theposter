import random 
from googleapiclient.discovery import build
import anthropic
import requests


# Function to pick random image from list of google drive subfolders
def pick_image(google_drive, folder_id):
    subfolders = list_subfolders(google_drive, folder_id)
    selected_folder = random.choice(subfolders)
    images = list_images(google_drive, selected_folder['id'])
    selected_image = random.choice(images)
    return selected_image

def gen_caption(image_url, category):
    client = anthropic.Client()
    response = client.message.create()

    return response.content.text

# Returns hourly breakdown of when your followers are online
# Pick top 3 hours from today's day-of-week data
def get_best_posting_time(page_id,access_token):
    url = f"https://graph.facebook.com/{page_id}/insights"
    params = {
        'metric': 'page_impressions_by_day',
        'access_token': access_token
    }
    pass

def post_facebook():
    pass







