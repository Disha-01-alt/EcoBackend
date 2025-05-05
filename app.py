import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Allow Netlify frontend to access backend
allowed_origins = [
    "https://admirable-frangipane-21d5ff.netlify.app",  # ✅ Your Netlify domain
    "http://localhost:3000",  # Optional for local development
    "http://127.0.0.1:5000"
]

# Enable CORS
CORS(app, resources={r"/*": {"origins": allowed_origins}}, supports_credentials=True)

# Import routes
from routes.index import index_bp
from routes.api import api_bp

# Serve frontend partials
@app.route("/assets/pages/<path:filename>")
def serve_partials(filename):
    return send_from_directory("assets/pages", filename)

# Register routes
app.register_blueprint(index_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
