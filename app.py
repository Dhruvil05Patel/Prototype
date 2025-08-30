import os
import json
import uuid
import csv
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import requests
from invoice_extractor import extract_invoice_data

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
WEBHOOK_CONFIG_FILE = 'webhook_config.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_webhook_config():
    """Load webhook configuration from file"""
    try:
        with open(WEBHOOK_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_webhook_config(config):
    """Save webhook configuration to file"""
    try:
        with open(WEBHOOK_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving webhook config: {e}")
        return False

def send_to_hubspot(invoice_data):
    """Send invoice data to HubSpot CRM"""
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
    HUBSPOT_BASE_URL = "https://api.hubapi.com"
    
    # Configure which fields to send to HubSpot (set to False to exclude)
    # Temporarily disabled custom fields for testing
    HUBSPOT_FIELD_CONFIG = {
        'invoice_number': False,     # GST Invoice Number - DISABLED FOR TESTING
        'invoice_date': False,       # Invoice Date - DISABLED FOR TESTING
        'vendor_gst': False,         # Company GST Number - DISABLED FOR TESTING
        'invoice_items': False,      # Detailed items list (can be large)
        'billing_address': False,    # Full billing address
        'shipping_address': False,   # Full shipping address
        'payment_terms': False,      # Payment terms and conditions
        'tax_details': False,        # Detailed tax breakdown
        'discount_details': False,   # Discount information
        'notes': False,              # Additional notes
        'currency': False,           # Currency code
        'exchange_rate': False,      # Exchange rate if applicable
        'due_date': False,           # Payment due date
        'po_number': False,          # Purchase order number
        'vendor_contact': False,     # Vendor contact information
        'line_items_count': False,   # Number of line items
        'attachment_url': False,     # URL to invoice attachment
        'processing_status': False,  # Processing status
        'approval_status': False,    # Approval status
        'payment_status': False,     # Payment status
        'created_by': False,         # User who created the record
        'last_modified_by': False,   # User who last modified
        'tags': False,               # Tags for categorization
        'department': False,         # Department/cost center
        'project_code': False,       # Project code if applicable
        'vendor_category': False,    # Vendor category
        'payment_method': False,     # Payment method
        'bank_details': False,       # Bank details for payment
        'recurring': False,          # Is this a recurring invoice
        'parent_invoice': False,     # Parent invoice if this is a child
        'workflow_stage': False,     # Current workflow stage
        'escalation_level': False,   # Escalation level if any
        'risk_score': False,         # Risk assessment score
        'compliance_status': False,  # Compliance check status
        'audit_trail': False,        # Audit trail information
        'integration_source': False, # Source of integration
        'custom_field_1': False,     # Custom field 1
        'custom_field_2': False,     # Custom field 2
        'custom_field_3': False,     # Custom field 3
        'custom_field_4': False,     # Custom field 4
        'custom_field_5': False,     # Custom field 5
    }
    
    if not HUBSPOT_API_KEY:
        print("Warning: HUBSPOT_API_KEY not found in environment variables")
        return False
    
    # Prepare the data for HubSpot
    hubspot_data = {
        "properties": {}
    }
    
    # Add basic fields that are always included
    basic_fields = {
        'company_name': invoice_data.get('vendor_name', ''),
        'total_amount': str(invoice_data.get('total_amount', 0)),
        'invoice_status': 'processed'
    }
    
    # Add basic fields to properties
    for field, value in basic_fields.items():
        if value:  # Only add non-empty values
            hubspot_data["properties"][field] = value
    
    # Add configured fields
    field_mapping = {
        'invoice_number': invoice_data.get('invoice_number', ''),
        'invoice_date': invoice_data.get('invoice_date', ''),
        'vendor_gst': invoice_data.get('vendor_gst', ''),
        'invoice_items': json.dumps(invoice_data.get('items', [])),
        'billing_address': invoice_data.get('billing_address', ''),
        'shipping_address': invoice_data.get('shipping_address', ''),
        'payment_terms': invoice_data.get('payment_terms', ''),
        'tax_details': json.dumps(invoice_data.get('tax_details', {})),
        'discount_details': json.dumps(invoice_data.get('discount_details', {})),
        'notes': invoice_data.get('notes', ''),
        'currency': invoice_data.get('currency', 'INR'),
        'exchange_rate': str(invoice_data.get('exchange_rate', 1.0)),
        'due_date': invoice_data.get('due_date', ''),
        'po_number': invoice_data.get('po_number', ''),
        'vendor_contact': invoice_data.get('vendor_contact', ''),
        'line_items_count': str(len(invoice_data.get('items', []))),
        'attachment_url': invoice_data.get('attachment_url', ''),
        'processing_status': 'completed',
        'approval_status': 'pending',
        'payment_status': 'pending',
        'created_by': 'invoice_scanner',
        'last_modified_by': 'invoice_scanner',
        'tags': 'automated_processing',
        'department': invoice_data.get('department', ''),
        'project_code': invoice_data.get('project_code', ''),
        'vendor_category': invoice_data.get('vendor_category', ''),
        'payment_method': invoice_data.get('payment_method', ''),
        'bank_details': invoice_data.get('bank_details', ''),
        'recurring': str(invoice_data.get('recurring', False)),
        'parent_invoice': invoice_data.get('parent_invoice', ''),
        'workflow_stage': 'data_extracted',
        'escalation_level': '0',
        'risk_score': str(invoice_data.get('risk_score', 0)),
        'compliance_status': 'pending_review',
        'audit_trail': json.dumps([{
            'action': 'data_extracted',
            'timestamp': datetime.now().isoformat(),
            'user': 'system'
        }]),
        'integration_source': 'invoice_scanner_api',
        'custom_field_1': invoice_data.get('custom_field_1', ''),
        'custom_field_2': invoice_data.get('custom_field_2', ''),
        'custom_field_3': invoice_data.get('custom_field_3', ''),
        'custom_field_4': invoice_data.get('custom_field_4', ''),
        'custom_field_5': invoice_data.get('custom_field_5', ''),
    }
    
    # Add only enabled fields to the request
    for field, value in field_mapping.items():
        if HUBSPOT_FIELD_CONFIG.get(field, False) and value:
            hubspot_data["properties"][field] = value
    
    # Send to HubSpot Companies API
    headers = {
        'Authorization': f'Bearer {HUBSPOT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f'{HUBSPOT_BASE_URL}/crm/v3/objects/companies',
            headers=headers,
            json=hubspot_data,
            timeout=30
        )
        
        if response.status_code == 201:
            print("Successfully sent invoice data to HubSpot")
            return True
        else:
            print(f"Failed to send to HubSpot: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending to HubSpot: {e}")
        return False

def send_webhook(invoice_data, webhook_url):
    """Send invoice data to configured webhook URL"""
    try:
        response = requests.post(
            webhook_url,
            json=invoice_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"Successfully sent webhook to {webhook_url}")
            return True
        else:
            print(f"Webhook failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending webhook: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate a unique filename to avoid conflicts
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"temp_invoice_{uuid.uuid4().hex[:16]}.{file_extension}"
            filename = secure_filename(unique_filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Extract invoice data
                invoice_data = extract_invoice_data(filepath)
                
                if invoice_data:
                    # Save to CSV
                    csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_invoices.csv')
                    
                    # Check if CSV exists to determine if we need headers
                    file_exists = os.path.exists(csv_filename)
                    
                    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                        fieldnames = [
                            'timestamp', 'filename', 'vendor_name', 'vendor_gst', 'invoice_number', 
                            'invoice_date', 'total_amount', 'tax_amount', 'subtotal', 'items_count',
                            'billing_address', 'shipping_address', 'payment_terms'
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        # Write header if file is new
                        if not file_exists:
                            writer.writeheader()
                        
                        # Prepare row data
                        row_data = {
                            'timestamp': datetime.now().isoformat(),
                            'filename': filename,
                            'vendor_name': invoice_data.get('vendor_name', ''),
                            'vendor_gst': invoice_data.get('vendor_gst', ''),
                            'invoice_number': invoice_data.get('invoice_number', ''),
                            'invoice_date': invoice_data.get('invoice_date', ''),
                            'total_amount': invoice_data.get('total_amount', 0),
                            'tax_amount': invoice_data.get('tax_amount', 0),
                            'subtotal': invoice_data.get('subtotal', 0),
                            'items_count': len(invoice_data.get('items', [])),
                            'billing_address': invoice_data.get('billing_address', ''),
                            'shipping_address': invoice_data.get('shipping_address', ''),
                            'payment_terms': invoice_data.get('payment_terms', '')
                        }
                        
                        writer.writerow(row_data)
                    
                    # Load webhook configuration
                    webhook_config = load_webhook_config()
                    
                    # Send to HubSpot if enabled
                    if webhook_config.get('hubspot_enabled', False):
                        send_to_hubspot(invoice_data)
                    
                    # Send to custom webhook if configured
                    if webhook_config.get('webhook_enabled', False) and webhook_config.get('webhook_url'):
                        send_webhook(invoice_data, webhook_config['webhook_url'])
                    
                    flash('Invoice processed successfully!')
                    return jsonify({
                        'success': True,
                        'message': 'Invoice processed successfully',
                        'data': invoice_data
                    })
                else:
                    flash('Failed to extract invoice data')
                    return jsonify({
                        'success': False,
                        'message': 'Failed to extract invoice data'
                    }), 400
                    
            except Exception as e:
                flash(f'Error processing invoice: {str(e)}')
                return jsonify({
                    'success': False,
                    'message': f'Error processing invoice: {str(e)}'
                }), 500
            finally:
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
    
    return render_template('upload.html')

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """API endpoint for invoice extraction"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate a unique filename
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"temp_invoice_{uuid.uuid4().hex[:16]}.{file_extension}"
    filename = secure_filename(unique_filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        
        # Extract invoice data
        invoice_data = extract_invoice_data(filepath)
        
        if invoice_data:
            # Load webhook configuration
            webhook_config = load_webhook_config()
            
            # Send to HubSpot if enabled
            if webhook_config.get('hubspot_enabled', False):
                send_to_hubspot(invoice_data)
            
            # Send to custom webhook if configured
            if webhook_config.get('webhook_enabled', False) and webhook_config.get('webhook_url'):
                send_webhook(invoice_data, webhook_config['webhook_url'])
            
            return jsonify({
                'success': True,
                'data': invoice_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to extract invoice data'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/webhook-config', methods=['GET', 'POST'])
def webhook_config():
    """Configure webhook settings"""
    if request.method == 'POST':
        config = {
            'webhook_enabled': request.form.get('webhook_enabled') == 'on',
            'webhook_url': request.form.get('webhook_url', ''),
            'hubspot_enabled': request.form.get('hubspot_enabled') == 'on'
        }
        
        if save_webhook_config(config):
            flash('Webhook configuration saved successfully!')
        else:
            flash('Error saving webhook configuration')
        
        return redirect(url_for('webhook_config'))
    
    # Load current configuration
    config = load_webhook_config()
    return render_template('webhook_config.html', config=config)

@app.route('/download-csv')
def download_csv():
    """Download the extracted invoices CSV file"""
    csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_invoices.csv')
    
    if os.path.exists(csv_filename):
        return send_file(csv_filename, as_attachment=True, download_name='extracted_invoices.csv')
    else:
        flash('No CSV file found')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
