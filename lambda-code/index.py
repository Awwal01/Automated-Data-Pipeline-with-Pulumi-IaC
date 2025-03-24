import json
import boto3
import requests
from datetime import datetime
import os

# Initialize S3 client
s3 = boto3.client('s3')

# Schema for Hacker News stories
def validate_story(item):
    """
    Validate and enforce schema for a Hacker News story.
    """
    time_readable = datetime.fromtimestamp(item.get("time")).strftime("%Y-%m-%d %H:%M:%S") if item.get("time") else None

    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "score": item.get("score"),
        "time": item.get("time"),
        "time_readable": time_readable,
        "by": item.get("by"),
        "descendants": item.get("descendants"),
    }

def fetch_hn_data(endpoint):
    """
    Fetch data from Hacker News API.
    """
    url = f"https://hacker-news.firebaseio.com/v0/{endpoint}.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def upload_to_s3(bucket_name, data, key):
    """
    Upload data to S3 bucket.
    """
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(data, indent=2))

def lambda_handler(event, context):
    # Configuration
    bucket_name = os.environ.get("BUCKET_NAME")  # Replace with your S3 bucket name
    endpoints = ["topstories", "newstories", "beststories"]  # API endpoints to fetch

    try:
        for endpoint in endpoints:
            # Fetch data from Hacker News API
            item_ids = fetch_hn_data(endpoint)

            # Fetch details for each item and enforce schema
            items = []
            for item_id in item_ids[:10]:  # Limit to 10 items for testing
                item = fetch_hn_data(f"item/{item_id}")
                if item and item.get("type") == "story":  # Only process stories
                    validated_item = validate_story(item)
                    items.append(validated_item)

            # Generate a unique key for S3 (e.g., timestamp + endpoint)
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            key = f"processed/{endpoint}/{timestamp}.json"

            # Upload data to S3
            upload_to_s3(bucket_name, items, key)
            print(f"Uploaded {endpoint} data to S3: {key}")

        return {
            "statusCode": 200,
            "body": json.dumps("Data extraction and upload successful!")
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps("Data extraction failed!")
        }
