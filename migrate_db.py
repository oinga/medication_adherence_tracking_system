
from app import create_app, db
from app.models import *
app = create_app()
with app.app_context():
    db.create_all()
    print("Test MATS tables created.")
