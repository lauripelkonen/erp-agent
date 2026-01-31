#!/usr/bin/env python3
"""
Test script to verify libratom installation and basic functionality
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_libratom_import():
    """Test if libratom can be imported"""
    try:
        from libratom.lib.pff import PffArchive
        logger.info("✅ libratom import successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import libratom: {e}")
        return False

def test_pst_file_opening(pst_path):
    """Test opening a PST file with libratom"""
    if not Path(pst_path).exists():
        logger.warning(f"⚠️  PST file not found: {pst_path}")
        return False
    
    try:
        from libratom.lib.pff import PffArchive
        
        logger.info(f"Attempting to open PST file: {pst_path}")
        with PffArchive(pst_path) as archive:
            logger.info("✅ PST file opened successfully")
            
            # Try to count messages
            message_count = 0
            try:
                for message in archive.messages():
                    message_count += 1
                    if message_count >= 5:  # Just count first 5 for testing
                        break
                logger.info(f"✅ Found {message_count} messages (sample)")
                
                # Test message properties like in the example
                if message_count > 0:
                    try:
                        first_message = next(iter(archive.messages()))
                        subject = getattr(first_message, 'subject', 'No subject')
                        logger.info(f"✅ Sample message subject: {subject[:50]}...")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not get message details: {e}")
                        
            except Exception as e:
                logger.warning(f"⚠️  Could not iterate messages: {e}")
            
            return True
    except Exception as e:
        error_msg = str(e)
        if "koska toinen prosessi on lukinnut" in error_msg or "another process" in error_msg.lower():
            logger.error(f"❌ PST file is locked by another process (likely Outlook is running)")
            logger.error(f"💡 Please close Outlook and try again")
        else:
            logger.error(f"❌ Failed to open PST file: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Testing libratom installation...")
    
    # Test import
    if not test_libratom_import():
        sys.exit(1)
    
    # Test with PST file from config
    try:
        from config import Config
        pst_file_path = Config.PST_FILE_PATH
        logger.info(f"Using PST file from config: {pst_file_path}")
        test_pst_file_opening(pst_file_path)
    except Exception as e:
        logger.error(f"❌ Failed to load PST path from config: {e}")
        
        # Fallback: Look for PST files in current directory
        pst_files = list(Path('.').glob('*.pst'))
        if pst_files:
            logger.info(f"Fallback: Found PST files: {[str(f) for f in pst_files]}")
            test_pst_file_opening(str(pst_files[0]))
        else:
            logger.info("No PST files found in current directory for testing")
    
    logger.info("libratom test completed!")

if __name__ == "__main__":
    main() 