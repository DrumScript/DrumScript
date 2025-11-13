import logging
import sys
import os
from pathlib import Path

def setup_logging(level=logging.INFO):
    
    # Configures a basic logger for the DrumScript application.
    
    # This logger will:
    # 1. Stream (print) logs to the console (stdout).
    # 2. Save all logs to a file at 'drumscript/logs/drumscript.log'.
    
    logger = logging.getLogger('DrumScript')
    logger.setLevel(level)

    # Create a simple and clean formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    
    # Prevent duplicate handlers if this is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # --- Handler 1: Stream to Terminal (stdout) ---
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # --- Handler 2: Save to File ---
        
        # 1. Define the log file path
        # Goes up 3 levels (logging.py -> utils -> drumscript -> root)
        project_root = Path(__file__).parent.parent.parent 
        log_dir = project_root / "drumscript" / "logs"
        log_file = log_dir / "drumscript.log"
        
        # 2. Create the 'logs' directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Create the file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)  # Use the same formatter

        
    return logger