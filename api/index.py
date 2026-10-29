import os
import sys

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app
from app.database import init_db, seed_initial_data

# Ensure database tables and initial demo seeds exist on serverless cold-start
try:
    init_db()
    seed_initial_data()
except Exception as e:
    pass
