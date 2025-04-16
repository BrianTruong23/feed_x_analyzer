import os
import tweepy
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.parser import parse

class XClient:
    def __init__(self):
        load_dotenv()
        
        # Load credentials from .env
        bearer_token = os.getenv('X_BEARER_TOKEN')
        access_token = os.getenv('X_ACCESS_TOKEN')
        access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        api_key = os.getenv('X_API_KEY')
        api_key_secret = os.getenv('X_API_KEY_SECRET')
        
        # Initialize client
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_key_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True  # Let tweepy handle rate limits
        )
        
        # Track API requests
        self.request_timestamps = {
            'home_timeline': [],
            'user_tweets': [],
            'user_info': []
        }
        
        # Rate limits for different endpoints (requests per 15-minute window)
        self.RATE_LIMITS = {
            'home_timeline': 15,
            'user_tweets': 100,
            'user_info': 100
        }
        self.WINDOW_SIZE = 15 * 60  # 15 minutes in seconds

    def _check_rate_limit(self, endpoint):
        """Check if we can make a request within rate limits"""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.WINDOW_SIZE)
        
        # Clean up old timestamps
        self.request_timestamps[endpoint] = [
            ts for ts in self.request_timestamps[endpoint]
            if ts > window_start
        ]
        
        # Check if we've hit the limit
        if len(self.request_timestamps[endpoint]) >= self.RATE_LIMITS[endpoint]:
            wait_time = (self.request_timestamps[endpoint][0] + timedelta(seconds=self.WINDOW_SIZE) - current_time).total_seconds()
            if wait_time > 0:
                print(f"Rate limit reached for {endpoint}. Waiting {int(wait_time)} seconds...")
                time.sleep(wait_time)
                self.request_timestamps[endpoint] = []
        
        # Add new timestamp
        self.request_timestamps[endpoint].append(current_time)
        
        # Add a small delay between requests to be nice to the API
        time.sleep(2)

    def get_feed_users_posts(self, max_users=2, posts_per_user=2):
        """
        Fetch posts from users that appear in the authenticated user's home timeline.
        """
        try:
            print("Fetching home timeline...")
            self._check_rate_limit('home_timeline')
            
            # Make single home timeline request with minimum needed results
            timeline = self.client.get_home_timeline(
                max_results=5,
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                user_fields=['username', 'name', 'description']
            )
            
            if not timeline.data:
                print("No timeline data found")
                return []

            # Get unique users from the timeline
            unique_users = {}
            for tweet in timeline.data:
                if len(unique_users) >= max_users:
                    break
                if tweet.author_id not in unique_users:
                    unique_users[tweet.author_id] = {
                        'author_id': tweet.author_id,
                        'posts': []
                    }

            print(f"Found {len(unique_users)} unique users")
            
            # For each unique user, fetch their recent posts
            all_user_posts = []
            for i, user_id in enumerate(unique_users.keys(), 1):
                try:
                    print(f"Fetching posts for user {i} of {len(unique_users)}...")
                    
                    # Get user info
                    self._check_rate_limit('user_info')
                    user_info = self.client.get_user(id=user_id)
                    if not user_info.data:
                        continue
                    
                    # Get user's recent tweets
                    self._check_rate_limit('user_tweets')
                    user_tweets = self.client.get_users_tweets(
                        id=user_id,
                        max_results=posts_per_user,
                        tweet_fields=['created_at', 'public_metrics', 'text'],
                        user_fields=['username', 'name', 'description']
                    )
                    
                    if user_tweets.data:
                        # Format user's posts
                        formatted_posts = []
                        for tweet in user_tweets.data:
                            formatted_posts.append({
                                'id': tweet.id,
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'metrics': tweet.public_metrics
                            })
                        
                        # Add user and their posts to the result
                        all_user_posts.append({
                            'user_id': user_id,
                            'username': user_info.data.username,
                            'name': user_info.data.name,
                            'description': user_info.data.description,
                            'posts': formatted_posts
                        })
                        
                except Exception as e:
                    print(f"Error fetching tweets for user {user_id}: {str(e)}")
                    continue
            
            return all_user_posts
            
        except Exception as e:
            print(f"Error fetching feed users' posts: {str(e)}")
            return []

    def get_feed_summary(self):
        """Get a structured summary of posts from users in the feed."""
        print("Starting feed analysis...")
        users_posts = self.get_feed_users_posts()
        
        if not users_posts:
            return {
                'status': 'error',
                'message': 'No posts found or error occurred'
            }
        
        print(f"Successfully fetched posts from {len(users_posts)} users")
        
        # Get the overall time range
        all_posts = []
        for user in users_posts:
            all_posts.extend(user['posts'])
        
        # Sort posts by creation time
        all_posts.sort(key=lambda x: x['created_at'])
        
        return {
            'status': 'success',
            'user_count': len(users_posts),
            'total_posts': len(all_posts),
            'users_data': users_posts,
            'time_range': {
                'oldest': all_posts[0]['created_at'] if all_posts else None,
                'newest': all_posts[-1]['created_at'] if all_posts else None
            }
        }

    def get_user_recent_posts(self, username):
        """
        Fetch 2 recent posts from a specific user (rate-limit friendly).

        Args:
            username (str): The Twitter username without @

        Returns:
            dict: Status and user posts data
        """
        try:
            print(f"\nLooking up user ID for @{username}...")

            # Single API call to get user ID and recent tweets in sequence
            user = self.client.get_user(username=username)
            if not user.data:
                return {
                    'status': 'error',
                    'message': f'User @{username} not found.'
                }

            user_id = user.data.id
            print(f"User found: {user.data.name} (@{user.data.username})")

            # Optional delay to prevent rapid successive calls
            time.sleep(1)

            # Fetch only 5 recent tweets (limit to what's needed)
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=5,
                tweet_fields=['created_at', 'public_metrics', 'text']
            )

            if not tweets.data:
                return {
                    'status': 'error',
                    'message': f'No tweets found for @{username}'
                }

            formatted_posts = [{
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat(),
                'metrics': tweet.public_metrics
            } for tweet in tweets.data]

            return {
                'status': 'success',
                'user_info': {
                    'id': user_id,
                    'username': user.data.username,
                    'name': user.data.name,
                },
                'posts': formatted_posts
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error fetching posts: {str(e)}'
            }


def test_user_posts():
    """Test function to fetch and print posts from a specific user"""
    client = XClient()
    
    # Replace with the username you want to test (without @ symbol)
    test_username = "Riazi_Cafe_en"
    
    result = client.get_user_recent_posts(test_username)
    
    if result['status'] == 'success':
        print(f"\nSuccessfully fetched posts from {result['user_info']['name']} (@{result['user_info']['username']})")
        print("\nRecent posts:")
        for i, post in enumerate(result['posts'], 1):
            print(f"\n{i}. Posted at: {post['created_at']}")
            print(f"Text: {post['text']}")
            print("Metrics:", post['metrics'])
    else:
        print(f"\nError: {result['message']}")

if __name__ == "__main__":
    test_user_posts()
    