import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Configures a basic logger for the DrumScript application.
    """
    logger = logging.getLogger('DrumScript')
    logger.setLevel(level)
    
    # Prevent duplicate handlers if this is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # Create a simple and clean formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                    datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger