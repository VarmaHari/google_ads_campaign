from flask import Flask
from dotenv import load_dotenv
import os, sys
from routes import campaigns_bp


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Load environment variables from the .env file
load_dotenv()

# Register the Blueprint with the Flask app
app.register_blueprint(campaigns_bp)

if __name__ == '__main__':
    app.run(debug=True)
