#!/usr/bin/env python3
"""
Script to set up Gmail push notifications to Google Cloud Pub/Sub
"""

import os
import json
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import pubsub_v1
import boto3

def setup_gmail_push_notifications(
    service_account_file: str,
    project_id: str,
    topic_name: str,
    gmail_address: str,
    aws_eventbridge_endpoint: str = None
):
    """Set up Gmail push notifications to Pub/Sub"""
    
    print("Setting up Gmail push notifications...")
    
    # Setup credentials
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/pubsub'
        ]
    )
    
    # Initialize services
    gmail_service = build('gmail', 'v1', credentials=credentials)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    
    # Create topic if it doesn't exist
    topic_path = publisher.topic_path(project_id, topic_name)
    
    try:
        publisher.get_topic(request={"topic": topic_path})
        print(f"Topic {topic_name} already exists")
    except Exception:
        print(f"Creating topic {topic_name}")
        publisher.create_topic(request={"name": topic_path})
    
    # Set up Gmail watch
    watch_request = {
        'labelIds': ['INBOX'],
        'topicName': topic_path
    }
    
    try:
        result = gmail_service.users().watch(userId='me', body=watch_request).execute()
        print(f"Gmail watch set up successfully!")
        print(f"History ID: {result.get('historyId')}")
        print(f"Expiration: {result.get('expiration')}")
        
        # Save watch info
        watch_info = {
            'historyId': result.get('historyId'),
            'expiration': result.get('expiration'),
            'topicName': topic_path,
            'gmail_address': gmail_address
        }
        
        with open('gmail_watch_info.json', 'w') as f:
            json.dump(watch_info, f, indent=2)
            
        print("Watch information saved to gmail_watch_info.json")
        
    except Exception as e:
        print(f"Error setting up Gmail watch: {e}")
        return False
    
    # If AWS EventBridge endpoint is provided, set up Pub/Sub subscription
    if aws_eventbridge_endpoint:
        setup_pubsub_to_eventbridge(
            credentials, project_id, topic_name, aws_eventbridge_endpoint
        )
    
    return True

def setup_pubsub_to_eventbridge(
    credentials,
    project_id: str,
    topic_name: str,
    eventbridge_endpoint: str
):
    """Set up Pub/Sub subscription to push to AWS EventBridge"""
    
    print("Setting up Pub/Sub to EventBridge integration...")
    
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    
    subscription_name = f"{topic_name}-to-eventbridge"
    topic_path = subscriber.topic_path(project_id, topic_name)
    subscription_path = subscriber.subscription_path(project_id, subscription_name)
    
    # Create push subscription to EventBridge
    push_config = {
        'push_endpoint': eventbridge_endpoint,
        'attributes': {
            'x-goog-version': 'v1'
        }
    }
    
    try:
        subscriber.get_subscription(request={"subscription": subscription_path})
        print(f"Subscription {subscription_name} already exists")
    except Exception:
        print(f"Creating subscription {subscription_name}")
        subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "push_config": push_config
            }
        )
    
    print("Pub/Sub to EventBridge integration set up successfully!")

def create_service_account_and_setup(project_id: str, gmail_address: str):
    """Create service account and set up Gmail notifications"""
    
    print("This function would create a service account in Google Cloud.")
    print("Please follow these manual steps:")
    print("1. Go to Google Cloud Console")
    print("2. Create a new service account")
    print("3. Grant it Gmail API and Pub/Sub permissions")
    print("4. Download the service account key file")
    print("5. Run this script again with the service account file")

def main():
    parser = argparse.ArgumentParser(description='Set up Gmail push notifications')
    parser.add_argument('--service-account-file', required=True,
                       help='Path to Google service account JSON file')
    parser.add_argument('--project-id', required=True,
                       help='Google Cloud Project ID')
    parser.add_argument('--topic-name', default='gmail-notifications',
                       help='Pub/Sub topic name')
    parser.add_argument('--gmail-address', required=True,
                       help='Gmail address to monitor')
    parser.add_argument('--eventbridge-endpoint',
                       help='AWS EventBridge endpoint URL')
    
    args = parser.parse_args()
    
    # Validate service account file
    if not os.path.exists(args.service_account_file):
        print(f"Error: Service account file not found: {args.service_account_file}")
        return False
    
    success = setup_gmail_push_notifications(
        args.service_account_file,
        args.project_id,
        args.topic_name,
        args.gmail_address,
        args.eventbridge_endpoint
    )
    
    if success:
        print("\n✅ Gmail push notifications set up successfully!")
        print("\nNext steps:")
        print("1. Test by sending an email to your Gmail address")
        print("2. Check CloudWatch logs for Lambda function execution")
        print("3. Verify Fargate task is triggered")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
    
    return success

if __name__ == '__main__':
    main() 