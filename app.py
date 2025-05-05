import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")  # Ensure this is set in your environment

# Enable CORS for your Netlify domain
allowed_origins = [
    "https://admirable-frangipane-21d5ff.netlify.app/"  # Netlify frontend domain
]

# Configure CORS with more options
CORS(app, resources={r"/*": {"origins": allowed_origins, "supports_credentials": True}})

# Import routes
from routes.index import index_bp
from routes.api import api_bp

@app.route("/assets/pages/<path:filename>")
def serve_partials(filename):
    # Ensure the "assets/pages" directory exists and contains the required files
    return send_from_directory("assets/pages", filename)

# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Main entry point for Flask app
if __name__ == "__main__":
    # Use host="0.0.0.0" for external access and specify the port, or use an environment variable
    port = int(os.environ.get("PORT", 5000))  # Make sure the port matches your platform’s configuration
    app.run(host="0.0.0.0", port=port, debug=True)
