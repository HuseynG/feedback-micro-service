import logging
import os
import colorlog
import json
import pprint

# Custom formatter that beautifies messages
class BeautifyFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        # If record.msg is a complex data type, pretty-print it
        if isinstance(record.msg, (dict, list, tuple, set)):
            record.msg = pprint.pformat(record.msg, indent=4)
        else:
            # Try to parse the message string as JSON
            message = record.getMessage()
            try:
                json_obj = json.loads(message)
                record.msg = json.dumps(json_obj, indent=4)
            except (TypeError, json.JSONDecodeError):
                # Leave the message as is if it's not JSON
                pass
        return super().format(record)

# Create a common logger that can be imported in all files
logger = logging.getLogger('common_logger')

# Set logger level based on environment variable (for debug mode)
debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

# Define the absolute path for the log directory
LOG_DIR = '.'
os.makedirs(LOG_DIR, exist_ok=True)

# Create a file handler to log errors and critical messages to a file
file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'ai_backend_error.log'))
file_handler.setLevel(logging.ERROR)  # Log only errors and critical messages to the file

# Create a console handler to output debug and above messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)

# Define format strings
log_format = '%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s'
color_log_format = '%(log_color)s' + log_format + '%(reset)s'

# Define a plain formatter for the file handler (no color codes)
plain_formatter = BeautifyFormatter(log_format)

# Create a colorful formatter for the console handler
color_formatter = BeautifyFormatter(
    color_log_format,
    log_colors={
        'DEBUG':    'blue',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red,bg_white',
    }
)

# Set formatter for file handler (plain) and console handler (colored)
file_handler.setFormatter(plain_formatter)
console_handler.setFormatter(color_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent log messages from being propagated to the root logger
logger.propagate = False

# Example usage
if __name__ == "__main__":
    name = 'Huseyn'
    project = 'AI Feedback System'
    logger.info(f'This is a message from {name} about the {project}')
    logger.info('{"name": "Huseyn", "project": "AI Feedback System"}')
    logger.debug({"status": "processing", "task": "Generate feedback"})
    logger.warning(['This', 'is', 'a', 'list', 'of', 'warnings'])
    logger.error('This is a plain error message')
    logger.critical('{"error": "Critical failure", "code": 500}')