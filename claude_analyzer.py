import os
from anthropic import Anthropic
from dotenv import load_dotenv
from x_client import XClient

class ClaudeAnalyzer:
    def __init__(self):
        load_dotenv()
        self.anthropic = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.x_client = XClient()

    def analyze_feed(self):
        """
        Fetch the user's X feed and analyze it using Claude AI.
        
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

        # Prepare prompt for Claude
        prompt = self._create_analysis_prompt(feed_data)
        
        try:
            # Get Claude's analysis
            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert social media analyst. Analyze the provided X (Twitter) feed data and provide insights about the content, engagement patterns, and notable trends.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return {
                'status': 'success',
                'analysis': message.content,
                'tweet_count': feed_data['tweet_count'],
                'time_range': feed_data['time_range']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error during Claude analysis: {str(e)}'
            }

    def _create_analysis_prompt(self, feed_data):
        """
        Create a detailed prompt for Claude AI based on the feed data.
        
        Args:
            feed_data (dict): Feed data from X
            
        Returns:
            str: Formatted prompt for Claude
        """
        tweets = feed_data['tweets']
        time_range = feed_data['time_range']
        
        prompt = f"""Please analyze this X (Twitter) feed data and provide insights:

Time Range: From {time_range['oldest']} to {time_range['newest']}
Number of Tweets: {feed_data['tweet_count']}

Tweet Contents:
"""
        
        for tweet in tweets:
            prompt += f"\n- Tweet ID {tweet['id']}:"
            prompt += f"\n  Text: {tweet['text']}"
            prompt += f"\n  Metrics: {tweet['metrics']}\n"
            
        prompt += """

Please provide:
1. A summary of the main topics and themes in the feed
2. Analysis of engagement patterns
3. Notable trends or interesting observations
4. Any recommendations for better engagement

Please format your response in a clear, structured way."""
        
        return prompt 