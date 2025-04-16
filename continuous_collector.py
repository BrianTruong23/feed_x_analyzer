import os
import time
import json
import sys
from datetime import datetime, timedelta
from x_client import XClient
from gemini_analyzer import GeminiAnalyzer
from email_sender import EmailSender

class PostCollector:
    def __init__(self, collection_file="collected_posts.json", target_count=50):
        self.collection_file = collection_file
        self.target_count = target_count
        self.x_client = XClient()
        self.analyzer = GeminiAnalyzer()
        self.email_sender = EmailSender()
        self.start_time = None
        self.MAX_RUNTIME = 2 * 60 * 60  # 2 hours in seconds
        
        # Initialize or load existing collection
        self.collected_posts = self.load_collection()
        
    def load_collection(self):
        """Load existing collection or create new one"""
        if os.path.exists(self.collection_file):
            try:
                with open(self.collection_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'users_data': [], 'total_posts': 0}
        return {'users_data': [], 'total_posts': 0}
    
    def save_collection(self):
        """Save current collection to file"""
        with open(self.collection_file, 'w', encoding='utf-8') as f:
            json.dump(self.collected_posts, f, indent=2, ensure_ascii=False)
            
    def merge_new_posts(self, new_users_data):
        """Merge new posts with existing collection"""
        existing_users = {user['user_id']: user for user in self.collected_posts['users_data']}
        
        for new_user in new_users_data:
            if new_user['user_id'] in existing_users:
                # Add only new posts from this user
                existing_posts_ids = {post['id'] for post in existing_users[new_user['user_id']]['posts']}
                new_posts = [post for post in new_user['posts'] if post['id'] not in existing_posts_ids]
                existing_users[new_user['user_id']]['posts'].extend(new_posts)
            else:
                # Add new user and their posts
                self.collected_posts['users_data'].append(new_user)
                
        # Update total posts count
        self.collected_posts['total_posts'] = sum(len(user['posts']) for user in self.collected_posts['users_data'])
        
    def should_analyze(self):
        """Check if we've reached the target post count"""
        return self.collected_posts['total_posts'] >= self.target_count

    def check_timeout(self):
        """Check if we've exceeded the maximum runtime"""
        if self.start_time and (datetime.now() - self.start_time).total_seconds() >= self.MAX_RUNTIME:
            print("\nReached maximum runtime of 2 hours. Performing final analysis...")
            if self.collected_posts['total_posts'] > 0:
                self.run_analysis()
            print("\nExiting after 2 hours of operation.")
            sys.exit(0)  # Clean exit after 2 hours
        
    def run_analysis(self):
        """Run analysis on collected posts and send email"""
        print(f"\nAnalyzing {self.collected_posts['total_posts']} posts...")
        
        # Add time range to collection
        all_posts = []
        for user in self.collected_posts['users_data']:
            all_posts.extend(user['posts'])
        
        if not all_posts:
            print("No posts to analyze")
            return
            
        all_posts.sort(key=lambda x: x['created_at'])
        self.collected_posts['time_range'] = {
            'oldest': all_posts[0]['created_at'],
            'newest': all_posts[-1]['created_at']
        }
        
        # Run analysis
        analysis_results = self.analyzer.analyze_feed_data(self.collected_posts)
        
        if analysis_results['status'] == 'success':
            # Send email
            recipient_email = "truongthoithang@gmail.com"
            print(f"Sending analysis to {recipient_email}...")
            self.email_sender.send_analysis(recipient_email, analysis_results)
            
            # Archive current collection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = f"archive_posts_{timestamp}.json"
            os.rename(self.collection_file, archive_file)
            print(f"Archived posts to {archive_file}")
            
            # Reset collection
            self.collected_posts = {'users_data': [], 'total_posts': 0}
            self.save_collection()
        else:
            print(f"Analysis failed: {analysis_results['message']}")
            # Save current state in case of failure
            error_file = f"error_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_posts, f, indent=2, ensure_ascii=False)
            print(f"Saved current state to {error_file}")
    
    def run_collection_loop(self, interval_minutes=15):
        """Run continuous collection loop"""
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(hours=2)
        
        print(f"Starting continuous collection at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Will stop at {end_time.strftime('%Y-%m-%d %H:%M:%S')} (2 hours)")
        print(f"Checking for new posts every {interval_minutes} minutes")
        print(f"Current collection has {self.collected_posts['total_posts']} posts")
        
        try:
            while True:
                try:
                    # Check timeout - will exit after 2 hours
                    self.check_timeout()
                    
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching new posts...")
                    remaining_time = timedelta(seconds=int(self.MAX_RUNTIME - (datetime.now() - self.start_time).total_seconds()))
                    print(f"Time remaining until shutdown: {str(remaining_time)}")
                    
                    # Get new posts
                    feed_data = self.x_client.get_feed_summary()
                    if feed_data['status'] == 'success':
                        # Merge new posts
                        self.merge_new_posts(feed_data['users_data'])
                        self.save_collection()
                        
                        print(f"Total posts collected: {self.collected_posts['total_posts']}")
                        
                        # Check if we should run analysis
                        if self.should_analyze():
                            self.run_analysis()
                    else:
                        print(f"Failed to fetch posts: {feed_data['message']}")
                    
                    # Wait for next collection
                    print(f"Waiting {interval_minutes} minutes before next collection...")
                    time.sleep(interval_minutes * 60)
                    
                except Exception as e:
                    print(f"\nError in collection loop: {str(e)}")
                    if self.collected_posts['total_posts'] > 0:
                        print("Running analysis on collected posts before retry...")
                        self.run_analysis()
                    time.sleep(300)  # Wait 5 minutes before retry
                    
        except KeyboardInterrupt:
            print("\nCollection stopped by user")
            if self.collected_posts['total_posts'] > 0:
                print("Running final analysis before exit...")
                self.run_analysis()
        finally:
            runtime = datetime.now() - self.start_time
            print(f"\nCollection ended. Total runtime: {str(runtime)}")
            print("Script completed successfully.")
            sys.exit(0)

def main():
    collector = PostCollector()
    collector.run_collection_loop()

if __name__ == "__main__":
    main() 