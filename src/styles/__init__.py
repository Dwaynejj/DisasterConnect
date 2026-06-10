import os
from .tokens import LIGHT_TOKENS, DARK_TOKENS

def load_stylesheet(dark=False):
    """
    Loads main.qss and interpolates the appropriate tokens based on the theme.
    Returns the final QSS string.
    """
    tokens = DARK_TOKENS if dark else LIGHT_TOKENS
    qss_path = os.path.join(os.path.dirname(__file__), 'main.qss')
    
    with open(qss_path, 'r') as f:
        qss_template = f.read()
        
    return qss_template.format(**tokens)
