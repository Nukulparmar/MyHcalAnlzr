#!/usr/bin/env python3
"""
File skimmer for ROOT files - removes unnecessary branches and filters events.

This script can be used standalone or imported as a module.
"""

import os
import sys
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def make_small(path, max_tries=3, debug=False):
    """
    Make ROOT file smaller by removing unnecessary branches and events.
    
    Args:
        path (str): Path to the input ROOT file
        max_tries (int): Maximum number of attempts (default: 3)
        debug (bool): Enable debug logging
        
    Returns:
        bool: True if successful, False otherwise
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not os.path.exists(path):
        logger.error(f"Input file does not exist: {path}")
        return False
    
    if not path.endswith(".root"):
        logger.error(f"Input file is not a ROOT file: {path}")
        return False
    
    patht1 = path.replace(".root", "_temp.root")
    patht2 = path.replace(".root", "_temp2.root")
    backup_path = path.replace(".root", "_FULL.root")
    
    logger.info(f"Processing: {path}")
    logger.debug(f"Temp file 1: {patht1}")
    logger.debug(f"Temp file 2: {patht2}")
    logger.debug(f"Backup will be: {backup_path}")
    
    try:
        tries = 0
        while tries < max_tries:
            logger.info(f"Attempt {tries + 1}/{max_tries}")
            
            # Remove HLT branches and filter non-eventtype 1 events
            logger.debug("Running rooteventselector...")
            selector_cmd = (
                f'rooteventselector -s "(uMNio_EventType == 1)" '
                f'-e "HLT*,*RecHit*,DigiHF_ok*,DigiHO_er*,DigiHO_dv*,*Error,'
                f'*fiber*,*flags,*pedestalfc*,*subdet,*soi,*tdc*,*valid" '
                f'{path}:Events {patht1}'
            )
            
            selector_result = os.system(selector_cmd)
            if selector_result != 0:
                logger.warning(f"rooteventselector failed with code {selector_result}")
                tries += 1
                continue
            
            # Re-compress using haddnano
            logger.debug("Running haddnano for compression...")
            haddnano_cmd = f'python3 haddnano.py {patht2} {patht1}'
            success = os.system(haddnano_cmd)
            
            # Clean up temp file 1
            if os.path.exists(patht1):
                os.remove(patht1)
                logger.debug(f"Removed temporary file: {patht1}")
            
            if success == 0:
                logger.info("Successfully processed file")
                break
            else:
                logger.warning(f"haddnano failed with code {success}")
                # Clean up temp file 2 if it exists
                if os.path.exists(patht2):
                    os.remove(patht2)
                    logger.debug(f"Removed failed output file: {patht2}")
                tries += 1
        
        if tries >= max_tries:
            logger.error(f"Failed after {max_tries} attempts")
            return False
        
        # Move original file to backup
        logger.info(f"Creating backup: {backup_path}")
        mv_backup_cmd = f'mv {path} {backup_path}'
        backup_result = os.system(mv_backup_cmd)
        if backup_result != 0:
            logger.error(f"Failed to create backup, aborting")
            return False
        
        # Move processed file to original location
        logger.info(f"Moving processed file to original location")
        mv_final_cmd = f'mv {patht2} {path}'
        final_result = os.system(mv_final_cmd)
        if final_result != 0:
            logger.error(f"Failed to move final file")
            # Try to restore backup
            os.system(f'mv {backup_path} {path}')
            return False
        
        logger.info(f"Successfully processed {path}")
        logger.info(f"Original file backed up as: {backup_path}")
        logger.info(f"deleting the backup file might save disk space")
        os.remove(backup_path)
        logger.info(f"Deleted backup file: {backup_path}")
        return True
        
    except OSError as e:
        logger.error(f"File operation error: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        # Clean up temporary files
        for temp_file in [patht1, patht2]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"Cleaned up: {temp_file}")

        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    """Main function for standalone usage."""
    parser = argparse.ArgumentParser(
        description="Make ROOT files smaller by removing unnecessary branches and events"
    )
    parser.add_argument(
        "input_file", 
        help="Path to input ROOT file"
    )
    parser.add_argument(
        "--max-tries", 
        type=int, 
        default=10, 
        help="Maximum number of attempts (default: 3)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    success = make_small(args.input_file, args.max_tries, args.debug)
    
    if success:
        logger.info("File processing completed successfully")
        sys.exit(0)
    else:
        logger.error("File processing failed")
        sys.exit(1)

# Backward compatibility - keep original function name
def MakeSmall(path):
    """
    Original function name for backward compatibility.
    
    Args:
        path (str): Path to the input ROOT file
    """
    return make_small(path, max_tries=1, debug=False)

if __name__ == "__main__":
    main()