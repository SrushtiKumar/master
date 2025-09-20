"""
Document steganography module for PDF and DOCX files.
"""

import io
import logging
from typing import Dict, Any
import pikepdf
from docx import Document
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentSteganography:
    """Implements steganography for document files (PDF and DOCX)."""
    
    def __init__(self):
        pass
    
    def embed_pdf(self, pdf_data, payload, seed):
        """Embed payload into PDF using object stream."""
        try:
            # Open the PDF
            with pikepdf.Pdf.open(io.BytesIO(pdf_data)) as pdf:
                # Create a custom metadata object to store the payload
                # In a real implementation, this would be more sophisticated
                # and would use proper steganography techniques
                pdf.Root.Stego = pikepdf.Stream(pdf, payload)
                
                # Save the modified PDF
                output = io.BytesIO()
                pdf.save(output)
                
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error embedding payload in PDF: {str(e)}")
            raise
    
    def extract_pdf(self, pdf_data, seed):
        """Extract payload from PDF."""
        try:
            # Open the PDF
            with pikepdf.Pdf.open(io.BytesIO(pdf_data)) as pdf:
                # Extract the payload from the custom metadata
                if hasattr(pdf.Root, 'Stego'):
                    return bytes(pdf.Root.Stego.read_bytes())
                else:
                    raise ValueError("No steganographic payload found in PDF")
                
        except Exception as e:
            logger.error(f"Error extracting payload from PDF: {str(e)}")
            raise
    
    def embed_docx(self, docx_data, payload, seed):
        """Embed payload into DOCX using customXml."""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as input_file, \
                 tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as output_file:
                
                # Write input DOCX data
                input_file.write(docx_data)
                input_file.flush()
                
                # Open the document
                doc = Document(input_file.name)
                
                # Add a custom property to store the payload
                # In a real implementation, this would use proper steganography
                # techniques like hiding in customXml parts
                core_props = doc.core_properties
                core_props.comments = payload.hex()
                
                # Save the modified document
                doc.save(output_file.name)
                
                # Read the output file
                output_file.close()
                with open(output_file.name, 'rb') as f:
                    result = f.read()
                
                # Clean up temporary files
                os.unlink(input_file.name)
                os.unlink(output_file.name)
                
                return result
                
        except Exception as e:
            logger.error(f"Error embedding payload in DOCX: {str(e)}")
            raise
    
    def extract_docx(self, docx_data, seed):
        """Extract payload from DOCX."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as input_file:
                
                # Write input DOCX data
                input_file.write(docx_data)
                input_file.flush()
                
                # Open the document
                doc = Document(input_file.name)
                
                # Extract the payload from the custom property
                core_props = doc.core_properties
                if core_props.comments:
                    payload = bytes.fromhex(core_props.comments)
                else:
                    raise ValueError("No steganographic payload found in DOCX")
                
                # Clean up temporary file
                input_file.close()
                os.unlink(input_file.name)
                
                return payload
                
        except Exception as e:
            logger.error(f"Error extracting payload from DOCX: {str(e)}")
            raise
    
    def embed(self, document_data, payload, seed, document_type=None):
        """Embed payload into document (auto-detect type if not specified)."""
        if document_type == 'pdf' or (document_type is None and document_data[:4] == b'%PDF'):
            return self.embed_pdf(document_data, payload, seed)
        elif document_type == 'docx' or (document_type is None and document_data[:2] == b'PK'):
            return self.embed_docx(document_data, payload, seed)
        else:
            raise ValueError("Unsupported document type")
    
    def extract(self, document_data, seed, document_type=None):
        """Extract payload from document (auto-detect type if not specified)."""
        if document_type == 'pdf' or (document_type is None and document_data[:4] == b'%PDF'):
            return self.extract_pdf(document_data, seed)
        elif document_type == 'docx' or (document_type is None and document_data[:2] == b'PK'):
            return self.extract_docx(document_data, seed)
        else:
            raise ValueError("Unsupported document type")
    
    def analyze_capacity(self, document_data, document_type=None):
        """Analyze the capacity of a document for steganography."""
        try:
            # Determine document type
            if document_type == 'pdf' or (document_type is None and document_data[:4] == b'%PDF'):
                # For PDF, estimate based on file size
                capacity_bytes = len(document_data) // 100  # Conservative estimate
                
                return {
                    "type": "pdf",
                    "size_bytes": len(document_data),
                    "capacity_bytes": capacity_bytes,
                    "recommended_max_payload": capacity_bytes // 2
                }
                
            elif document_type == 'docx' or (document_type is None and document_data[:2] == b'PK'):
                # For DOCX, estimate based on file size
                capacity_bytes = len(document_data) // 200  # More conservative for DOCX
                
                return {
                    "type": "docx",
                    "size_bytes": len(document_data),
                    "capacity_bytes": capacity_bytes,
                    "recommended_max_payload": capacity_bytes // 2
                }
                
            else:
                raise ValueError("Unsupported document type")
                
        except Exception as e:
            logger.error(f"Error analyzing document capacity: {str(e)}")
            # Return a minimal estimate if analysis fails
            return {
                "capacity_bytes": 1000,  # Conservative default
                "recommended_max_payload": 500
            }