import os
import requests
from django.conf import settings

def send_sms(phone_number, message):
    """
    Send SMS using Africa's Talking API
    """
    try:
        username = os.getenv('SMS_USERNAME')
        api_key = os.getenv('SMS_API_KEY')
        sender_id = os.getenv('SMS_SENDER_ID')
        
        print(f"SMS Config - Username: {username}, API Key: {'*' * len(api_key) if api_key else None}, Sender: {sender_id}")
        
        if not all([username, api_key, sender_id]):
            print("SMS credentials not configured")
            return False
        
        # Format phone number for Kenya (+254)
        if phone_number.startswith('0'):
            phone_number = '+254' + phone_number[1:]
        elif not phone_number.startswith('+'):
            phone_number = '+254' + phone_number
            
        print(f"Sending SMS to: {phone_number}")
        
        url = "https://api.africastalking.com/version1/messaging"
        
        headers = {
            'apiKey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        payload = {
            'username': username,
            'to': phone_number,
            'message': message,
            'from': sender_id
        }
        
        print(f"Payload: {payload}")
        
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            if 'SMSMessageData' in response_data and 'Recipients' in response_data['SMSMessageData']:
                recipients = response_data['SMSMessageData']['Recipients']
                if recipients and recipients[0].get('status') == 'Success':
                    return True
            print(f"SMS API returned error: {response_data}")
            return False
        else:
            print(f"SMS sending failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"SMS sending error: {e}")
        return False
