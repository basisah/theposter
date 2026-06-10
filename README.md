# theposter
AI Agent that posts on your socials using photos from google drive and generating captions in the best timeframe

# What it does

1. Reads images from a Google Drive folder organized into category subfolders
(e.g. Client showcase, Product Display, New Looks, Mela engagement).
2. Picks images for the next 7 days, 3 posts per day.
3. Generates an engagement-focused caption for each, based on what's in the photo.
4. Schedules each post on the page at preset best times (Bangladesh / UTC+6).

Scheduled posts appear in Meta Business Suite → Planner, where you review,
edit, or delete them before they go live.
# Install — step by step
Step 1. Get the code
git clone https://github.com/basisah/theposter.git
cd theposter
Step 2. (Recommended) Create and activate a virtual environment
python3 -m venv posteragent
source posteragent/bin/activate
Step 3. Install the dependencies
pip install google-api-python-client google-auth openai requests python-dotenv
Step 4. Add your Google key
Put your service_account.json (the Google Cloud service account key) in the
project folder. The Drive folder must be shared with the service account's
email address (Viewer access is enough).
Step 5. Create your .env file
In the project folder, make a file named .env with these four lines:
OPENAI_API_KEY=sk-...
FACEBOOK_ACCESS_TOKEN=your_long_lived_PAGE_token
FACEBOOK_PAGE_ID=your_page_id
GOOGLE_DRIVE_FOLDER_ID=the_string_from_the_folder_url

The Facebook token must be a long-lived Page token (not a User token).
Check it at developers.facebook.com/tools/debug/accesstoken — it should show
the page name and ~2 months until expiry. Renew it roughly every 60 days.

Step 6. Prepare the Drive folder
Inside the main Drive folder, make subfolders by category (e.g. Client showcase,
Product Display). Put .jpg images inside them — not .heic. Name files
usefully, e.g. client : Basisah.jpg or dress: green farsi salwar.jpg; the
caption uses these hints.
That's the setup. You only do this once.

# Run — step by step
Step 1. Preview first (nothing gets posted)
Open poster.py and make sure this line near the top says:
pythonDRY_RUN = True
Then run:
python3 poster.py
This prints the chosen images, captions, and schedule times without posting.
Read through the captions and check they look right.

Step 2. Schedule for real
When you're happy with the preview, change the line to:
pythonDRY_RUN = False
and run again:
python3 poster.py
This schedules the posts.

Step 3. Confirm in the Planner
Go to business.facebook.com → Planner (or Content → Posts & reels → Scheduled).
Your posts should appear there. Delete any duplicates or ones you don't want
before they publish.

# Settings you can change
In poster.py, near the top:

BEST_TIMES — the posting hours per weekday (Bangladesh local time).
DAYS_AHEAD — how many days to schedule ahead (default 7).
DRY_RUN — True to preview, False to actually schedule.


# Notes

More photos in Drive = more variety. With only a few images the same ones
repeat across slots.
Nothing posts instantly — everything is scheduled, so the Planner is your
safety check before anything goes public.
If the Facebook token expires, posting fails with an "access token expired"
error. Regenerate a long-lived Page token and update .env.
.env and service_account.json hold secrets — keep them out of git
(they're in .gitignore).
