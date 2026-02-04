#!/usr/bin/env python3
"""
Invoice Processor - Simple PDF Invoice Data Extractor
=====================================================
A lightweight tool for extracting key data from PDF invoices.
Perfect for small businesses starting with AI automation.

Author: Saga AI Team
Version: 0.1.0
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InvoiceProcessor:
    """Extract data from PDF invoice files."""
    
    def __init__(self):
        self.patterns = {
            'amount': [
                r'(?:Total|Summa|Belopp|Amount)[\s:]*([\d\s.,]+(?:\s*kr|SEK|USD|EUR)?)',
                r'(?:Att betala|To pay)[\s:]*([\d\s.,]+)',
                r'(?:Totalt|Total)[\s:]*([\d\s.,]+(?:\s*kr)?)',
            ],
            'date': [
                r'(?:Fakturadatum|Invoice date|Date)[\s:]*(\d{4}-\d{2}-\d{2})',
                r'(?:Fakturadatum|Invoice date|Date)[\s:]*(\d{2}/\d{2}/\d{4})',
                r'(?:Fakturadatum|Invoice date|Date)[\s:]*(\d{2}\.\d{2}\.\d{4})',
                r'(\d{4}-\d{2}-\d{2})',  # Fallback: any YYYY-MM-DD
            ],
            'due_date': [
                r'(?:Förfallodatum|Due date|Betala senast)[\s:]*(\d{4}-\d{2}-\d{2})',
                r'(?:Förfallodatum|Due date)[\s:]*(\d{2}/\d{2}/\d{4})',
            ],
            'invoice_number': [
                r'(?:Fakturanummer|Invoice number|Faktura nr)[\s:]*([A-Z0-9\-]+)',
                r'(?:Invoice #|Faktura #)[\s:]*([A-Z0-9\-]+)',
            ],
            'vendor': [
                r'(?:Från|From|Leverantör|Vendor)[\s:]*\n?([^\n]{3,50})',
                r'^([A-Z][A-Za-z0-9\s]+(?:AB|Ltd|Inc|LLC|HB)?)\s*$',
            ],
            'vat': [
                r'(?:Moms|VAT|Momsbelopp)[\s:]*([\d\s.,]+)',
                r'(?:VAT amount)[\s:]*([\d\s.,]+)',
            ]
        }
    
    def extract_from_text(self, text: str) -> Dict[str, Optional[str]]:
        """Extract invoice data from text using regex patterns."""
        results = {}
        
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    # Clean up amount formats
                    if field in ['amount', 'vat']:
                        value = self._clean_amount(value)
                    results[field] = value
                    break
            else:
                results[field] = None
        
        return results
    
    def _clean_amount(self, amount_str: str) -> str:
        """Clean and standardize amount strings."""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[\s]', '', amount_str)
        cleaned = re.sub(r'(kr|SEK|USD|EUR|€|\$)', '', cleaned, flags=re.IGNORECASE)
        
        # Handle Swedish format (1.234,56 -> 1234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                # Swedish: 1.234,56
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US: 1,234.56
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Could be decimal comma
            if len(cleaned.split(',')[-1]) == 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        return cleaned
    
    def process_file(self, file_path: Path) -> Dict:
        """Process a single invoice file."""
        logger.info(f"Processing: {file_path}")
        
        try:
            # Read file (currently supports text files, PDF support requires PyPDF2)
            if file_path.suffix.lower() == '.pdf':
                text = self._read_pdf(file_path)
            else:
                text = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Extract data
            data = self.extract_from_text(text)
            data['filename'] = file_path.name
            data['processed_at'] = datetime.now().isoformat()
            data['status'] = 'success'
            
            return data
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return {
                'filename': file_path.name,
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def _read_pdf(self, file_path: Path) -> str:
        """Read text from PDF file."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return "[PDF support requires PyPDF2]"
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return ""
    
    def batch_process(self, directory: Path, output_file: Optional[Path] = None) -> List[Dict]:
        """Process all invoices in a directory."""
        results = []
        
        # Find all invoice files
        patterns = ['*.txt', '*.pdf', '*.csv']
        files = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))
        
        logger.info(f"Found {len(files)} files to process")
        
        for file_path in files:
            result = self.process_file(file_path)
            results.append(result)
        
        # Save results
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {output_file}")
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a summary report."""
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        total_amount = 0.0
        
        for r in results:
            if r.get('amount'):
                try:
                    total_amount += float(r['amount'])
                except ValueError:
                    pass
        
        report = f"""
INVOICE PROCESSING REPORT
=========================
Processed: {total} files
Successful: {successful}
Failed: {total - successful}

Total Amount Extracted: {total_amount:,.2f}

Status Breakdown:
- Successfully processed: {successful}
- Errors: {total - successful}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return report


def main():
    parser = argparse.ArgumentParser(
        description='Invoice Processor - Extract data from invoice files'
    )
    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('-o', '--output', help='Output JSON file')
    parser.add_argument('-r', '--report', action='store_true', help='Generate summary report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = InvoiceProcessor()
    path = Path(args.path)
    
    if path.is_file():
        # Process single file
        result = processor.process_file(path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif path.is_dir():
        # Process directory
        output_file = Path(args.output) if args.output else path / 'results.json'
        results = processor.batch_process(path, output_file)
        
        if args.report:
            report = processor.generate_report(results)
            print(report)
        else:
            print(f"Processed {len(results)} files")
            print(f"Results saved to: {output_file}")
    
    else:
        print(f"Error: Path not found: {path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
