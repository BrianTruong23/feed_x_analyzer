# X Feed Analyzer with Google Gemini

This project combines X (Twitter) API with Google Gemini to analyze your X feed and provide intelligent insights about your timeline.

## Setup

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your API credentials:
```env
# X (Twitter) API Credentials
X_BEARER_TOKEN=your_bearer_token_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_API_KEY=your_api_key_here
X_API_KEY_SECRET=your_api_key_secret_here

# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Getting API Keys

1. For X API credentials:
   - Go to the [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
   - Create a new app or use an existing one
   - Generate the necessary tokens and keys

2. For Google Gemini API key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key in your Google Cloud Console
   - Copy the API key to your .env file

## Usage

Here's a simple example of how to use the analyzer:

```python
from gemini_analyzer import GeminiAnalyzer

# Initialize the analyzer
analyzer = GeminiAnalyzer()

# Get analysis of your feed
results = analyzer.analyze_feed()

# Print the analysis
if results['status'] == 'success':
    print(results['analysis'])
else:
    print(f"Error: {results['message']}")
```

## Features

- Fetches your X home timeline
- Processes tweet content and engagement metrics
- Uses Google Gemini to provide intelligent analysis including:
  - Topic and theme identification
  - Engagement pattern analysis
  - Trend detection
  - Engagement improvement recommendations

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure and rotate them regularly
- Follow X and Google's API usage guidelines and rate limits

## License

MIT License 