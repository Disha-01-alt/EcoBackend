import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS


# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS
# Define the allowed frontend origins (add your Netlify domain when deployed)
allowed_origins = [
    'http://localhost:5000',
    'http://localhost:8080',  # Local development
    'https://your-netlify-app.netlify.app',  # Replace with your Netlify domain
    '*'  # Allow any domain during development (remove in production)
]

# Configure CORS with more options
CORS(app, resources={r"/*": {"origins": allowed_origins, "supports_credentials": True}})

# Import routes
from routes.index import index_bp
from routes.api import api_bp
@app.route("/assets/pages/<path:filename>")
def serve_partials(filename):
    return send_from_directory("assets/pages", filename)

# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
