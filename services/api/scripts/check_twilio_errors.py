import os
import requests
from dotenv import load_dotenv
import json

def check_errors():
    load_dotenv()
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    # Fetch latest call
    calls_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json?PageSize=1"
    resp = requests.get(calls_url, auth=(account_sid, auth_token))
    
    if resp.status_code != 200:
        print("Failed to fetch calls:", resp.text)
        return
        
    calls = resp.json().get("calls", [])
    if not calls:
        print("No calls found.")
        return
        
    call = calls[0]
    print(f"Latest Call SID: {call['sid']}")
    print(f"Status: {call['status']}")
    print(f"Direction: {call['direction']}")
    print(f"To: {call['to']}")
    
    # Fetch notifications for this call
    notif_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call['sid']}/Notifications.json"
    notif_resp = requests.get(notif_url, auth=(account_sid, auth_token))
    
    if notif_resp.status_code == 200:
        notifications = notif_resp.json().get("notifications", [])
        if notifications:
            print(f"\nFound {len(notifications)} errors/warnings:")
            for n in notifications:
                print(f" - Error {n['error_code']}: {n['message_text']}")
                print(f"   Log: {n.get('log')}")
        else:
            print("\nNo errors/warnings found for this call in Twilio.")
    else:
        print("Failed to fetch notifications.")

if __name__ == "__main__":
    check_errors()
