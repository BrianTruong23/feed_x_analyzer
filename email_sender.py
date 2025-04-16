import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

class EmailSender:
    def __init__(self):
        load_dotenv()
        self.sender_email = os.getenv('EMAIL_ADDRESS')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        
    def send_analysis(self, recipient_email, analysis_data):
        """
        Send the X feed analysis via email
        
        Args:
            recipient_email (str): Recipient's email address
            analysis_data (dict): Analysis results from GeminiAnalyzer
        """
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f'X Feed Analysis Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        
        # Create email body
        body = f"""X Feed Analysis Report

Time Range: From {analysis_data['time_range']['oldest']} to {analysis_data['time_range']['newest']}
Users Analyzed: {analysis_data['user_count']}
Total Posts: {analysis_data['total_posts']}

Analysis Results:
----------------
{analysis_data['analysis']}

---
Generated using X Feed Analyzer with Google Gemini
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # Create server connection
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Login and send email
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Analysis sent successfully to {recipient_email}")
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            
        # Also save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(body)
            
        print(f"Analysis saved to {filename}") 