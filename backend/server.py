import os
import json
from googleapiclient.discovery import build
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#load_dotenv()

# Initializing vader
analyzer = SentimentIntensityAnalyzer()

#API_KEY = os.getenv('API_KEY')
API_KEY = "AIzaSyAqktuR2rOSVetvOEs1zPd5281Vo8kcAbs"


# Function to fetch comments
def get_video_comments(video_id):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    comments = []
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,  # Max 100 per request
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "date": comment["publishedAt"],
                "user": comment["authorDisplayName"],
                "comment": comment["textDisplay"],
                "likes": comment["likeCount"],
                "video_id": video_id
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments

# Function to analyze comment sentiment
def analyze_comments(comments):
    for entry in comments:
        comment = entry['comment']
        sentiment = analyzer.polarity_scores(comment)
        compound_score = sentiment['compound']
        if compound_score >= 0.05:
            sentiment_category = "Positive"
        elif compound_score <= -0.05:
            sentiment_category = "Negative"
        else:
            sentiment_category = "Neutral"
        
        entry['sentiment'] = sentiment_category

    return comments

# Function to video views
def get_video_views(video_id):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    request = youtube.videos().list(
        part="statistics",
        id=video_id
    ).execute()

    views = request['items'][0]['statistics']['viewCount']
    return views

# API Endpoint
@app.get("/fetch-comments/{video_id}")
def fetch_comments(video_id: str):
    comments = get_video_comments(video_id)
    comments_with_sentiment = analyze_comments(comments)
    return {"comments": comments_with_sentiment}

@app.get("/fetch-views/{video_id}")
def fetch_views(video_id: str):
    views = get_video_views(video_id)
    return {"video_views": views}