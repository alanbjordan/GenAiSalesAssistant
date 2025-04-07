# leads_routes.py

# Import necessary modules
from flask import Blueprint, request, jsonify, g
from config import Config
from datetime import datetime
import os
from helpers.cors_helpers import cors_preflight

# Initialize the Blueprint for the leads routes
leads_bp = Blueprint("leads_bp", __name__)

