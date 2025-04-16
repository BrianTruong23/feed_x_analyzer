import os
from datetime import datetime
from gemini_analyzer import GeminiAnalyzer
from email_sender import EmailSender
import subprocess

def git_commit_and_push(file_path):
    """Commit and push the analysis file to git"""
    try:
        # Add the file
        subprocess.run(['git', 'add', file_path], check=True)
        
        # Create commit with timestamp
        commit_message = f"Add analysis report for {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push to remote
        subprocess.run(['git', 'push'], check=True)
        print(f"Successfully committed and pushed {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error in git operations: {str(e)}")

def main():
    # Initialize the analyzer
    analyzer = GeminiAnalyzer()
    
    # Get the analysis
    print("Fetching and analyzing X feed data...")
    results = analyzer.analyze_feed()
    
    if results['status'] != 'success':
        print(f"Error: {results['message']}")
        return
    
    # Create analysis report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"analysis_report_{timestamp}.txt"
    
    report_content = f"""X Feed Analysis Report
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Time Range: From {results['time_range']['oldest']} to {results['time_range']['newest']}
Users Analyzed: {results['user_count']}
Total Posts: {results['total_posts']}

Analysis Results:
----------------
{results['analysis']}

---
Generated using X Feed Analyzer with Google Gemini
"""
    
    # Save report to file
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"\nAnalysis saved to {report_file}")
    
    # Initialize email sender and send analysis
    email_sender = EmailSender()
    recipient_email = "truongthoithang@gmail.com"
    print(f"\nSending analysis to {recipient_email}...")
    email_sender.send_analysis(recipient_email, results)
    
    # Commit and push the analysis file
    git_commit_and_push(report_file)

if __name__ == "__main__":
    main() 