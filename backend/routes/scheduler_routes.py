

# Import necessary modules
from flask import Blueprint, request, jsonify, g
from config import Config
from datetime import datetime
import os
from helpers.cors_helpers import cors_preflight

# Initialize the Blueprint for the leads routes
scheduler_bp = Blueprint("scheduler_bp", __name__)