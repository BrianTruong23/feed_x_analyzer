import os
import tweepy
from dotenv import load_dotenv

# Load API credentials from .env
load_dotenv()
client = tweepy.Client(
    bearer_token=os.getenv('X_BEARER_TOKEN'),
    consumer_key=os.getenv('X_API_KEY'),
    consumer_secret=os.getenv('X_API_KEY_SECRET'),
    access_token=os.getenv('X_ACCESS_TOKEN'),
    access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET'),
    wait_on_rate_limit=True  # prevents rate limit errors
)

def get_user_recent_posts(username, count=5):
    try:
        print(f"Looking up user ID for @{username}...")
        user_response = client.get_user(username=username)
        user_id = user_response.data.id

        print(f"User found: {user_response.data.name} (@{username})")

        # Fetch up to 5 recent tweets (minimum allowed is 5)
        tweets_response = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=["created_at", "text"]
        )

        tweets = tweets_response.data or []
        print(f"\n{len(tweets)} Recent Posts by @{username}:")
        for i, tweet in enumerate(tweets, 1):
            print(f"\n[{i}] {tweet.created_at}: {tweet.text}")

        return tweets

    except tweepy.TooManyRequests:
        print("Rate limit hit! Try again later.")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
get_user_recent_posts("Riazi_Cafe_en")
