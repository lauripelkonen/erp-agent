#!/usr/bin/env python3
"""
Gmail Token Management CLI
Helps manage Gmail OAuth tokens - check status, force renewal, etc.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_processing.gmail_oauth_processor import GmailOAuthProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def check_token_status():
    """Check the current status of the Gmail token."""
    processor = GmailOAuthProcessor()
    status = await processor.check_token_status()
    
    print("\n🔍 Gmail Token Status:")
    print(f"   Status: {status['status']}")
    print(f"   Message: {status['message']}")
    print(f"   Needs Auth: {status['needs_auth']}")
    
    if 'expires_at' in status:
        print(f"   Expires At: {status['expires_at']}")
    
    return status


async def force_renewal():
    """Force a fresh OAuth flow to renew the token."""
    processor = GmailOAuthProcessor()
    
    print("\n🔄 Starting token renewal...")
    success = await processor.force_token_renewal()
    
    if success:
        print("✅ Token renewal completed successfully!")
        # Check new status
        await check_token_status()
    else:
        print("❌ Token renewal failed!")
        return False
    
    return True


async def test_connection():
    """Test the Gmail connection."""
    processor = GmailOAuthProcessor()
    
    print("\n🧪 Testing Gmail connection...")
    
    try:
        await processor.initialize()
        health = await processor.health_check()
        
        print("✅ Gmail connection test results:")
        print(f"   Status: {health['status']}")
        
        if health['status'] == 'healthy':
            print(f"   Email: {health.get('email_address', 'Unknown')}")
            print(f"   Total Messages: {health.get('messages_total', 'Unknown')}")
            print(f"   Total Threads: {health.get('threads_total', 'Unknown')}")
        else:
            print(f"   Error: {health.get('error', 'Unknown error')}")
        
        return health['status'] == 'healthy'
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Gmail Token Management CLI")
    parser.add_argument(
        'action',
        choices=['status', 'renew', 'test'],
        help='Action to perform: status (check token), renew (force renewal), test (test connection)'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Automatically fix issues (e.g., renew expired tokens)'
    )
    
    args = parser.parse_args()
    
    print("📧 Gmail Token Management")
    print("=" * 40)
    
    if args.action == 'status':
        status = await check_token_status()
        
        if args.auto_fix and status['needs_auth']:
            print("\n🔧 Auto-fix enabled - attempting token renewal...")
            await force_renewal()
    
    elif args.action == 'renew':
        await force_renewal()
    
    elif args.action == 'test':
        status = await check_token_status()
        
        if status['needs_auth']:
            print("\n⚠️ Token needs authentication - run 'renew' first or use --auto-fix")
            
            if args.auto_fix:
                print("\n🔧 Auto-fix enabled - renewing token first...")
                if await force_renewal():
                    await test_connection()
        else:
            await test_connection()
    
    print("\n✨ Done!")


if __name__ == '__main__':
    asyncio.run(main()) 