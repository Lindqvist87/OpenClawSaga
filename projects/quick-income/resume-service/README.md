# AI Resume Optimizer v2.0.0

A production-ready Python script for analyzing and optimizing CVs for ATS (Applicant Tracking Systems) and human recruiters.

## Features

- **PDF Support**: Read and analyze PDF resumes using PyPDF2
- **Multiple Formats**: Support for TXT, MD, DOCX (with python-docx), and PDF files
- **ATS Scoring**: 0-100 score with detailed breakdown across 6 categories:
  - Contact Information (15 points)
  - Resume Structure (20 points)
  - Content Quality (20 points)
  - Keyword Matching (20 points)
  - Formatting (10 points)
  - Readability (15 points)
- **Keyword Analysis**: Industry-specific keyword extraction and suggestions
- **Multiple Report Formats**: JSON, human-readable, Markdown, and HTML
- **Swedish CV Support**: Handles Swedish phone formats (07X-XXX XX XX), Swedish characters (åäö), and Swedish-specific suggestions
- **Before/After Comparison**: Shows sample improvements with weak phrase replacements
- **Comprehensive Logging**: Debug logging to file for troubleshooting
- **Error Handling**: Graceful handling of empty files, corrupted PDFs, large files (>10MB)

## Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Or install individually
pip install PyPDF2 python-docx
```

## Usage

### Basic Usage

```bash
# Analyze a PDF resume
python resume_optimizer.py resume.pdf --job "Software Engineer"

# Analyze with specific output file
python resume_optimizer.py cv.txt --job "Sales Manager" --output report.txt

# Generate HTML report
python resume_optimizer.py resume.docx --format html --output report.html

# Swedish CV analysis
python resume_optimizer.py mitt-cv.pdf --job "Systemutvecklare" --lang sv
```

### Command-Line Options

```
positional arguments:
  file                  Resume file (PDF, TXT, DOCX, or MD)

optional arguments:
  -h, --help            Show help message
  --job JOB, -j JOB     Target job title
  --industry INDUSTRY, -i INDUSTRY
                        Target industry (overrides auto-detect)
  --output OUTPUT, -o OUTPUT
                        Output file path
  --format {json,human,markdown,html}, -f {json,human,markdown,html}
                        Output format (default: human)
  --lang {en,sv,auto}, -l {en,sv,auto}
                        Language (default: auto)
  --create-sample       Create a sample resume for testing
  --verbose, -v         Enable verbose logging
  --version             Show version
```

### Examples

```bash
# Create a sample resume for testing
python resume_optimizer.py --create-sample --output my_resume.txt

# Analyze with verbose logging
python resume_optimizer.py resume.pdf --job "Data Scientist" --verbose

# Generate JSON report for API integration
python resume_optimizer.py cv.pdf --format json --output analysis.json

# Analyze Swedish resume
python resume_optimizer.py cv_se.pdf --job "Projektledare" --lang sv --format html
```

## ATS Scoring Algorithm

The script calculates an ATS compatibility score (0-100) based on:

| Category | Points | Criteria |
|----------|--------|----------|
| Contact Info | 15 | Has email + phone |
| Structure | 20 | Summary, Experience, Education, Skills sections |
| Content Quality | 20 | Power verbs variety, quantified achievements |
| Keywords | 20 | Industry keyword coverage |
| Formatting | 10 | Bullet points, bullet quality |
| Readability | 15 | Optimal word count (300-600) |

**Score Interpretation:**
- **90-100**: Excellent - Ready for submission
- **70-89**: Good - Minor improvements needed
- **50-69**: Needs Work - Several improvements recommended
- **0-49**: Critical - Major revisions required

## Supported Industries

The optimizer includes keyword databases for:
- **Tech**: Python, JavaScript, AWS, Docker, React, Agile, etc.
- **Sales**: CRM, Salesforce, Pipeline, B2B, B2C, etc.
- **Marketing**: SEO, SEM, Google Analytics, Content Marketing, etc.
- **Finance**: Accounting, Financial Analysis, Budgeting, GAAP, etc.
- **Admin**: MS Office, Excel, Scheduling, Customer Service, etc.
- **Healthcare**: Patient Care, Medical Records, HIPAA, etc.

## Output Formats

### JSON Format
Structured data for programmatic access:
```json
{
  "ats_score": {
    "total": 75,
    "breakdown": {
      "contact_info": 15,
      "structure": 20,
      ...
    }
  },
  "keywords": {
    "found": {"python": 3, "aws": 2},
    "missing": ["kubernetes", "devops"]
  },
  "recommendations": {
    "critical_issues": [],
    "warnings": [...],
    "suggestions": [...]
  }
}
```

### Human Format
Easy-to-read console output with checkboxes and scores.

### Markdown Format
GitHub-friendly markdown with tables and badges.

### HTML Format
Styled HTML report suitable for web viewing or printing.

## Swedish CV Support

The optimizer handles Swedish CVs with:
- Swedish phone format detection (070-XXX XX XX, +46 7X XXX XX XX)
- Swedish character support (å, ä, ö)
- Swedish power verbs (ledde, utvecklade, förbättrade)
- Swedish-specific suggestions

## Error Handling

The script handles common edge cases:
- **Empty files**: Raises clear error message
- **Large files**: Rejects files >10MB
- **Corrupted PDFs**: Graceful error with helpful message
- **Non-existent files**: FileNotFoundError with path
- **Image-based PDFs**: Detects and reports lack of extractable text

## Testing

Run the test suite:

```bash
python test_resume_optimizer.py
```

Tests cover:
- Empty file handling
- Large file handling
- Non-existent file handling
- Swedish phone format detection
- Email detection
- ATS scoring algorithm
- Report generation (all formats)
- Keyword extraction
- Swedish CV handling
- Full analysis workflow

## Logging

The script logs all activity to `resume_optimizer.log`:
- File reading operations
- Analysis steps
- Errors and warnings
- Performance metrics

Enable verbose mode with `--verbose` for detailed debugging.

## Exit Codes

- **0**: Success (ATS score >= 70)
- **1**: Critical issues (ATS score < 50)
- **2**: Warnings present (ATS score 50-69)
- **3**: File not found
- **4**: File read error
- **5**: Missing dependency
- **99**: Unexpected error

## Production Deployment Tips

1. **Batch Processing**: Use the JSON output format for processing multiple resumes
2. **API Integration**: The JSON format is designed for easy API consumption
3. **Logging**: Monitor `resume_optimizer.log` for operational issues
4. **Customization**: Edit the `KEYWORDS` dictionary to add industry-specific terms
5. **Swedish Market**: Use `--lang sv` for Swedish CVs to get localized suggestions

## Changelog

### v2.0.0
- Production-ready release
- PDF reading support (PyPDF2)
- Comprehensive ATS scoring (0-100)
- Multiple report formats (JSON, Human, Markdown, HTML)
- Swedish CV support
- Before/after comparison
- Comprehensive error handling
- Full test suite

## License

This script is provided as-is for resume optimization services.

## Support

For issues or feature requests, check the logs in `resume_optimizer.log` first.
