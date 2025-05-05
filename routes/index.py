from flask import Blueprint, send_from_directory

index_bp = Blueprint('index', __name__)

# Main route serving the single page application
# All other routes will also use this entry point and routing will be handled by JavaScript
@index_bp.route('/')
@index_bp.route('/<path:path>')
def index(path=None):
    return send_from_directory('static', 'index.html')
