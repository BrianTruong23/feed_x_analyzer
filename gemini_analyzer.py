import os
import google.generativeai as genai
from dotenv import load_dotenv
from x_client import XClient

class GeminiAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Configure the Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Make sure we're using a supported model
        try:
            self.model = genai.GenerativeModel('gemini-2.5-pro')
        except Exception as e:
            print(f"Error initializing Gemini model, trying alternative model...")
            try:
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Failed to initialize Gemini model: {str(e)}")
                raise e
        
        self.x_client = XClient()

    def analyze_feed(self):
        """
        Fetch and analyze posts from users in the X feed using Google Gemini.
        
        Returns:
            dict: Analysis results including summary and insights
        """
        # Get feed data
        feed_data = self.x_client.get_feed_summary()
        
        if feed_data['status'] != 'success':
            return {
                'status': 'error',
                'message': 'Failed to fetch X feed data'
            }

        return self.analyze_feed_data(feed_data)

    def analyze_feed_data(self, feed_data):
        """
        Analyze provided feed data using Google Gemini.
        
        Args:
            feed_data (dict): Feed data containing users and their posts
            
        Returns:
            dict: Analysis results including summary and insights
        """
        # Prepare prompt for Gemini
        prompt = self._create_analysis_prompt(feed_data)
        
        try:
            # Get Gemini's analysis
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 2048,
                    'top_p': 0.8,
                    'top_k': 40
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            )
            
            return {
                'status': 'success',
                'analysis': response.text,
                'user_count': len(feed_data['users_data']),
                'total_posts': feed_data['total_posts'],
                'time_range': feed_data['time_range']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error during Gemini analysis: {str(e)}'
            }

    def _create_analysis_prompt(self, feed_data):
        """
        Create a detailed prompt for Gemini based on the feed data.
        
        Args:
            feed_data (dict): Feed data containing users and their posts
            
        Returns:
            str: Formatted prompt for Gemini
        """
        users_data = feed_data['users_data']
        time_range = feed_data['time_range']
        
        prompt = f"""You are an expert social media analyst. Please analyze this collection of X (Twitter) posts and provide insights:

Time Range: From {time_range['oldest']} to {time_range['newest']}
Number of Users Analyzed: {len(users_data)}
Total Posts Analyzed: {feed_data['total_posts']}

Users and Their Posts:
"""
        
        for user in users_data:
            prompt += f"\nUser: @{user['username']} ({user['name']})"
            prompt += f"\nBio: {user['description']}"
            prompt += "\nRecent Posts:"
            
            for post in user['posts']:
                prompt += f"\n- Post ID {post['id']}:"
                prompt += f"\n  Text: {post['text']}"
                prompt += f"\n  Metrics: {post['metrics']}\n"
            
            prompt += "\n---"
            
        prompt += """

Please provide:
1. A summary of the main topics and themes across all users
2. Analysis of user engagement patterns and influence
3. Notable trends or interesting observations about the user community
4. Content strategy recommendations based on successful posts
5. Identification of key influencers and their content patterns
6. Changes or patterns observed over the collection period

Please format your response in a clear, structured way, with separate sections for each analysis component."""
        
        return prompt 