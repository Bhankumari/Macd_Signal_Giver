#!/usr/bin/env python3
"""
Test Email Functionality
========================

This script tests the email functionality to ensure it's working correctly.
"""

import os
import sys
from email_config import SMTP_EMAIL, SMTP_PASSWORD, RECIPIENT_EMAIL
from main import EmailSender

def test_email_connection():
    """Test the email connection and send a test message"""
    print("🧪 Testing Email Functionality...")
    print("=" * 50)
    
    try:
        # Initialize email sender
        email_sender = EmailSender()
        
        print(f"📧 SMTP Email: {email_sender.smtp_email}")
        print(f"📧 Recipient: {email_sender.recipient_email}")
        print(f"📧 Server: {email_sender.smtp_server}:{email_sender.smtp_port}")
        
        # Send test email
        subject = "🧪 Test Email - MACD Signal Giver"
        message = """
        <h2>🧪 Test Email</h2>
        <p>This is a test email to verify that the MACD Signal Giver email functionality is working correctly.</p>
        <hr>
        <p><strong>Configuration:</strong></p>
        <ul>
            <li>SMTP Email: {smtp_email}</li>
            <li>Recipient: {recipient_email}</li>
            <li>Server: {smtp_server}:{smtp_port}</li>
        </ul>
        <hr>
        <p>✅ If you received this email, the email functionality is working correctly!</p>
        """.format(
            smtp_email=email_sender.smtp_email,
            recipient_email=email_sender.recipient_email,
            smtp_server=email_sender.smtp_server,
            smtp_port=email_sender.smtp_port
        )
        
        print("📤 Sending test email...")
        success = email_sender.send_email(subject, message)
        
        if success:
            print("✅ Test email sent successfully!")
            print("📧 Check your email at: " + email_sender.recipient_email)
        else:
            print("❌ Failed to send test email!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email: {str(e)}")
        return False
    
    return True

def test_configuration():
    """Test the configuration values"""
    print("🔧 Testing Configuration...")
    print("=" * 30)
    
    print(f"SMTP Email: {SMTP_EMAIL}")
    print(f"SMTP Password: {'*' * len(SMTP_PASSWORD)} (hidden)")
    print(f"Recipient Email: {RECIPIENT_EMAIL}")
    
    # Check if values are set
    if not SMTP_EMAIL or SMTP_EMAIL == "YOUR_SMTP_EMAIL_HERE":
        print("❌ SMTP Email not configured!")
        return False
    
    if not SMTP_PASSWORD or SMTP_PASSWORD == "YOUR_SMTP_PASSWORD_HERE":
        print("❌ SMTP Password not configured!")
        return False
    
    if not RECIPIENT_EMAIL or RECIPIENT_EMAIL == "YOUR_RECIPIENT_EMAIL_HERE":
        print("❌ Recipient Email not configured!")
        return False
    
    print("✅ Configuration looks good!")
    return True

def main():
    """Main test function"""
    print("🚀 MACD Signal Giver - Email Test")
    print("=" * 50)
    
    # Test configuration
    if not test_configuration():
        print("\n❌ Configuration test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test email functionality
    if not test_email_connection():
        print("\n❌ Email test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Email functionality is working correctly.")
    print("📧 You can now run the main script to receive MACD signals via email.")

if __name__ == "__main__":
    main() 