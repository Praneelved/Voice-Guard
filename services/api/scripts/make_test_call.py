import os
import sys
import requests
from dotenv import load_dotenv

def make_test_call(to_number: str):
    load_dotenv()
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    base_url = os.getenv("BASE_URL")
    
    if not all([account_sid, auth_token, from_number, base_url]):
        print("Missing required environment variables in .env")
        sys.exit(1)
        
    webhook_url = f"{base_url}/v1/providers/twilio/webhook"
    
    # Twilio REST API endpoint for creating a call
    twilio_api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    
    data = {
        "Url": webhook_url,
        "To": to_number,
        "From": from_number
    }
    
    print(f"Initiating outbound call from {from_number} to {to_number}...")
    print(f"Webhook URL: {webhook_url}")
    
    response = requests.post(
        twilio_api_url,
        data=data,
        auth=(account_sid, auth_token)
    )
    
    if response.status_code == 201:
        print("\nSUCCESS! Twilio is dialing the number.")
        call_sid = response.json().get("sid")
        print(f"Call SID: {call_sid}")
        print("Check your FastAPI server logs for 'CALL STARTED' and 'MEDIA RECEIVED'.")
    else:
        print(f"\nFAILED to initiate call (Status {response.status_code})")
        print(response.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.make_test_call <YOUR_PERSONAL_PHONE_NUMBER>")
        print("Example: python -m scripts.make_test_call +1234567890")
        sys.exit(1)
        
    make_test_call(sys.argv[1])
