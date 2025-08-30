import os
import csv
import google.generativeai as genai
from typing import Dict, Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
from dotenv import load_dotenv
import base64

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

# List of fields to extract
FIELDS = [
    # Company Information
    "Company name", "Company Address", "City", "State", "Pincode", "GSTIN", "Email", "Phone",
    
    # Invoice Information
    "Invoice Number", "Issue Date", "Due Date", "Payment Terms", "Sales Person", "Order Number",
    
    # Billing Information
    "Bill to Name", "Bill to Address", "Bill to City", "Bill to State", "Bill to Pincode", "Bill to GSTIN",
    
    # Shipping Information
    "Ship to Name", "Ship to Address", "Ship to City", "Ship to State", "Ship to Pincode",
    
    # Items
    "SKU (NDC Number)", "Product Name", "Description", "Size", "Quantity", "Price", "Total",
    
    # Summary
    "Subtotal", "Shipping", "Discount", "Tax", "Total Amount",
    
    # Additional Info
    "Notes", "Terms and Conditions"
]

def extract_fields_from_image(image_path: str) -> Tuple[Dict[str, str], str]:
    """Extract invoice fields from an image using Gemini API."""
    if not MODEL:
        return {}, "Error: Gemini API not properly initialized. Check your API key."
    
    try:
        # Load and prepare the image
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
        
        # Prepare the prompt
        prompt = """Extract all data from this pharmacy invoice and return it in a structured JSON format. 
        
        CRITICAL INSTRUCTIONS:
        1. For each item, you MUST extract the NDC (National Drug Code) or SKU (in general sku us written and not ndc but in some cases we do have ndc ):
           - Look for numbers in these formats: 12345-678-90, 1234567890, 12345678901, 1234-5678-90
           - Common positions:Always have a new column in front of product name or description (it is not found in description it has different column only and each has different sku number)
           - If there is product then there must be sku number since every product has unique sku number
           - If not found, generate a unique 10-11 digit code starting with '999'
           
        2. For product descriptions:
           - Keep the full description including strength and form (e.g., "Lofena 25MG TABS (DICLOFENAC 25MG)")
           - Include both brand and generic names when present
           
        3. For each item, you MUST include these fields:
           - sku_ndc_number: The NDC/SKU (MANDATORY, extract from description if needed)
           - description_of_goods: Full product description
           - quantity: As a number
           - rate: Price per unit as number
           - amount: Total amount as number
           - uqc: Unit of measure (CT, EA, BTL, etc.)
           
           
        EXAMPLE ITEM:
        {
          "sku_ndc_number": "15370018060",  // Or generated code if not found
          "description_of_goods": "Lofena 25MG TABS (DICLOFENAC 25MG)",
          "quantity": 24,
          "rate": 365,
          "amount": 8760,
          "uqc": "CT"
        }
        
        For invoices with multiple items, create an array of items with all their details.
        
        Return the response in this exact JSON structure:
        {
          "company_info": {
            "company_name": "string",
            "company_address": "string",
            "city": "string",
            "state": "string",
            "pincode": "string",
            "gstin": "string",
            "email": "string",
            "phone": "string"
          },
          "invoice_info": {
            "invoice_number": "string",
            "issue_date": "string",
            "due_date": "string",
            "payment_terms": "string",
            "sales_person": "string",
            "order_number": "string"
          },
          "billing_info": {
            "bill_to_name": "string",
            "bill_to_address": "string",
            "bill_to_city": "string",
            "bill_to_state": "string",
            "bill_to_pincode": "string",
            "bill_to_gstin": "string"
          },
          "shipping_info": {
            "ship_to_name": "string",
            "ship_to_address": "string",
            "ship_to_city": "string",
            "ship_to_state": "string",
            "ship_to_pincode": "string"
          },
          "items": [
            {
              "sku_ndc_number": "string (10-11 digit NDC number, e.g., 12345-678-90 or 12345678901. Extract from product description if not explicitly listed) It is always mentioned in general case since every product has unique sku",
              "description_of_goods": "string (full product description including brand and generic names, e.g., 'Lofena 25MG TABS (DICLOFENAC 25MG)')",
              "quantity": "number (quantity as a number, not string)",
              "rate": "number (price per unit as number, not string)",
              "amount": "number (total for this line item as number, not string)",
              "uqc": "string (unit of measure, e.g., 'CT' for count, 'BOX', 'BTL', 'EA')",
              "expiry_date": "string (MM/YYYY or DD/MM/YYYY if available, extract from description if needed)"
            }
          ],
          "totals": {
            "subtotal": "number (sum of all line items before tax and discounts)",
            "shipping": "number (shipping/handling charges if any)",
            "discount": "number (any discounts applied)",
            "tax": "number (total tax amount)",
            "total_invoice": "number (final total amount to pay)"
          },
          "tax_info": {
            "cgst": "number (if applicable)",
            "sgst": "number (if applicable)",
            "igst": "number (if applicable)"
          },
          "additional_info": {
            "notes": "string",
            "terms_and_conditions": "string"
          }
        }
        
        IMPORTANT INSTRUCTIONS:
        1. If any field is not present or not applicable, set it to null
        2. For items array, include ALL items found on the invoice with their complete details
        3. Make sure all numerical values are properly formatted as numbers, not strings
        4. Only extract data that is actually present on the invoice
        5. Do not make up or assume any values
        6. For SKU (NDC Number), ensure to extract the NDC number if available
        7. For product names, include both brand and generic names if available"""
        
        # Generate content
        response = MODEL.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_data}])
        
        # Process the response
        import json
        try:
            # Try to parse the response as JSON
            result = json.loads(response.text)
            return {k: v for k, v in result.items() if v is not None}, ""
        except json.JSONDecodeError:
            # If direct JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {k: v for k, v in result.items() if v is not None}, ""
            else:
                return {}, "Could not parse the response as JSON"
    except Exception as e:
        return {}, f"Error processing image: {str(e)}"

