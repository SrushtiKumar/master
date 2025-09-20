"""
Command-line interface for the steganography toolkit.
"""

import argparse
import sys
import os
import logging
from typing import Dict, Any

from stegano_toolkit.common_crypto import KeyManager, PayloadProcessor
from stegano_toolkit.image_stego import ImageSteganography
from stegano_toolkit.audio_stego import AudioSteganography
from stegano_toolkit.video_stego import VideoSteganography
from stegano_toolkit.document_stego import DocumentSteganography

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_file_type(file_path: str) -> str:
    """Detect the file type based on extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
        return 'image'
    elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
        return 'audio'
    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        return 'video'
    elif ext == '.pdf':
        return 'pdf'
    elif ext in ['.docx', '.doc']:
        return 'docx'
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def get_steganography_handler(file_type: str) -> Any:
    """Get the appropriate steganography handler for the file type."""
    if file_type == 'image':
        return ImageSteganography()
    elif file_type == 'audio':
        return AudioSteganography()
    elif file_type == 'video':
        return VideoSteganography()
    elif file_type in ['pdf', 'docx']:
        return DocumentSteganography()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def embed_command(args: argparse.Namespace) -> None:
    """Handle the embed command."""
    try:
        # Read the input file
        with open(args.input_file, 'rb') as f:
            input_data = f.read()
        
        # Read the message
        if args.message_file:
            with open(args.message_file, 'rb') as f:
                message = f.read()
        else:
            message = args.message.encode('utf-8')
        
        # Generate or load keys
        if args.key_file:
            with open(args.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate a new key
            key = KeyManager.generate_session_key()
            # Save the key if output key file is specified
            if args.output_key_file:
                with open(args.output_key_file, 'wb') as f:
                    f.write(key)
                logger.info(f"Key saved to {args.output_key_file}")
        
        # Process the payload
        payload, _ = PayloadProcessor.prepare_payload(message, key)
        
        # Detect file type and get appropriate handler
        file_type = detect_file_type(args.input_file)
        handler = get_steganography_handler(file_type)
        
        # Embed the payload
        output_data = handler.embed(input_data, payload, key)
        
        # Write the output file
        with open(args.output_file, 'wb') as f:
            f.write(output_data)
        
        logger.info(f"Payload embedded successfully in {args.output_file}")
        
    except Exception as e:
        logger.error(f"Error embedding payload: {str(e)}")
        sys.exit(1)

def extract_command(args: argparse.Namespace) -> None:
    """Handle the extract command."""
    try:
        # Read the input file
        with open(args.input_file, 'rb') as f:
            input_data = f.read()
        
        # Read the key
        with open(args.key_file, 'rb') as f:
            key = f.read()
        
        # Detect file type and get appropriate handler
        file_type = detect_file_type(args.input_file)
        handler = get_steganography_handler(file_type)
        
        # Extract the payload
        payload = handler.extract(input_data, key, args.payload_size)
        
        # Process the payload
        message = PayloadProcessor.extract_payload(payload, key)
        
        # Write the output message
        if args.output_file:
            with open(args.output_file, 'wb') as f:
                f.write(message)
            logger.info(f"Message extracted and saved to {args.output_file}")
        else:
            # Try to decode as UTF-8 and print
            try:
                print(message.decode('utf-8'))
            except UnicodeDecodeError:
                logger.warning("Message is not UTF-8 text. Use --output-file to save binary data.")
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error extracting payload: {str(e)}")
        sys.exit(1)

def analyze_command(args: argparse.Namespace) -> None:
    """Handle the analyze command."""
    try:
        # Read the input file
        with open(args.input_file, 'rb') as f:
            input_data = f.read()
        
        # Detect file type and get appropriate handler
        file_type = detect_file_type(args.input_file)
        handler = get_steganography_handler(file_type)
        
        # Analyze capacity
        capacity_info = handler.analyze_capacity(input_data)
        
        # Print capacity information
        print(f"File: {args.input_file}")
        print(f"Type: {file_type}")
        for key, value in capacity_info.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        sys.exit(1)

def generate_keys_command(args: argparse.Namespace) -> None:
    """Handle the generate-keys command."""
    try:
        # Generate keys
        if args.type == 'session':
            key = KeyManager.generate_session_key()
            with open(args.output_file, 'wb') as f:
                f.write(key)
            logger.info(f"Session key generated and saved to {args.output_file}")
        elif args.type == 'exchange':
            private_key, public_key = KeyManager.generate_keypair()
            with open(args.output_file, 'wb') as f:
                f.write(private_key)
            with open(f"{args.output_file}.pub", 'wb') as f:
                f.write(public_key)
            logger.info(f"Key pair generated and saved to {args.output_file} and {args.output_file}.pub")
        elif args.type == 'signing':
            private_key, public_key = KeyManager.generate_signing_keypair()
            with open(args.output_file, 'wb') as f:
                f.write(private_key)
            with open(f"{args.output_file}.pub", 'wb') as f:
                f.write(public_key)
            logger.info(f"Signing key pair generated and saved to {args.output_file} and {args.output_file}.pub")
        
    except Exception as e:
        logger.error(f"Error generating keys: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Steganography Toolkit')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Embed command
    embed_parser = subparsers.add_parser('embed', help='Embed a message in a file')
    embed_parser.add_argument('input_file', help='Input file path')
    embed_parser.add_argument('output_file', help='Output file path')
    message_group = embed_parser.add_mutually_exclusive_group(required=True)
    message_group.add_argument('--message', help='Message to embed')
    message_group.add_argument('--message-file', help='File containing the message to embed')
    key_group = embed_parser.add_mutually_exclusive_group()
    key_group.add_argument('--key-file', help='File containing the encryption key')
    key_group.add_argument('--output-key-file', help='File to save the generated key')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract a message from a file')
    extract_parser.add_argument('input_file', help='Input file path')
    extract_parser.add_argument('--output-file', help='Output file path for the extracted message')
    extract_parser.add_argument('--key-file', required=True, help='File containing the encryption key')
    extract_parser.add_argument('--payload-size', type=int, default=1024, help='Expected payload size in bytes')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a file for steganography capacity')
    analyze_parser.add_argument('input_file', help='Input file path')
    
    # Generate keys command
    generate_keys_parser = subparsers.add_parser('generate-keys', help='Generate cryptographic keys')
    generate_keys_parser.add_argument('--type', choices=['session', 'exchange', 'signing'], default='session',
                                     help='Type of key to generate')
    generate_keys_parser.add_argument('output_file', help='Output file path for the key')
    
    args = parser.parse_args()
    
    if args.command == 'embed':
        embed_command(args)
    elif args.command == 'extract':
        extract_command(args)
    elif args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'generate-keys':
        generate_keys_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()