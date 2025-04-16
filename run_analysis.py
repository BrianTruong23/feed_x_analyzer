from gemini_analyzer import GeminiAnalyzer
from email_sender import EmailSender

def main():
    # Initialize the analyzer
    analyzer = GeminiAnalyzer()
    
    # Get the analysis
    print("Fetching and analyzing X feed data...")
    results = analyzer.analyze_feed()
    
    if results['status'] != 'success':
        print(f"Error: {results['message']}")
        return
    
    # Initialize email sender
    email_sender = EmailSender()
    
    # Send analysis to specified email
    recipient_email = "truongthoithang@gmail.com"
    print(f"\nSending analysis to {recipient_email}...")
    email_sender.send_analysis(recipient_email, results)

if __name__ == "__main__":
    main() 