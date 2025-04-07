# helpers/llm_helpers.py
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import logging
import io
import os
from openai import OpenAI
from models.llm_models import PageClassification
import logging
from openai import OpenAI
from models import *
from models.llm_models import *
import json
from pydantic import ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed
from helpers.llm_wrappers import call_openai_embeddings, call_openai_chat_parse, call_openai_chat_create
from models.llm_models import BvaDecisionStructuredSummary
import decimal

# ====================================================
# Section: CONFIGURATION
# ====================================================
# Description:  Logging and Openai Setup
# ====================================================

# Set up the OpenAI API key to interact with the GPT models
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)
if not client:
    raise ValueError("Please set the VA_AUTOMATION_API_KEY environment variable.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
#client = OpenAI(api_key=api_key)

# ============  TESTING  ============
# ============  WRAPPED  ============
