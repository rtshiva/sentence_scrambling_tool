import logging
import sys

def setup_logging(level=logging.INFO):
    """Configure application-wide logging."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
