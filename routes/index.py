from flask import Blueprint, jsonify

index_bp = Blueprint('index', __name__)

@index_bp.route("/")
def root():
    return jsonify({"message": "EcoMonitor backend is running."})
