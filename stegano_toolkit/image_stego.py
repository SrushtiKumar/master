"""
Image steganography module using 2-level DWT on the Y channel and QIM.
"""

import numpy as np
import io
import logging
import cv2
import pywt
from PIL import Image
from .common_crypto import PayloadProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageSteganography:
    """
    Image steganography class using 2-level DWT on the Y channel and QIM.
    """
    
    def __init__(self):
        """Initialize the image steganography object."""
        self.payload_processor = PayloadProcessor()
        
    def _convert_to_ycbcr(self, img):
        """Convert RGB image to YCbCr color space."""
        if isinstance(img, np.ndarray):
            return cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
        else:
            return img.convert('YCbCr')
    
    def _convert_to_rgb(self, img):
        """Convert YCbCr image to RGB color space."""
        if isinstance(img, np.ndarray):
            return cv2.cvtColor(img, cv2.COLOR_YCrCb2RGB)
        else:
            return img.convert('RGB')
    
    def _apply_dwt(self, y_channel):
        """Apply 2-level DWT to Y channel."""
        coeffs = pywt.wavedec2(y_channel, 'haar', level=2)
        return coeffs
    
    def _inverse_dwt(self, coeffs):
        """Apply inverse 2-level DWT."""
        return pywt.waverec2(coeffs, 'haar')
    
    def _embed_in_coeffs(self, coeffs, payload_bits, key):
        """Embed payload bits in DWT coefficients using QIM."""
        # Get the horizontal detail coefficients from level 2
        h_coeffs = coeffs[1][1].copy()
        
        # QIM parameters
        delta = 20  # Quantization step
        
        # Flatten coefficients for embedding
        flat_coeffs = h_coeffs.flatten()
        
        # Ensure we have enough capacity
        if len(payload_bits) > len(flat_coeffs):
            raise ValueError(f"Payload too large. Max capacity: {len(flat_coeffs)} bits")
        
        # Embed using QIM
        for i in range(len(payload_bits)):
            bit = payload_bits[i]
            coeff = flat_coeffs[i]
            
            # QIM embedding
            if bit == 0:
                flat_coeffs[i] = delta * round(coeff / delta)
            else:
                flat_coeffs[i] = delta * round(coeff / delta + 0.5) - delta/2
        
        # Reshape back to original shape
        h_coeffs = flat_coeffs.reshape(h_coeffs.shape)
        
        # Update coefficients
        coeffs[1] = (coeffs[1][0], h_coeffs, coeffs[1][2])
        
        return coeffs
    
    def _extract_from_coeffs(self, coeffs, payload_length, key):
        """Extract payload bits from DWT coefficients using QIM."""
        # Get the horizontal detail coefficients from level 2
        h_coeffs = coeffs[1][1]
        
        # QIM parameters
        delta = 20  # Quantization step
        
        # Flatten coefficients for extraction
        flat_coeffs = h_coeffs.flatten()
        
        # Extract bits
        payload_bits = []
        for i in range(payload_length):
            if i >= len(flat_coeffs):
                break
                
            coeff = flat_coeffs[i]
            
            # QIM extraction
            q0 = delta * round(coeff / delta)
            q1 = delta * round(coeff / delta + 0.5) - delta/2
            
            # Determine which quantizer is closer
            if abs(coeff - q0) < abs(coeff - q1):
                payload_bits.append(0)
            else:
                payload_bits.append(1)
        
        return payload_bits
    
    def embed(self, image_data, payload, key=None):
        """
        Embed payload in image using 2-level DWT and QIM.
        
        Args:
            image_data: Image data as bytes or file-like object
            payload: String payload to embed
            key: Optional encryption key
            
        Returns:
            Bytes of stego image in PNG format
        """
        # Process payload
        payload_bits = self.payload_processor.prepare_payload(payload, key)
        
        # Open image
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(image_data)
        
        # Convert to YCbCr
        ycbcr = self._convert_to_ycbcr(img)
        
        # Split channels
        y, cb, cr = ycbcr.split()
        
        # Convert to numpy array
        y_array = np.array(y)
        
        # Apply DWT
        coeffs = self._apply_dwt(y_array)
        
        # Embed payload
        modified_coeffs = self._embed_in_coeffs(coeffs, payload_bits, key)
        
        # Apply inverse DWT
        modified_y = self._inverse_dwt(modified_coeffs)
        
        # Ensure values are in valid range
        modified_y = np.clip(modified_y, 0, 255).astype(np.uint8)
        
        # Create new Y channel image
        modified_y_img = Image.fromarray(modified_y)
        
        # Merge channels
        modified_ycbcr = Image.merge('YCbCr', (modified_y_img, cb, cr))
        
        # Convert back to RGB
        stego_img = self._convert_to_rgb(modified_ycbcr)
        
        # Save to bytes
        output = io.BytesIO()
        stego_img.save(output, format='PNG')
        
        return output.getvalue()
    
    def extract(self, stego_data, key=None):
        """
        Extract payload from stego image.
        
        Args:
            stego_data: Stego image data as bytes or file-like object
            key: Optional decryption key
            
        Returns:
            Extracted payload as string
        """
        # Open stego image
        if isinstance(stego_data, bytes):
            stego_img = Image.open(io.BytesIO(stego_data))
        else:
            stego_img = Image.open(stego_data)
        
        # Convert to YCbCr
        ycbcr = self._convert_to_ycbcr(stego_img)
        
        # Get Y channel
        y, _, _ = ycbcr.split()
        
        # Convert to numpy array
        y_array = np.array(y)
        
        # Apply DWT
        coeffs = self._apply_dwt(y_array)
        
        # Get payload length (first 32 bits)
        length_bits = self._extract_from_coeffs(coeffs, 32, key)
        payload_length = int(''.join(map(str, length_bits)), 2)
        
        # Extract payload bits
        payload_bits = self._extract_from_coeffs(coeffs, 32 + payload_length, key)
        
        # Process extracted bits
        payload = self.payload_processor.extract_payload(payload_bits, key)
        
        return payload
    
    def analyze_capacity(self, image_data):
        """
        Analyze the capacity of an image for steganography.
        
        Args:
            image_data: Image data as bytes or file-like object
            
        Returns:
            Dictionary with capacity information
        """
        # Open image
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        else:
            img = Image.open(image_data)
        
        # Convert to YCbCr
        ycbcr = self._convert_to_ycbcr(img)
        
        # Get Y channel
        y, _, _ = ycbcr.split()
        
        # Convert to numpy array
        y_array = np.array(y)
        
        # Apply DWT
        coeffs = self._apply_dwt(y_array)
        
        # Get horizontal detail coefficients
        h_coeffs = coeffs[1][1]
        
        # Calculate capacity
        total_coeffs = h_coeffs.size
        usable_bits = total_coeffs - 32  # Subtract header size
        usable_bytes = usable_bits // 8
        
        return {
            'total_coefficients': total_coeffs,
            'usable_bits': usable_bits,
            'usable_bytes': usable_bytes,
            'image_size_bytes': img.size[0] * img.size[1] * len(img.getbands()),
            'efficiency_ratio': usable_bytes / (img.size[0] * img.size[1] * len(img.getbands()))
        }