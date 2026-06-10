import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point of the DisasterConnect application.
    Delegates to the full-featured src/main.py entry point which includes
    the splash screen, sidebar navigation, and dashboard.
    """
    try:
        from src.main import main as src_main
        src_main()
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
