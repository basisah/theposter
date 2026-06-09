import random 
from googleapiclient.discovery import build
import openai
import requests
import response
from google.oauth2 import service_account
import os

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
    return response.content.text

# Returns hourly breakdown of when your followers are online
# Pick top 3 hours from today's day-of-week data
def get_best_posting_time(page_id,access_token):
    url = f"https://graph.facebook.com/{page_id}/insights"
    params = {
        'metric': 'page_impressions_by_day',
        'access_token': access_token
    }

def post_facebook():
    pass