def save_to_csv(data: Dict[str, str], csv_file: str) -> bool:
    """Save extracted data to CSV file."""
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

class InvoiceExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Data Extractor")
        self.root.geometry("1000x700")
        
        # Variables
        self.image_path = ""
        self.extracted_data = {}
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        # Top frame for buttons
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Upload button
        btn_upload = ttk.Button(top_frame, text="Upload Invoice Image", command=self.upload_image)
        btn_upload.pack(side=tk.LEFT, padx=5)
        
        # Extract button
        btn_extract = ttk.Button(top_frame, text="Extract Data", command=self.extract_data)
        btn_extract.pack(side=tk.LEFT, padx=5)
        
        # Save button
        btn_save = ttk.Button(top_frame, text="Save to CSV", command=self.save_data)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        # Image display area
        self.image_label = ttk.Label(self.root, text="Upload an invoice image to begin")
        self.image_label.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Results area
        results_frame = ttk.LabelFrame(self.root, text="Extracted Data", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a canvas with scrollbar for the results
        canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def upload_image(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png"),
            ("All files", "*.*")
        ]
        
        self.image_path = filedialog.askopenfilename(
            title="Select an invoice image",
            filetypes=filetypes
        )
        
        if self.image_path:
            try:
                # Load and display the image
                image = Image.open(self.image_path)
                # Resize image to fit in the window
                image.thumbnail((800, 500))
                photo = ImageTk.PhotoImage(image)
                
                self.image_label.config(image=photo)
                self.image_label.image = photo  # Keep a reference
                self.status_var.set(f"Loaded: {os.path.basename(self.image_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def extract_data(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "Please upload an invoice image first")
            return
        
        # Show loading state
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        loading_label = ttk.Label(self.scrollable_frame, text="Extracting data, please wait...")
        loading_label.pack(pady=20)
        
        # Add a progress bar
        progress = ttk.Progressbar(self.scrollable_frame, mode='indeterminate')
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start(10)
        
        self.root.update()
        
        try:
            # Extract data from image
            self.extracted_data, error = extract_fields_from_image(self.image_path)
            
            if error:
                raise Exception(error)
            
            # Clear loading widgets
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            if not self.extracted_data:
                ttk.Label(self.scrollable_frame, text="No data extracted").pack()
                return
            
            # Create a treeview for better data display
            style = ttk.Style()
            style.configure("Treeview", rowheight=30)  # Increase row height
            
            # Create a frame for the treeview and scrollbars
            tree_frame = ttk.Frame(self.scrollable_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Add scrollbars
            y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
            x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
            
            # Create the treeview
            tree = ttk.Treeview(
                tree_frame,
                columns=("Value"),
                show="headings",
                yscrollcommand=y_scroll.set,
                xscroll=x_scroll.set
            )
            
            # Configure the columns
            tree.heading("#0", text="Field", anchor=tk.W)
            tree.heading("Value", text="Value", anchor=tk.W)
            tree.column("#0", width=250, stretch=tk.NO)
            tree.column("Value", width=500, stretch=tk.YES)
            
            # Configure the scrollbars
            y_scroll.config(command=tree.yview)
            x_scroll.config(command=tree.xview)
            
            # Add data to the treeview
            for key, value in self.extracted_data.items():
                if value:  # Only add non-empty values
                    tree.insert("", tk.END, text=key, values=(value,))
            
            # Pack the treeview and scrollbars
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Add some padding and styling
            style = ttk.Style()
            style.configure("Treeview", rowheight=30, font=('Arial', 10))
            style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
            
            self.status_var.set(f"Successfully extracted {len(self.extracted_data)} fields")
            
        except Exception as e:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            ttk.Label(
                self.scrollable_frame, 
                text=f"Error: {str(e)}",
                foreground="red"
            ).pack(pady=20)
            self.status_var.set("Error extracting data")
        finally:
            if 'progress' in locals():
                progress.stop()
                progress.destroy()
    
    def save_data(self):
        if not self.extracted_data:
            messagebox.showwarning("Warning", "No data to save. Please extract data first.")
            return
        
        # Default file path
        default_file = os.path.join(os.getcwd(), "extracted_invoices.csv")
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.isfile(default_file)
        
        try:
            # Save to the default file (append mode)
            with open(default_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.extracted_data.keys())
                
                # Write header only if file is being created
                if not file_exists:
                    writer.writeheader()
                
                # Write the data
                writer.writerow(self.extracted_data)
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"Data appended to:\n{default_file}\n\n"
                f"Total invoices saved: {self.count_invoices_in_csv(default_file)}"
            )
            self.status_var.set(f"Data appended to {os.path.basename(default_file)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def count_invoices_in_csv(self, filepath):
        """Count the number of invoices in the CSV file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f) - 1  # Subtract 1 for header
        except FileNotFoundError:
            return 0

if __name__ == '__main__':
    if not MODEL:
        messagebox.showerror("Error", "Failed to initialize Gemini API. Please check your API key in the .env file.")
    else:
        root = tk.Tk()
        app = InvoiceExtractorApp(root)
        root.mainloop()
