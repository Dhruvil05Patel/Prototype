import { useState, useRef } from 'react'
import './App.css'

// Component to display structured invoice data
const InvoiceDataDisplay = ({ data }) => {
  const renderSection = (title, sectionData, icon) => {
    if (!sectionData || Object.keys(sectionData).length === 0) return null
    
    return (
      <div className="mb-6 bg-gray-50 rounded-lg p-4">
        <div className="flex items-center mb-3">
          {icon}
          <h3 className="text-md font-semibold text-gray-800 ml-2">{title}</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(sectionData).map(([key, value]) => 
            (value !== null && value !== undefined && value !== '' && value !== '0') && (
              <div key={key} className="bg-white p-3 rounded border">
                <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  {key.replace(/_/g, ' ')}
                </dt>
                <dd className="text-sm text-gray-900 font-medium">{value}</dd>
              </div>
            )
          )}
        </div>
      </div>
    )
  }

  // Function to extract NDC/SKU from product description
  const extractNDC = (description) => {
    if (!description) return null;
    
    // Try different NDC patterns in order of preference
    const patterns = [
      // NDC format: 12345-678-90 or 12345-6789-0 or 1234-5678-90
      /(?:NDC|SKU)[:\s]*([0-9]{4,5}-?[0-9]{3,4}-?[0-9]{1,2})/i,
      // Any 10-11 digit number, possibly with hyphens
      /([0-9]{4,5}-?[0-9]{3,4}-?[0-9]{1,2})/,
      // Numbers in parentheses at the end of the description
      /(?:\(|\b)([0-9]{4,5}-?[0-9]{3,4}-?[0-9]{1,2})(?:\)|\b)/,
      // Any remaining numbers that might be SKUs
      /(?:SKU|Item)[:\s]*(\d+)/i
    ];
    
    for (const pattern of patterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        return match[1].replace(/\s+/g, ''); // Remove any spaces in the matched NDC
      }
    }
    
    return null;
  };

  // Function to clean up product name
  const cleanProductName = (name) => {
    if (!name) return 'N/A';
    
    // First extract the NDC if present
    const ndcMatch = name.match(/(.*?)(?:\(([0-9-]{9,})\)|(?:NDC|SKU)[:\s]*([0-9-]+)|$)/i);
    const cleanName = ndcMatch ? ndcMatch[1].trim() : name;
    
    // Remove common patterns that might be part of the description but not the name
    return cleanName
      .replace(/(?:NDC|SKU)[:\s]*[0-9-]+/gi, '')  // Remove NDC/SKU: 12345 patterns
      .replace(/\([^)]*\)/g, '')                   // Remove anything in parentheses
      .replace(/\s+/g, ' ')                         // Normalize spaces
      .trim() || 'N/A';
  };

  // Function to render the items table
  const renderItems = (items = []) => {
    if (!items || items.length === 0) return null;
    
    // Get values directly from data.totals if they exist, default to 0 if not present
    const { 
      subtotal = 0,
      shipping = 0, 
      discount = 0,
      tax = 0,
      total_invoice: total = 0
    } = data.totals || {};
    
    return (
      <div className="mb-6">
        <div className="flex items-center mb-3">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-800 ml-2">Items ({items.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU (NDC)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {items.map((item, index) => {
                const ndcNumber = extractNDC(item.description_of_goods);
                const productName = cleanProductName(item.description_of_goods);
                
                return (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{index + 1}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {item.sku_ndc_number || ndcNumber || item.hsn_code || (
                        <span className="text-gray-400 italic">Not found</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {productName}
                      </div>
                      {item.batch_no && (
                        <div className="text-xs text-gray-500">Batch: {item.batch_no}</div>
                      )}
                      {item.expiry_date && (
                        <div className="text-xs text-gray-500">Exp: {item.expiry_date}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.uqc || 'EA'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      {item.quantity ? parseFloat(item.quantity).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      {item.rate ? `$${parseFloat(item.rate).toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {item.amount ? `$${parseFloat(item.amount).toFixed(2)}` : 'N/A'}
                    </td>
                  </tr>
                );
              })}
              
              {/* Totals Section - Only show rows for values that exist and are greater than 0 */}
              {(subtotal > 0 || subtotal === 0) && (
                <tr className="bg-gray-50">
                  <td colSpan="5" className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                    Subtotal:
                  </td>
                  <td colSpan="2" className="px-6 py-3 text-right text-sm font-medium">
                    ${parseFloat(subtotal).toFixed(2)}
                  </td>
                </tr>
              )}
              
              {shipping > 0 && (
                <tr className="bg-gray-50">
                  <td colSpan="5" className="px-6 py-1 text-right text-sm text-gray-500">
                    Shipping:
                  </td>
                  <td colSpan="2" className="px-6 py-1 text-right text-sm text-gray-500">
                    ${parseFloat(shipping).toFixed(2)}
                  </td>
                </tr>
              )}
              
              {discount > 0 && (
                <tr className="bg-gray-50">
                  <td colSpan="5" className="px-6 py-1 text-right text-sm text-gray-500">
                    Discount:
                  </td>
                  <td colSpan="2" className="px-6 py-1 text-right text-sm text-red-600">
                    -${parseFloat(discount).toFixed(2)}
                  </td>
                </tr>
              )}
              
              {tax > 0 && (
                <tr className="bg-gray-50">
                  <td colSpan="5" className="px-6 py-1 text-right text-sm text-gray-500">
                    Tax:
                  </td>
                  <td colSpan="2" className="px-6 py-1 text-right text-sm text-gray-500">
                    ${parseFloat(tax).toFixed(2)}
                  </td>
                </tr>
              )}
              
              {/* Total row - always show */}
              <tr className="bg-gray-100 border-t-2 border-gray-300">
                <td colSpan="5" className="px-6 py-3 text-right text-lg font-bold text-gray-900">
                  TOTAL:
                </td>
                <td colSpan="2" className="px-6 py-3 text-right text-lg font-bold text-gray-900">
                  ${parseFloat(total).toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Company Information */}
      {renderSection(
        'Pharmacy Information',
        data.company_info,
        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )}

      {/* Invoice Information */}
      {renderSection(
        'Invoice Details',
        data.invoice_info,
        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      )}

      {/* Billing Information */}
      {renderSection(
        'Bill To',
        data.billing_info,
        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )}

      {/* Shipping Information */}
      {renderSection(
        'Ship To',
        data.shipping_info,
        <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0 2 2 0 000-4z" />
        </svg>
      )}

      {/* Items */}
      {renderItems(data.items)}

      {/* Tax Information */}
      {renderSection(
        'Tax Information',
        data.tax_info,
        <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      )}

      {/* Totals */}
      {data.summary && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Order Summary</h3>
          <div className="max-w-md ml-auto">
            <div className="space-y-2">
              {data.summary.subtotal !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal:</span>
                  <span className="font-medium">₹{parseFloat(data.summary.subtotal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
              )}
              {data.summary.shipping !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Shipping:</span>
                  <span className="font-medium">₹{parseFloat(data.summary.shipping).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
              )}
              {data.summary.discount !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Discount:</span>
                  <span className="font-medium text-red-600">-₹{parseFloat(data.summary.discount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
              )}
              {data.summary.tax !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tax:</span>
                  <span className="font-medium">₹{parseFloat(data.summary.tax).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
              )}
              <div className="border-t border-gray-200 my-2"></div>
              {data.summary.total_amount !== undefined && (
                <div className="flex justify-between text-base font-bold">
                  <span>Total Amount:</span>
                  <span className="text-blue-600">₹{parseFloat(data.summary.total_amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Additional Information */}
      {data.additional_info && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {data.additional_info.notes && (
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Notes</h3>
              <p className="text-sm text-gray-700">{data.additional_info.notes}</p>
            </div>
          )}
          {data.additional_info.terms_and_conditions && (
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Terms & Conditions</h3>
              <p className="text-sm text-gray-700">{data.additional_info.terms_and_conditions}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [extractedData, setExtractedData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      setError(null)
      setExtractedData(null)
    } else {
      setError('Please select a valid image file (JPG, PNG, etc.)')
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    handleFileSelect(file)
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const file = e.dataTransfer.files[0]
    handleFileSelect(file)
  }

  const extractData = async () => {
    if (!selectedFile) return

    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/extract', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to extract data from invoice')
      }

      const data = await response.json()
      setExtractedData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const downloadCSV = async () => {
    if (!extractedData) return

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/download-csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(extractedData),
      })

      if (!response.ok) {
        throw new Error('Failed to generate CSV')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = 'extracted_invoice_data.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download CSV: ' + err.message)
    }
  }

  const downloadJSON = async () => {
    if (!extractedData) return

    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/download-json', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(extractedData),
      })

      if (!response.ok) {
        throw new Error('Failed to generate JSON')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = 'extracted_invoice_data.json'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download JSON: ' + err.message)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Invoice Data Extractor</h1>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Ready</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Invoice</h2>
              
              {/* Drag and Drop Area */}
              <div
                className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : selectedFile
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-xs text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-900">Drop your invoice here</p>
                    <p className="text-xs text-gray-500">or click to browse files</p>
                    <p className="text-xs text-gray-400">Supports JPG, PNG, PDF</p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Choose File
                </button>
                <button
                  onClick={extractData}
                  disabled={!selectedFile || isLoading}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-all disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Processing...</span>
                    </div>
                  ) : (
                    'Extract Data'
                  )}
                </button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Preview Section */}
            {selectedFile && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Preview</h3>
                <div className="border rounded-lg overflow-hidden">
                  <img
                    src={URL.createObjectURL(selectedFile)}
                    alt="Invoice preview"
                    className="w-full h-64 object-contain bg-gray-50"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Extracted Data</h2>
                {extractedData && (
                  <div className="flex space-x-2">
                    <button
                      onClick={downloadJSON}
                      className="bg-blue-600 hover:bg-blue-700 text-black font-medium py-2 px-4 rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>JSON</span>
                    </button>
                    {/* <button
                      onClick={downloadCSV}
                      className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>CSV</span>
                    </button> */}
                  </div>
                )}
              </div>

              {extractedData ? (
                <div className="max-h-96 overflow-y-auto">
                  <InvoiceDataDisplay data={extractedData} />
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-gray-500">Upload and process an invoice to see extracted data</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
