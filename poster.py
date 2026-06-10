from datetime import datetime, timedelta, timezone
from fileinput import filename
import random
import time
from xmlrpc import client 
import requests
from openai import OpenAI
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import io
from googleapiclient.http import MediaIoBaseDownload
import base64


load_dotenv()
 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FB_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

BEST_TIMES = {
    0: [8, 13, 21],   # Monday
    1: [8, 13, 21],   # Tuesday
    2: [8, 14, 21],   # Wednesday
    3: [8, 13, 22],   # Thursday
    4: [11, 15, 22],  # Friday (weekend in BD — Fri/Sat — people up later)
    5: [10, 14, 22],  # Saturday
    6: [9, 13, 21],   # Sunday
}

DAYS_AHEAD = 7
BD_TZ = timezone(timedelta(hours=6))  # Bangladesh UTC+6
# man in the loop  
# Set to True to show the selected image and caption to approve without posting to fb
DRY_RUN = False


SERVICE_ACCOUNT_FILE = "service_account.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

#function to get acess to the google drive folders
def get_google_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES
    )
    return build('drive', 'v3', credentials=creds)

#build the bunch of images from the google drive folder and subfolders into a pool to pick from
def build_image_pool(google_drive, folder_id):
    pool = []
    subfolders = list_subfolders(google_drive, folder_id)
    if not subfolders:
        raise RuntimeError(f"No subfolders found in Drive folder {folder_id}")
    for sub in subfolders:
        for img in list_images(google_drive, sub["id"]):
            pool.append({"category": sub["name"], "file_id": img["id"], "name": img["name"]})
    if not pool:
        raise RuntimeError("Found subfolders but no images inside them.")
    return pool

#function to download the image from google drive using the file id and save it to a local path
def download_image(google_drive, file_id, dest_path):
    request = google_drive.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return dest_path

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
        f"'{folder_id}' in parents "
        "and mimeType contains 'image/' "
        "and trashed = false"
    )
    res = google_drive.files().list(q=q, fields="files(id, name)").execute()
    return res.get("files", [])

#function to download the image bytes from google drive using the file id
def download_image_bytes(google_drive, file_id):
    request = google_drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()

# Function to pick random image from list of google drive subfolders
def pick_image(google_drive, folder_id):
    subfolders = list_subfolders(google_drive, folder_id)
    selected_folder = random.choice(subfolders)
    images = list_images(google_drive, selected_folder['id'])
    selected_image = random.choice(images)
    return selected_image

#generates caption for the image using openai's language model
def generate_caption(client, category, image_bytes, filename):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    name_hint = os.path.splitext(filename)[0]  # filename without .jpg

    prompt = (
        f"You write Facebook captions for 'Trendy Design by Shila Noor', a South "
        f"Asian fashion boutique with a mostly Bangladeshi audience. This photo is "
        f"in the '{category}' category. Look carefully at the image and name the EXACT garment type you see "
        f"(salwar kameez, saree, lehenga, kurti, etc.) — do not use vague words "
        f"like 'ensemble' or 'outfit'. Describe the real fabric and colours. "
        f"Do not invent details that aren't visible. "
        f"If '{name_hint}' looks like a person's name, you may use it as the client's "
        f"name; if it looks like a random filename or code, do NOT use it and don't "
        f"mention any name. "
        f"Write ONE caption optimized for engagement: a short scroll-stopping hook, "
        f"warm and culturally resonant, ending with a question that invites comments, "
        f"plus 3-5 relevant hashtags. Under 60 words. Return only the caption."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()

#function to calculate the unix timestamp for scheduling the facebook post based on the day offset and local hour
def scheduled_unix(day_offset, hour_local):
    target = (datetime.now(BD_TZ) + timedelta(days=day_offset)).replace(
        hour=hour_local, minute=0, second=0, microsecond=0
    )
    return int(target.timestamp())
 

# post the photo as scheduled on facebook using the facebook graph api
def schedule_photo_post(image_path, caption, publish_unix):
    url = f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as img:
        files = {"source": img}
        data = {
            "caption": caption,
            "published": "false",
            "scheduled_publish_time": str(publish_unix),
            "access_token": FB_TOKEN,
        }
        r = requests.post(url, files=files, data=data, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Facebook error {r.status_code}: {r.text}")
    return r.json()
 
 

def main():
    missing = [
        k
        for k, v in {
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "FACEBOOK_ACCESS_TOKEN": FB_TOKEN,
            "FACEBOOK_PAGE_ID": FB_PAGE_ID,
            "GOOGLE_DRIVE_FOLDER_ID": DRIVE_FOLDER_ID,
        }.items()
        if not v
    ]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")
 
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    drive = get_google_drive_service()
 
    print("Building image pool from Drive...")
    pool = build_image_pool(drive, DRIVE_FOLDER_ID)
    print(f"  found {len(pool)} images across categories.")
 
    os.makedirs("tmp", exist_ok=True)
    used_ids = set()
 
    for day in range(1, DAYS_AHEAD + 1):
        weekday = (datetime.now(BD_TZ) + timedelta(days=day)).weekday()
        hours = BEST_TIMES[weekday]
 
        # pick 3 distinct images for the day, avoiding repeats where possible
        available = [p for p in pool if p["file_id"] not in used_ids]
        if len(available) < len(hours):
            # ran out of fresh images; allow reuse
            available = pool
        picks = random.sample(available, len(hours))
 
        for slot, (img, hour) in enumerate(zip(picks, hours)):
            used_ids.add(img["file_id"])
            caption = generate_caption(openai_client, img["category"], image_bytes=download_image_bytes(drive, img["file_id"]), filename=img["name"])
            when = scheduled_unix(day, hour)
            when_str = datetime.fromtimestamp(when, BD_TZ).strftime("%Y-%m-%d %H:%M BD")
            print(f"\nDay +{day} slot {slot+1}  [{img['category']}]  {img['name']}")
            print(f"  schedule: {when_str}")
            print(f"  caption : {caption}")
 
            if DRY_RUN:
                print("  DRY_RUN: not posting.")
                continue
 
            local_path = download_image(drive, img["file_id"], f"tmp/{img['name']}")
            result = schedule_photo_post(local_path, caption, when)
            print(f"  posted id: {result.get('id') or result.get('post_id')}")
            time.sleep(2)  # be gentle with the API
 
    print("\nDone.")
    if DRY_RUN:
        print("This was a DRY RUN. Set DRY_RUN = False to actually schedule posts.")
 
 
if __name__ == "__main__":
    main()
 


\




