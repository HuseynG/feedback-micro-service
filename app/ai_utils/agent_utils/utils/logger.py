import logging
from typing import Dict
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors based on the agent name."""
    
    COLORS = {
        'overview': Fore.BLUE,
        'news': Fore.GREEN,
        'reviews': Fore.MAGENTA,
        'default': Fore.WHITE
    }

    def format(self, record):
        # Extract agent name from the record (if available)
        agent_name = getattr(record, 'agent_name', 'default').lower()
        
        # Get the appropriate color
        color = self.COLORS.get(agent_name, self.COLORS['default'])
        
        # Add color to the message
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(name: str = "agent_logger", level=logging.INFO) -> logging.Logger:
    """
    Set up a logger with colored output based on agent name.
    
    Args:
        name (str): Name of the logger
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(agent_name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger if it doesn't already have handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger

# Create a global logger instance
logger = setup_logger()

def log_agent_action(agent_name: str, message: str, level: int = logging.INFO):
    """
    Log an action with the appropriate color for the agent.
    
    Args:
        agent_name (str): Name of the agent (e.g., 'overview', 'news', 'reviews')
        message (str): Message to log
        level (int): Logging level (default: logging.INFO)
    """
    logger.log(level, message, extra={'agent_name': agent_name})
