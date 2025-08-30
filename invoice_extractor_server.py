import os
import google.generativeai as genai
from typing import Dict, Optional, Tuple
from PIL import Image
import io
from dotenv import load_dotenv
import base64
import json
import re

# Load environment variables
load_dotenv()

# Initialize Gemini API
try:
    GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("Please set the GOOGLE_API_KEY in the .env file")
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error initializing Gemini API: {e}")
    MODEL = None

def extract_fields_from_image(image_path: str) -> Tuple[Dict[str, str], str]:
    """Extract invoice fields from an image using Gemini API."""
    if not MODEL:
        return {}, "Error: Gemini API not properly initialized. Check your API key."
    
    try:
        # Load and prepare the image
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
        
        # Prepare the prompt
        prompt = """Extract data from this pharmacy invoice and return it in a structured JSON format.
        
        CRITICAL INSTRUCTIONS:
        1. For each item, you MUST extract the NDC (National Drug Code) or SKU:
           - Look for numbers in these formats: 12345-678-90, 1234567890, 12345678901, 1234-5678-90
           - Look in a separate column specifically for SKU/NDC/HSN code
           - If SKU/NDC is not found, use "NA" (do not generate or make up codes)
           - Never extract SKU from product description or other fields
        
        2. Return the response in this exact JSON structure:
        {
          "company_info": {
            "company_name": "string"
          },
          "billing_info": {
            "billing_company_name": "string",
            "billing_address": "string"
          },
          "shipping_info": {
            "shipping_company_name": "string",
            "shipping_address": "string"
          },
          "invoice_info": {
            "gst_invoice_number": "string",
            "invoice_date": "string",
            "due_date": "string",
            "sales_person": "string",
            "order_number": "string"
          },
          "items": [
            {
              "sku_ndc_number": "string (or 'NA' if not found)",
              "description_of_goods": "string (product name/description)",
              "size": "string (or 'NA' if not found)",
              "quantity": "number (0 if not found)",
              "rate": "number (0 if not found)",
              "amount": "number (0 if not found)",
              "uqc": "string (e.g., 'CT', 'BOX', 'BTL')"
            }
          ],
          "totals": {
            "subtotal": "number (0 if not found, sum of all item amounts if not explicitly provided)",
            "shipping": "number (0 if not found)",
            "discount": "number (0 if not found)",
            "tax": "number (0 if not found)",
            "total_invoice": "number (0 if not found)"
          }
        }
        
        IMPORTANT RULES:
        1. For missing text fields, use "NA"
        2. For missing numeric fields, use 0
        3. SKU/NDC must only come from a dedicated column, not from descriptions
        4. Never make up or hallucinate data - only extract what's visible
        5. For totals, only include values that are explicitly shown in the invoice
        6. Do not calculate any values - only extract what's visible
        7. If subtotal is not shown, leave it as 0
        8. If discount is not shown, leave it as 0
        9. If shipping is not shown, leave it as 0
       10. If tax is not shown, leave it as 0
       11. For items, include ALL products exactly as listed
        """
        # Generate content
        response = MODEL.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_data}])
        
        # Process the response
        try:
            # Try to parse the response as JSON
            result = json.loads(response.text)
            return {k: v for k, v in result.items() if v is not None}, ""
        except json.JSONDecodeError:
            # If direct JSON parsing fails, try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {k: v for k, v in result.items() if v is not None}, ""
            else:
                return {}, "Could not parse the response as JSON"
    except Exception as e:
        return {}, f"Error processing image: {str(e)}"

# Removed save_to_csv function as it's not needed
