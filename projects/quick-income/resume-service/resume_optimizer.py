#!/usr/bin/env python3
"""
AI Resume Optimizer - Production Ready
======================================
A professional CV optimization tool for ATS systems and recruiters.
Supports PDF and text files, with Swedish CV compatibility.

Usage:
    python resume_optimizer.py input.pdf --job "Software Engineer" --output report.json
    python resume_optimizer.py cv.txt --job "Sales Manager" --format human --lang sv

Author: AI Assistant
Version: 2.0.0
"""

import re
import sys
import argparse
import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod

# Optional imports with graceful fallback
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resume_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MD = "md"
    UNKNOWN = "unknown"


class OutputFormat(Enum):
    """Output report formats."""
    JSON = "json"
    HUMAN = "human"
    MARKDOWN = "markdown"
    HTML = "html"


@dataclass
class ATSScoreBreakdown:
    """Detailed ATS scoring breakdown."""
    contact_info: int = 0
    structure: int = 0
    content_quality: int = 0
    keywords: int = 0
    formatting: int = 0
    readability: int = 0
    total: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Complete analysis results."""
    file_path: str
    file_format: str
    file_size_bytes: int
    text_hash: str
    analysis_timestamp: str
    
    # Basic metrics
    word_count: int = 0
    char_count: int = 0
    line_count: int = 0
    
    # Content checks
    has_contact_info: bool = False
    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_summary: bool = False
    has_education: bool = False
    has_experience: bool = False
    has_skills_section: bool = False
    
    # Structure metrics
    section_count: int = 0
    bullet_points: int = 0
    bullet_quality_score: float = 0.0
    
    # Content quality
    power_verbs: int = 0
    power_verb_variety: int = 0
    quantified_achievements: int = 0
    action_oriented_bullets: float = 0.0
    
    # Keywords
    detected_industry: str = "unknown"
    keywords_found: Dict[str, int] = None
    keywords_missing: List[str] = None
    keyword_coverage: float = 0.0
    
    # ATS scoring
    ats_score: int = 0
    score_breakdown: ATSScoreBreakdown = None
    
    # Issues and suggestions
    critical_issues: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    # Language detection
    detected_language: str = "en"
    
    def __post_init__(self):
        if self.keywords_found is None:
            self.keywords_found = {}
        if self.keywords_missing is None:
            self.keywords_missing = []
        if self.critical_issues is None:
            self.critical_issues = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.score_breakdown is None:
            self.score_breakdown = ATSScoreBreakdown()


class FileReader(ABC):
    """Abstract base class for file readers."""
    
    @abstractmethod
    def read(self, file_path: Path) -> str:
        """Read and return text content from file."""
        pass
    
    @abstractmethod
    def supports(self, file_format: FileFormat) -> bool:
        """Check if this reader supports the given format."""
        pass


class TextFileReader(FileReader):
    """Reader for plain text files."""
    
    SUPPORTED_FORMATS = {FileFormat.TXT, FileFormat.MD}
    
    def read(self, file_path: Path) -> str:
        logger.info(f"Reading text file: {file_path}")
        try:
            # Try UTF-8 first (Swedish compatible)
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decoding failed for {file_path}, trying latin-1")
            try:
                return file_path.read_text(encoding='latin-1')
            except Exception as e:
                logger.error(f"Failed to read text file: {e}")
                raise FileReadError(f"Cannot decode file {file_path}: {e}")
    
    def supports(self, file_format: FileFormat) -> bool:
        return file_format in self.SUPPORTED_FORMATS


class PDFFileReader(FileReader):
    """Reader for PDF files using PyPDF2."""
    
    def read(self, file_path: Path) -> str:
        if not PDF_SUPPORT:
            raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")
        
        logger.info(f"Reading PDF file: {file_path}")
        text = ""
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {num_pages} pages")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        else:
                            logger.warning(f"Page {page_num} appears to be an image or has no extractable text")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {e}")
                
                if not text.strip():
                    raise FileReadError("PDF appears to contain no extractable text (may be scanned/image PDF)")
                
        except Exception as e:
            logger.error(f"PDF read error: {e}")
            raise FileReadError(f"Cannot read PDF: {e}")
        
        return text
    
    def supports(self, file_format: FileFormat) -> bool:
        return file_format == FileFormat.PDF


class DOCXFileReader(FileReader):
    """Reader for DOCX files."""
    
    def read(self, file_path: Path) -> str:
        if not DOCX_SUPPORT:
            raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")
        
        logger.info(f"Reading DOCX file: {file_path}")
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"DOCX read error: {e}")
            raise FileReadError(f"Cannot read DOCX: {e}")
    
    def supports(self, file_format: FileFormat) -> bool:
        return file_format == FileFormat.DOCX


class FileReadError(Exception):
    """Custom exception for file reading errors."""
    pass


class FileReaderFactory:
    """Factory for creating appropriate file readers."""
    
    READERS = [TextFileReader(), PDFFileReader(), DOCXFileReader()]
    
    @classmethod
    def get_reader(cls, file_format: FileFormat) -> FileReader:
        """Get a reader for the specified format."""
        for reader in cls.READERS:
            if reader.supports(file_format):
                return reader
        raise FileReadError(f"No reader available for format: {file_format}")


class ResumeOptimizer:
    """Production-ready resume optimization tool."""
    
    VERSION = "2.0.0"
    
    # Power verbs for resumes (expanded)
    POWER_VERBS = [
        'achieved', 'improved', 'trained', 'managed', 'created', 'resolved',
        'volunteered', 'influenced', 'increased', 'decreased', 'launched',
        'generated', 'negotiated', 'streamlined', 'transformed', 'developed',
        'implemented', 'led', 'designed', 'delivered', 'optimized', 'reduced',
        'spearheaded', 'pioneered', 'accelerated', 'boosted', 'enhanced',
        'executed', 'facilitated', 'headed', 'initiated', 'maximized',
        'orchestrated', 'produced', 'revamped', 'secured', 'supervised',
        'engineered', 'architected', 'mentored', 'coordinated', 'directed'
    ]
    
    # Swedish power verbs
    POWER_VERBS_SV = [
        'ledde', 'utvecklade', 'förbättrade', 'hanterade', 'skapade', 'löste',
        'genomförde', 'implementerade', 'optimerade', 'reducerade', 'maximerade',
        'koordinerade', 'organiserade', 'planerade', 'drev', 'ansvarade',
        'levererade', 'uppnådde', 'ökade', 'minskade', 'effektiviserade'
    ]
    
    # ATS keywords by industry (expanded)
    KEYWORDS = {
        'tech': {
            'core': ['python', 'javascript', 'java', 'sql', 'api', 'git', 'aws', 
                     'docker', 'kubernetes', 'react', 'node.js', 'agile', 'scrum'],
            'advanced': ['ci/cd', 'devops', 'microservices', 'cloud', 'rest api', 
                        'machine learning', 'data structures', 'algorithms'],
            'soft': ['collaboration', 'problem solving', 'communication', 'teamwork']
        },
        'sales': {
            'core': ['crm', 'salesforce', 'pipeline', 'quota', 'b2b', 'b2c', 
                     'negotiation', 'closing', 'prospecting', 'cold calling'],
            'advanced': ['account management', 'lead generation', 'sales strategy', 
                        'territory management', 'client retention'],
            'soft': ['relationship building', 'presentation', 'persuasion']
        },
        'marketing': {
            'core': ['seo', 'sem', 'google analytics', 'social media', 'content marketing',
                     'email marketing', 'marketing automation', 'crm'],
            'advanced': ['conversion optimization', 'a/b testing', 'roi analysis',
                        'brand strategy', 'market research', 'ppc'],
            'soft': ['creativity', 'storytelling', 'analytical thinking']
        },
        'finance': {
            'core': ['accounting', 'financial analysis', 'budgeting', 'forecasting',
                     'excel', 'gaap', 'erp', 'financial reporting'],
            'advanced': ['risk management', 'compliance', 'audit', 'investment analysis',
                        'financial modeling', 'sox'],
            'soft': ['attention to detail', 'integrity', 'numerical proficiency']
        },
        'admin': {
            'core': ['ms office', 'excel', 'outlook', 'data entry', 'scheduling',
                     'customer service', 'phone etiquette', 'filing'],
            'advanced': ['project coordination', 'event planning', 'travel arrangements',
                        'expense reporting', 'office management'],
            'soft': ['organization', 'multitasking', 'time management']
        },
        'healthcare': {
            'core': ['patient care', 'medical records', 'hipaa', 'clinical', 'emr',
                     'vital signs', 'treatment plans'],
            'advanced': ['diagnostic', 'care coordination', 'case management',
                        'medication administration'],
            'soft': ['empathy', 'patient advocacy', 'crisis management']
        }
    }
    
    # Swedish keywords
    KEYWORDS_SV = {
        'tech': ['python', 'javascript', 'java', 'sql', 'api', 'git', 'aws', 
                 'docker', 'kubernetes', 'react', 'agil', 'scrum', 'programmering',
                 'utveckling', 'systemutveckling', 'mjukvaruutveckling', 'kodning'],
        'sales': ['försäljning', 'kundrelationer', 'affärsutveckling', 'avtal', 
                  'kundservice', 'nykundsbearbetning', 'sälj', 'budget', 'försäljningsbudget'],
        'marketing': ['marknadsföring', 'digital marknadsföring', 'seo', 'sem', 
                      'sociala medier', 'content', 'kampanjer', 'kommunikation'],
        'finance': ['redovisning', 'ekonomi', 'budgetering', 'prognoser', 
                    'bokslut', 'finansiell analys', 'kassaflöde', 'lönsamhet'],
        'admin': ['kontor', 'administration', 'kundservice', 'dokumentation', 
                  'schema', 'sekreterare', 'koordinering', 'beställningar'],
        'healthcare': ['vård', 'patientvård', 'omvårdnad', 'hälso- och sjukvård',
                       'medicinsk dokumentation', 'behandling', 'diagnos']
    }
    
    # Resume sections - English + Swedish
    SECTION_KEYWORDS = {
        'summary': ['summary', 'professional summary', 'profile', 'about me', 
                    'objective', 'career summary', 'professional profile',
                    # Swedish
                    'sammanfattning', 'profil', 'om mig', 'personlig profil'],
        'experience': ['experience', 'work experience', 'employment history', 
                       'professional experience', 'work history', 'career history',
                       # Swedish
                       'erfarenhet', 'arbetslivserfarenhet', 'arbetserfarenhet', 
                       'yrkeserfarenhet', 'anställningar', 'tidigare anställningar'],
        'education': ['education', 'academic background', 'qualifications', 
                      'educational background', 'academic history',
                      # Swedish
                      'utbildning', 'studier', 'akademisk bakgrund', 
                      'examen', 'universitet', 'högskola', 'gymnasium'],
        'skills': ['skills', 'technical skills', 'core competencies', 
                   'key skills', 'expertise', 'competencies',
                   # Swedish
                   'kompetenser', 'färdigheter', 'kunskaper', 'tekniska kunskaper',
                   'key competencies', 'tekniska kompetenser'],
        'certifications': ['certifications', 'certificates', 'professional development',
                          'licenses', 'accreditations',
                          # Swedish
                          'certifieringar', 'certifikat', 'kurser', 'vidareutbildning']
    }
    
    # Weak words to avoid
    WEAK_WORDS = [
        'responsible for', 'duties included', 'worked on', 'helped with',
        'assisted in', 'participated in', 'involved in', 'familiar with',
        'knowledge of', 'experience with', 'various', 'some', 'many'
    ]
    
    def __init__(self, language: str = "en"):
        self.language = language
        logger.info(f"Initializing ResumeOptimizer v{self.VERSION} (lang: {language})")
    
    def read_file(self, file_path: Path) -> Tuple[str, FileFormat]:
        """Read file and return text content with detected format."""
        logger.info(f"Reading file: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file size (max 10MB)
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            raise ValueError(f"File too large: {file_size} bytes (max 10MB)")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Detect format
        file_format = self._detect_format(file_path)
        logger.info(f"Detected format: {file_format.value}")
        
        # Get appropriate reader
        reader = FileReaderFactory.get_reader(file_format)
        
        # Read content
        text = reader.read(file_path)
        
        if not text or not text.strip():
            raise FileReadError("File contains no readable text")
        
        # Detect language if not specified
        if self.language == "auto":
            self.language = self._detect_language(text)
            logger.info(f"Auto-detected language: {self.language}")
        
        return text, file_format
    
    def _detect_format(self, file_path: Path) -> FileFormat:
        """Detect file format from extension and content."""
        extension = file_path.suffix.lower()
        
        format_map = {
            '.pdf': FileFormat.PDF,
            '.txt': FileFormat.TXT,
            '.md': FileFormat.MD,
            '.docx': FileFormat.DOCX
        }
        
        return format_map.get(extension, FileFormat.UNKNOWN)
    
    def _detect_language(self, text: str) -> str:
        """Detect language from text content."""
        text_lower = text.lower()
        
        # Swedish indicators
        sv_indicators = ['å', 'ä', 'ö', 'cv', 'personligt brev', 'erfarenhet', 
                        'utbildning', 'kompetenser', 'arbetsuppgifter']
        sv_count = sum(1 for ind in sv_indicators if ind in text_lower)
        
        if sv_count >= 2:
            return 'sv'
        
        return 'en'
    
    def analyze_resume(self, text: str, job_title: str = "", 
                       target_industry: str = "") -> AnalysisResult:
        """Perform comprehensive resume analysis."""
        logger.info("Starting resume analysis")
        
        result = AnalysisResult(
            file_path="",
            file_format="text",
            file_size_bytes=len(text.encode('utf-8')),
            text_hash=hashlib.md5(text.encode()).hexdigest(),
            analysis_timestamp=datetime.now().isoformat(),
            detected_language=self.language
        )
        
        # Basic metrics
        result.word_count = len(text.split())
        result.char_count = len(text)
        result.line_count = text.count('\n') + 1
        
        logger.info(f"Text stats: {result.word_count} words, {result.char_count} chars")
        
        # Detect industry
        if target_industry:
            result.detected_industry = target_industry.lower()
        elif job_title:
            result.detected_industry = self._detect_industry(job_title)
        else:
            result.detected_industry = self._detect_industry_from_content(text)
        
        # Content checks
        result.has_email = self._check_email(text)
        result.has_phone = self._check_phone(text)
        result.has_linkedin = self._check_linkedin(text)
        result.has_contact_info = result.has_email and result.has_phone
        result.has_summary = self._check_summary(text)
        result.has_education = self._check_education(text)
        result.has_experience = self._check_experience(text)
        result.has_skills_section = self._check_skills(text)
        
        # Structure
        result.section_count = self._count_sections(text)
        result.bullet_points = self._count_bullets(text)
        result.bullet_quality_score = self._calculate_bullet_quality(text)
        
        # Content quality
        result.power_verbs = self._count_power_verbs(text)
        result.power_verb_variety = self._count_power_verb_variety(text)
        result.quantified_achievements = self._count_quantified_achievements(text)
        result.action_oriented_bullets = self._calculate_action_oriented_ratio(text)
        
        # Keywords
        keyword_data = self._analyze_keywords(text, result.detected_industry)
        result.keywords_found = keyword_data['found']
        result.keywords_missing = keyword_data['missing']
        result.keyword_coverage = keyword_data['coverage']
        
        # ATS Score
        result.ats_score, result.score_breakdown = self._calculate_detailed_ats_score(result, text)
        
        # Generate suggestions
        result.critical_issues = self._generate_critical_issues(result)
        result.warnings = self._generate_warnings(result, text)
        result.suggestions = self._generate_suggestions(result, text)
        
        logger.info(f"Analysis complete. ATS Score: {result.ats_score}")
        
        return result
    
    def _check_email(self, text: str) -> bool:
        """Check for email address."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(pattern, text))
    
    def _check_phone(self, text: str) -> bool:
        """Check for phone number (supports US, Swedish, and international formats)."""
        patterns = [
            # US: (123) 456-7890, 123-456-7890, etc.
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            # Swedish mobile: 07X-XXX XX XX, +46 70 XXX XX XX, 0723-456789, etc.
            r'(\+46|0)\s?7[\d][-\s]?\d{2,3}[-\s]?\d{2,3}[-\s]?\d{2,3}',
            # Swedish landline: 08-XXX XX XX
            r'0\d{1,2}[-\s]?\d{2,3}[-\s]?\d{2}[-\s]?\d{2}',
            # International: +1, +44, etc.
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _check_linkedin(self, text: str) -> bool:
        """Check for LinkedIn URL."""
        pattern = r'linkedin\.com\/in\/[a-zA-Z0-9-]+'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _check_summary(self, text: str) -> bool:
        """Check for professional summary section."""
        text_lower = text.lower()
        keywords = self.SECTION_KEYWORDS['summary']
        
        for keyword in keywords:
            # Look for keyword as section header
            if re.search(rf'\b{re.escape(keyword)}\b[:\s]', text_lower):
                return True
        return False
    
    def _check_education(self, text: str) -> bool:
        """Check for education section."""
        text_lower = text.lower()
        keywords = self.SECTION_KEYWORDS['education']
        
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b[:\s]', text_lower):
                return True
        return False
    
    def _check_experience(self, text: str) -> bool:
        """Check for experience section."""
        text_lower = text.lower()
        keywords = self.SECTION_KEYWORDS['experience']
        
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b[:\s]', text_lower):
                return True
        return False
    
    def _check_skills(self, text: str) -> bool:
        """Check for skills section."""
        text_lower = text.lower()
        keywords = self.SECTION_KEYWORDS['skills']
        
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b[:\s]', text_lower):
                return True
        return False
    
    def _count_sections(self, text: str) -> int:
        """Count resume sections."""
        count = 0
        text_lower = text.lower()
        
        for section_type, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b[:\s]', text_lower):
                    count += 1
                    break
        
        return count
    
    def _count_bullets(self, text: str) -> int:
        """Count bullet points."""
        patterns = [r'[•\*\-\○\▪\►\‣\⁃]', r'^\s*[\-\*•]\s', r'^\s*\d+[.\)]\s']
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.MULTILINE))
        return count
    
    def _calculate_bullet_quality(self, text: str) -> float:
        """Calculate bullet point quality score (0-100)."""
        lines = text.split('\n')
        bullet_lines = []
        
        for line in lines:
            if re.match(r'^\s*[•\*\-\○\▪]', line.strip()):
                bullet_lines.append(line.strip())
        
        if not bullet_lines:
            return 0.0
        
        quality_points = 0
        total_points_possible = len(bullet_lines) * 3
        
        for bullet in bullet_lines:
            # Starts with power verb
            first_word = bullet.split()[1] if len(bullet.split()) > 1 else ""
            if first_word.lower() in [v.lower() for v in self.POWER_VERBS + self.POWER_VERBS_SV]:
                quality_points += 1
            
            # Contains quantifiable metric
            if re.search(r'\d+%|\d+\s*(years?|months?|%|k|million|billion)', bullet, re.IGNORECASE):
                quality_points += 1
            
            # Good length (50-150 characters)
            if 50 <= len(bullet) <= 150:
                quality_points += 1
        
        return (quality_points / total_points_possible * 100) if total_points_possible > 0 else 0.0
    
    def _count_power_verbs(self, text: str) -> int:
        """Count power verb usage."""
        text_lower = text.lower()
        verbs = self.POWER_VERBS if self.language == 'en' else self.POWER_VERBS_SV
        count = 0
        for verb in verbs:
            count += len(re.findall(rf'\b{verb}\b', text_lower))
        return count
    
    def _count_power_verb_variety(self, text: str) -> int:
        """Count unique power verbs used."""
        text_lower = text.lower()
        verbs = self.POWER_VERBS if self.language == 'en' else self.POWER_VERBS_SV
        unique_verbs = set()
        for verb in verbs:
            if re.search(rf'\b{verb}\b', text_lower):
                unique_verbs.add(verb)
        return len(unique_verbs)
    
    def _count_quantified_achievements(self, text: str) -> int:
        """Count achievements with numbers/percentages."""
        patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\s*(million|billion|k)',  # Large numbers
            r'\d+\s*(years?|months?)',  # Time periods
            r'increased\s+by\s+\d+',  # Growth metrics
            r'reduced\s+by\s+\d+',  # Reduction metrics
            r'\d+\s*(team|people|employees)',  # Team sizes
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return count
    
    def _calculate_action_oriented_ratio(self, text: str) -> float:
        """Calculate percentage of action-oriented bullets."""
        lines = text.split('\n')
        bullet_count = 0
        action_count = 0
        verbs = self.POWER_VERBS if self.language == 'en' else self.POWER_VERBS_SV
        
        for line in lines:
            if re.match(r'^\s*[•\*\-\○\▪]', line.strip()):
                bullet_count += 1
                first_words = line.strip().split()[:3]  # Check first 3 words
                for word in first_words:
                    if word.lower() in [v.lower() for v in verbs]:
                        action_count += 1
                        break
        
        return (action_count / bullet_count * 100) if bullet_count > 0 else 0.0
    
    def _detect_industry(self, job_title: str) -> str:
        """Detect industry from job title."""
        job_lower = job_title.lower()
        
        industry_map = {
            'tech': ['software', 'developer', 'engineer', 'programmer', 'it ', 'data ', 
                     'devops', 'frontend', 'backend', 'fullstack', 'web'],
            'sales': ['sales', 'account executive', 'business development', 'sdr', 
                      'account manager', 'territory'],
            'marketing': ['marketing', 'content', 'seo', 'social media', 'brand', 
                          'product marketing', 'growth'],
            'finance': ['accountant', 'finance', 'analyst', 'controller', 'cfo', 
                        'financial', 'audit', 'tax'],
            'admin': ['admin', 'assistant', 'coordinator', 'office', 'secretary', 
                      'receptionist', 'clerk'],
            'healthcare': ['nurse', 'doctor', 'medical', 'clinical', 'patient', 
                           'healthcare', 'therapist']
        }
        
        for industry, keywords in industry_map.items():
            if any(kw in job_lower for kw in keywords):
                return industry
        
        return 'tech'  # Default
    
    def _detect_industry_from_content(self, text: str) -> str:
        """Detect industry from resume content."""
        text_lower = text.lower()
        scores = {}
        
        for industry, keyword_sets in self.KEYWORDS.items():
            score = 0
            all_keywords = []
            if isinstance(keyword_sets, dict):
                all_keywords = keyword_sets.get('core', []) + keyword_sets.get('advanced', [])
            else:
                all_keywords = keyword_sets
            
            for keyword in all_keywords:
                score += len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
            
            scores[industry] = score
        
        return max(scores, key=scores.get) if scores else 'tech'
    
    def _analyze_keywords(self, text: str, industry: str) -> Dict:
        """Analyze keyword usage."""
        text_lower = text.lower()
        result = {'found': {}, 'missing': [], 'coverage': 0.0}
        
        # Get keywords for industry
        keyword_sets = self.KEYWORDS.get(industry, self.KEYWORDS['tech'])
        
        if isinstance(keyword_sets, dict):
            all_keywords = keyword_sets.get('core', []) + keyword_sets.get('advanced', [])
        else:
            all_keywords = keyword_sets
        
        # Check each keyword
        found_count = 0
        for keyword in all_keywords:
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
            if count > 0:
                result['found'][keyword] = count
                found_count += 1
            else:
                result['missing'].append(keyword)
        
        # Calculate coverage
        result['coverage'] = (found_count / len(all_keywords) * 100) if all_keywords else 0.0
        
        return result
    
    def _calculate_detailed_ats_score(self, analysis: AnalysisResult, text: str) -> Tuple[int, ATSScoreBreakdown]:
        """Calculate detailed ATS score with breakdown (0-100)."""
        breakdown = ATSScoreBreakdown()
        
        # 1. Contact Info (15 points)
        if analysis.has_contact_info:
            breakdown.contact_info = 15
        elif analysis.has_email or analysis.has_phone:
            breakdown.contact_info = 8
        
        # 2. Structure (20 points)
        # - Has summary (5)
        if analysis.has_summary:
            breakdown.structure += 5
        
        # - Has education (5)
        if analysis.has_education:
            breakdown.structure += 5
        
        # - Has experience (5)
        if analysis.has_experience:
            breakdown.structure += 5
        
        # - Has skills section (5)
        if analysis.has_skills_section:
            breakdown.structure += 5
        
        # 3. Content Quality (20 points)
        # - Power verbs variety (10)
        if analysis.power_verb_variety >= 8:
            breakdown.content_quality += 10
        elif analysis.power_verb_variety >= 5:
            breakdown.content_quality += 7
        elif analysis.power_verb_variety >= 3:
            breakdown.content_quality += 4
        
        # - Quantified achievements (10)
        if analysis.quantified_achievements >= 5:
            breakdown.content_quality += 10
        elif analysis.quantified_achievements >= 3:
            breakdown.content_quality += 6
        elif analysis.quantified_achievements >= 1:
            breakdown.content_quality += 3
        
        # 4. Keywords (20 points)
        if analysis.keyword_coverage >= 50:
            breakdown.keywords = 20
        elif analysis.keyword_coverage >= 30:
            breakdown.keywords = 15
        elif analysis.keyword_coverage >= 15:
            breakdown.keywords = 10
        elif analysis.keyword_coverage > 0:
            breakdown.keywords = 5
        
        # 5. Formatting (10 points)
        # - Bullet point usage
        if 10 <= analysis.bullet_points <= 25:
            breakdown.formatting += 5
        elif analysis.bullet_points > 0:
            breakdown.formatting += 3
        
        # - Bullet quality
        if analysis.bullet_quality_score >= 70:
            breakdown.formatting += 5
        elif analysis.bullet_quality_score >= 40:
            breakdown.formatting += 3
        
        # 6. Readability (15 points)
        # - Word count (optimal: 300-600)
        if 300 <= analysis.word_count <= 600:
            breakdown.readability = 15
        elif 200 <= analysis.word_count < 300:
            breakdown.readability = 10
        elif 600 < analysis.word_count <= 800:
            breakdown.readability = 10
        elif 100 <= analysis.word_count < 200:
            breakdown.readability = 5
        elif analysis.word_count > 800:
            breakdown.readability = 5
        
        # Calculate total
        breakdown.total = min(
            breakdown.contact_info + 
            breakdown.structure + 
            breakdown.content_quality + 
            breakdown.keywords + 
            breakdown.formatting + 
            breakdown.readability,
            100
        )
        
        return breakdown.total, breakdown
    
    def _generate_critical_issues(self, analysis: AnalysisResult) -> List[str]:
        """Generate critical issues that must be fixed."""
        issues = []
        
        if not analysis.has_contact_info:
            if not analysis.has_email:
                issues.append("[CRITICAL] No email address found. ATS systems require contact information.")
            if not analysis.has_phone:
                issues.append("[CRITICAL] No phone number found. Add your phone number for recruiter contact.")
        
        if not analysis.has_summary:
            issues.append("[CRITICAL] No professional summary section. This is the first thing recruiters see.")
        
        if not analysis.has_experience:
            issues.append("[CRITICAL] No experience section detected. Add your work history.")
        
        if analysis.word_count < 100:
            issues.append("[CRITICAL] Resume is too short (<100 words). Expand with relevant details.")
        
        return issues
    
    def _generate_warnings(self, analysis: AnalysisResult, text: str) -> List[str]:
        """Generate warnings for suboptimal elements."""
        warnings = []
        
        if not analysis.has_linkedin:
            warnings.append("[WARN] No LinkedIn URL found. Adding it increases recruiter engagement.")
        
        if not analysis.has_education:
            warnings.append("[WARN] No education section detected. Consider adding if applicable.")
        
        if not analysis.has_skills_section:
            warnings.append("[WARN] No skills section found. Add a dedicated skills section for better ATS matching.")
        
        if analysis.bullet_points < 5:
            warnings.append("[WARN] Very few bullet points. Use bullets for better readability.")
        elif analysis.bullet_points > 30:
            warnings.append("[WARN] Too many bullet points. Focus on 10-15 strongest achievements.")
        
        if analysis.power_verbs < 3:
            warnings.append("[WARN] Few action verbs detected. Start bullets with strong action verbs.")
        
        if analysis.quantified_achievements < 2:
            warnings.append("[WARN] Limited quantified achievements. Add numbers/percentages to demonstrate impact.")
        
        if analysis.word_count > 700:
            warnings.append("[WARN] Resume is long (>700 words). Consider condensing to 1 page if early career.")
        
        # Check for weak words
        text_lower = text.lower()
        weak_found = [w for w in self.WEAK_WORDS if w in text_lower]
        if weak_found:
            warnings.append(f"[WARN] Weak phrases detected: {', '.join(weak_found[:3])}. Replace with stronger language.")
        
        return warnings
    
    def _generate_suggestions(self, analysis: AnalysisResult, text: str) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if analysis.keyword_coverage < 30:
            suggestions.append(f"[TIP] Add more industry keywords. Missing: {', '.join(analysis.keywords_missing[:5])}")
        
        if analysis.power_verb_variety < 5:
            verb_suggestions = [v for v in self.POWER_VERBS[:8] if v not in text.lower()]
            if verb_suggestions:
                suggestions.append(f"[TIP] Vary your action verbs. Try: {', '.join(verb_suggestions[:4])}")
        
        if analysis.bullet_quality_score < 50:
            suggestions.append("[TIP] Improve bullet quality: Start with action verbs, include metrics, keep 50-150 chars.")
        
        if analysis.action_oriented_bullets < 60:
            suggestions.append("[TIP] More bullets should start with action verbs. Revise passive statements.")
        
        # Length suggestions
        if analysis.word_count < 250:
            suggestions.append("[TIP] Expand your resume with more specific achievements and responsibilities.")
        
        # Section suggestions
        if analysis.section_count < 3:
            suggestions.append("[TIP] Consider adding more sections: Skills, Certifications, Projects, or Awards.")
        
        # Swedish-specific
        if self.language == 'sv':
            suggestions.append("[TIP] For Swedish CVs: Consider adding a personal letter (personligt brev) as a complement.")
        
        return suggestions
    
    def generate_before_after_comparison(self, original_text: str, 
                                         analysis: AnalysisResult) -> Dict:
        """Generate before/after comparison showing improvements."""
        comparison = {
            'original_stats': {
                'word_count': analysis.word_count,
                'ats_score': analysis.ats_score,
                'bullet_points': analysis.bullet_points,
                'keywords_found': len(analysis.keywords_found)
            },
            'target_stats': {
                'word_count': max(300, min(600, analysis.word_count)),
                'ats_score': min(100, analysis.ats_score + 20),
                'bullet_points': max(10, min(20, analysis.bullet_points)),
                'keywords_found': min(10, len(analysis.keywords_found) + 5)
            },
            'improvement_areas': [],
            'sample_improvements': self._generate_sample_improvements(original_text, analysis)
        }
        
        # Calculate improvement areas
        if analysis.ats_score < 70:
            comparison['improvement_areas'].append(f"ATS Score: {analysis.ats_score} -> Target: 70+")
        if analysis.bullet_points < 10:
            comparison['improvement_areas'].append(f"Bullets: {analysis.bullet_points} -> Target: 10-15")
        if len(analysis.keywords_found) < 5:
            comparison['improvement_areas'].append(f"Keywords: {len(analysis.keywords_found)} -> Target: 5+")
        
        return comparison
    
    def _generate_sample_improvements(self, text: str, analysis: AnalysisResult) -> List[Dict]:
        """Generate sample before/after improvements."""
        samples = []
        
        # Find weak phrases to improve
        for weak_phrase in self.WEAK_WORDS[:3]:
            if weak_phrase in text.lower():
                # Find the sentence containing this phrase
                sentences = re.split(r'[.!?]+', text)
                for sent in sentences:
                    if weak_phrase in sent.lower() and len(sent.strip()) > 20:
                        samples.append({
                            'before': sent.strip(),
                            'after': self._improve_sentence(sent.strip()),
                            'reason': f"Replaced weak phrase '{weak_phrase}' with strong action verb"
                        })
                        break
                if len(samples) >= 2:
                    break
        
        return samples
    
    def _improve_sentence(self, sentence: str) -> str:
        """Improve a sentence with weak language."""
        sentence = sentence.strip()
        
        # Replace weak phrases with strong alternatives
        improvements = {
            'responsible for': 'Led',
            'duties included': 'Managed',
            'worked on': 'Developed',
            'helped with': 'Contributed to',
            'assisted in': 'Supported',
            'participated in': 'Collaborated on'
        }
        
        for weak, strong in improvements.items():
            if weak in sentence.lower():
                # Capitalize and replace
                pattern = re.compile(re.escape(weak), re.IGNORECASE)
                return pattern.sub(strong, sentence)
        
        # If no weak phrase found, just suggest starting with a power verb
        return f"[Start with action verb] {sentence}"


class ReportGenerator:
    """Generate reports in various formats."""
    
    def __init__(self, language: str = "en"):
        self.language = language
    
    def generate(self, analysis: AnalysisResult, format_type: OutputFormat) -> str:
        """Generate report in specified format."""
        if format_type == OutputFormat.JSON:
            return self._generate_json(analysis)
        elif format_type == OutputFormat.HUMAN:
            return self._generate_human(analysis)
        elif format_type == OutputFormat.MARKDOWN:
            return self._generate_markdown(analysis)
        elif format_type == OutputFormat.HTML:
            return self._generate_html(analysis)
        else:
            raise ValueError(f"Unknown format: {format_type}")
    
    def _generate_json(self, analysis: AnalysisResult) -> str:
        """Generate JSON report."""
        data = {
            'metadata': {
                'version': ResumeOptimizer.VERSION,
                'timestamp': analysis.analysis_timestamp,
                'file': {
                    'path': analysis.file_path,
                    'format': analysis.file_format,
                    'size_bytes': analysis.file_size_bytes,
                    'text_hash': analysis.text_hash
                }
            },
            'language': {
                'detected': analysis.detected_language
            },
            'metrics': {
                'word_count': analysis.word_count,
                'char_count': analysis.char_count,
                'line_count': analysis.line_count,
                'bullet_points': analysis.bullet_points,
                'sections': analysis.section_count
            },
            'content_analysis': {
                'has_contact_info': analysis.has_contact_info,
                'has_email': analysis.has_email,
                'has_phone': analysis.has_phone,
                'has_linkedin': analysis.has_linkedin,
                'has_summary': analysis.has_summary,
                'has_education': analysis.has_education,
                'has_experience': analysis.has_experience,
                'has_skills_section': analysis.has_skills_section
            },
            'quality_metrics': {
                'power_verbs': analysis.power_verbs,
                'power_verb_variety': analysis.power_verb_variety,
                'quantified_achievements': analysis.quantified_achievements,
                'bullet_quality_score': round(analysis.bullet_quality_score, 1),
                'action_oriented_bullets': round(analysis.action_oriented_bullets, 1)
            },
            'keywords': {
                'detected_industry': analysis.detected_industry,
                'found': analysis.keywords_found,
                'missing': analysis.keywords_missing,
                'coverage_percent': round(analysis.keyword_coverage, 1)
            },
            'ats_score': {
                'total': analysis.ats_score,
                'breakdown': analysis.score_breakdown.to_dict()
            },
            'recommendations': {
                'critical_issues': analysis.critical_issues,
                'warnings': analysis.warnings,
                'suggestions': analysis.suggestions
            }
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _generate_human(self, analysis: AnalysisResult) -> str:
        """Generate human-readable report."""
        score_status = "PASS" if analysis.ats_score >= 70 else "NEEDS WORK" if analysis.ats_score >= 50 else "CRITICAL"
        
        report = f"""
{'='*60}
   RESUME OPTIMIZATION REPORT v{ResumeOptimizer.VERSION}
{'='*60}

FILE INFORMATION
   Path: {analysis.file_path}
   Format: {analysis.file_format}
   Size: {analysis.file_size_bytes:,} bytes
   Analyzed: {analysis.analysis_timestamp}

LANGUAGE
   Detected: {'Swedish' if analysis.detected_language == 'sv' else 'English'}

ATS COMPATIBILITY SCORE: {analysis.ats_score}/100 [{score_status}]
   
   Score Breakdown:
   - Contact Information: {analysis.score_breakdown.contact_info}/15
   - Resume Structure:    {analysis.score_breakdown.structure}/20
   - Content Quality:     {analysis.score_breakdown.content_quality}/20
   - Keyword Matching:    {analysis.score_breakdown.keywords}/20
   - Formatting:          {analysis.score_breakdown.formatting}/10
   - Readability:         {analysis.score_breakdown.readability}/15

BASIC METRICS
   Word Count:   {analysis.word_count}
   Characters:   {analysis.char_count:,}
   Lines:        {analysis.line_count}
   Sections:     {analysis.section_count}
   Bullets:      {analysis.bullet_points}

CONTENT CHECKLIST
   [{'X' if analysis.has_contact_info else ' '}] Contact Information (Email + Phone)
   [{'X' if analysis.has_email else ' '}] Email Address
   [{'X' if analysis.has_phone else ' '}] Phone Number
   [{'X' if analysis.has_linkedin else ' '}] LinkedIn URL
   [{'X' if analysis.has_summary else ' '}] Professional Summary
   [{'X' if analysis.has_experience else ' '}] Experience Section
   [{'X' if analysis.has_education else ' '}] Education Section
   [{'X' if analysis.has_skills_section else ' '}] Skills Section

QUALITY METRICS
   Power Verbs Used:        {analysis.power_verbs}
   Power Verb Variety:      {analysis.power_verb_variety} unique
   Quantified Achievements: {analysis.quantified_achievements}
   Bullet Quality Score:    {analysis.bullet_quality_score:.1f}%
   Action-Oriented Bullets: {analysis.action_oriented_bullets:.1f}%

INDUSTRY KEYWORDS
   Detected Industry: {analysis.detected_industry.upper()}
   Coverage: {analysis.keyword_coverage:.1f}%
   
   Keywords Found ({len(analysis.keywords_found)}):
"""
        
        for keyword, count in sorted(analysis.keywords_found.items(), key=lambda x: -x[1]):
            report += f"   - {keyword}: {count}x\n"
        
        if analysis.keywords_missing:
            report += f"\n   Missing Keywords (top 5): {', '.join(analysis.keywords_missing[:5])}\n"
        
        # Critical Issues
        if analysis.critical_issues:
            report += f"""
CRITICAL ISSUES (Must Fix)
"""
            for issue in analysis.critical_issues:
                report += f"   [CRITICAL] {issue}\n"
        
        # Warnings
        if analysis.warnings:
            report += f"""
WARNINGS
"""
            for warning in analysis.warnings:
                report += f"   [WARN] {warning}\n"
        
        # Suggestions
        if analysis.suggestions:
            report += f"""
IMPROVEMENT SUGGESTIONS
"""
            for suggestion in analysis.suggestions:
                report += f"   [TIP] {suggestion}\n"
        
        report += f"""
{'='*60}
   END OF REPORT
{'='*60}
"""
        
        return report
    
    def _generate_markdown(self, analysis: AnalysisResult) -> str:
        """Generate Markdown report."""
        score_badge = "![Passing](https://img.shields.io/badge/ATS-{score}-green)" if analysis.ats_score >= 70 else \
                      "![Needs Work](https://img.shields.io/badge/ATS-{score}-yellow)" if analysis.ats_score >= 50 else \
                      "![Critical](https://img.shields.io/badge/ATS-{score}-red)"
        
        report = f"""# Resume Analysis Report

## Overview

{score_badge.format(score=analysis.ats_score)}

| Metric | Value |
|--------|-------|
| ATS Score | {analysis.ats_score}/100 |
| Word Count | {analysis.word_count} |
| Industry | {analysis.detected_industry.title()} |
| Language | {'Swedish' if analysis.detected_language == 'sv' else 'English'} |

## Score Breakdown

| Category | Score | Max |
|----------|-------|-----|
| Contact Information | {analysis.score_breakdown.contact_info} | 15 |
| Structure | {analysis.score_breakdown.structure} | 20 |
| Content Quality | {analysis.score_breakdown.content_quality} | 20 |
| Keywords | {analysis.score_breakdown.keywords} | 20 |
| Formatting | {analysis.score_breakdown.formatting} | 10 |
| Readability | {analysis.score_breakdown.readability} | 15 |
| **Total** | **{analysis.ats_score}** | **100** |

## Keywords Found ({len(analysis.keywords_found)})

"""
        for keyword, count in sorted(analysis.keywords_found.items(), key=lambda x: -x[1]):
            report += f"- **{keyword}**: {count}x\n"
        
        if analysis.critical_issues:
            report += "\n## Critical Issues\n\n"
            for issue in analysis.critical_issues:
                report += f"- 🔴 {issue}\n"
        
        if analysis.warnings:
            report += "\n## Warnings\n\n"
            for warning in analysis.warnings:
                report += f"- ⚠️ {warning}\n"
        
        if analysis.suggestions:
            report += "\n## Suggestions\n\n"
            for suggestion in analysis.suggestions:
                report += f"- 💡 {suggestion}\n"
        
        return report
    
    def _generate_html(self, analysis: AnalysisResult) -> str:
        """Generate HTML report."""
        score_color = "#4CAF50" if analysis.ats_score >= 70 else "#FF9800" if analysis.ats_score >= 50 else "#F44336"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; margin: 20px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .score-value {{ font-size: 36px; font-weight: bold; color: {score_color}; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .keyword {{ display: inline-block; background: #e3f2fd; color: #1976d2; padding: 4px 12px; border-radius: 15px; margin: 4px; font-size: 14px; }}
        .critical {{ background: #ffebee; color: #c62828; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .warning {{ background: #fff3e0; color: #ef6c00; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .suggestion {{ background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Resume Analysis Report</h1>
        <p>Generated: {analysis.analysis_timestamp}</p>
    </div>
    
    <div class="card">
        <div class="score-circle">
            <span class="score-value">{analysis.ats_score}</span>
        </div>
        <p style="text-align: center; font-size: 18px;">ATS Compatibility Score</p>
    </div>
    
    <div class="card">
        <h2>📊 Key Metrics</h2>
        <div class="metric">
            <div class="metric-value">{analysis.word_count}</div>
            <div class="metric-label">Words</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis.bullet_points}</div>
            <div class="metric-label">Bullets</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis.detected_industry.title()}</div>
            <div class="metric-label">Industry</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(analysis.keywords_found)}</div>
            <div class="metric-label">Keywords</div>
        </div>
    </div>
    
    <div class="card">
        <h2>📈 Score Breakdown</h2>
        <table>
            <tr><th>Category</th><th>Score</th><th>Max</th></tr>
            <tr><td>Contact Information</td><td>{analysis.score_breakdown.contact_info}</td><td>15</td></tr>
            <tr><td>Structure</td><td>{analysis.score_breakdown.structure}</td><td>20</td></tr>
            <tr><td>Content Quality</td><td>{analysis.score_breakdown.content_quality}</td><td>20</td></tr>
            <tr><td>Keywords</td><td>{analysis.score_breakdown.keywords}</td><td>20</td></tr>
            <tr><td>Formatting</td><td>{analysis.score_breakdown.formatting}</td><td>10</td></tr>
            <tr><td>Readability</td><td>{analysis.score_breakdown.readability}</td><td>15</td></tr>
        </table>
    </div>
"""
        
        if analysis.keywords_found:
            html += '<div class="card"><h2>🏷️ Keywords Found</h2>'
            for keyword in analysis.keywords_found:
                html += f'<span class="keyword">{keyword}</span>'
            html += '</div>'
        
        if analysis.critical_issues:
            html += '<div class="card"><h2>❌ Critical Issues</h2>'
            for issue in analysis.critical_issues:
                html += f'<div class="critical">{issue}</div>'
            html += '</div>'
        
        if analysis.warnings:
            html += '<div class="card"><h2>⚠️ Warnings</h2>'
            for warning in analysis.warnings:
                html += f'<div class="warning">{warning}</div>'
            html += '</div>'
        
        if analysis.suggestions:
            html += '<div class="card"><h2>💡 Suggestions</h2>'
            for suggestion in analysis.suggestions:
                html += f'<div class="suggestion">{suggestion}</div>'
            html += '</div>'
        
        html += """
</body>
</html>
"""
        
        return html


def create_sample_resume() -> str:
    """Create a sample resume for testing."""
    return """
John Andersson
Stockholm, Sverige
john.andersson@email.se | +46 70 123 45 67 | linkedin.com/in/johnandersson

PROFESSIONAL SUMMARY
Experienced software developer with 5+ years in full-stack development. 
Passionate about creating scalable solutions and mentoring junior developers.

WORK EXPERIENCE

Senior Developer | Tech Solutions AB | 2020 - Present
• Led a team of 5 developers in agile sprints
• Improved application performance by 40% through optimization
• Implemented CI/CD pipeline reducing deployment time by 50%
• Responsible for code reviews and mentoring junior developers

Developer | Digital Innovations | 2018 - 2020
• Worked on various web applications using React and Node.js
• Duties included frontend development and API integration
• Helped with bug fixes and feature implementations

EDUCATION
Master of Science in Computer Engineering
KTH Royal Institute of Technology, 2018

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, Git, Agile

CERTIFICATIONS
• AWS Certified Solutions Architect
• Scrum Master Certification
"""


def main():
    parser = argparse.ArgumentParser(
        description='AI Resume Optimizer - Production Ready CV Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a PDF resume
  python resume_optimizer.py resume.pdf --job "Software Engineer"
  
  # Generate HTML report
  python resume_optimizer.py cv.docx --format html --output report.html
  
  # Swedish CV analysis
  python resume_optimizer.py mitt-cv.pdf --job "Systemutvecklare" --lang sv
  
  # Create sample resume for testing
  python resume_optimizer.py --create-sample --output sample_resume.txt
        """
    )
    
    parser.add_argument('file', nargs='?', help='Resume file (PDF, TXT, DOCX, or MD)')
    parser.add_argument('--job', '-j', help='Target job title', default='')
    parser.add_argument('--industry', '-i', help='Target industry (overrides auto-detect)', default='')
    parser.add_argument('--output', '-o', help='Output file path', default='')
    parser.add_argument('--format', '-f', 
                        choices=['json', 'human', 'markdown', 'html'],
                        default='human',
                        help='Output format (default: human)')
    parser.add_argument('--lang', '-l', 
                        choices=['en', 'sv', 'auto'],
                        default='auto',
                        help='Language (en=English, sv=Swedish, auto=detect)')
    parser.add_argument('--create-sample', action='store_true',
                        help='Create a sample resume for testing')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--version', action='version', version=f'%(prog)s {ResumeOptimizer.VERSION}')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle sample creation
    if args.create_sample:
        sample = create_sample_resume()
        output_path = args.output or 'sample_resume.txt'
        Path(output_path).write_text(sample, encoding='utf-8')
        print(f"[OK] Sample resume created: {output_path}")
        return
    
    # Validate file argument
    if not args.file:
        parser.error("File path is required (unless using --create-sample)")
    
    file_path = Path(args.file)
    
    try:
        # Initialize optimizer
        optimizer = ResumeOptimizer(language=args.lang)
        
        # Read file
        text, file_format = optimizer.read_file(file_path)
        
        # Perform analysis
        analysis = optimizer.analyze_resume(text, args.job, args.industry)
        analysis.file_path = str(file_path)
        analysis.file_format = file_format.value
        
        # Generate before/after comparison
        comparison = optimizer.generate_before_after_comparison(text, analysis)
        
        # Generate report
        format_map = {
            'json': OutputFormat.JSON,
            'human': OutputFormat.HUMAN,
            'markdown': OutputFormat.MARKDOWN,
            'html': OutputFormat.HTML
        }
        output_format = format_map[args.format]
        
        report_generator = ReportGenerator(language=analysis.detected_language)
        report = report_generator.generate(analysis, output_format)
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(report, encoding='utf-8')
            print(f"[OK] Report saved to: {output_path}")
            
            # Also save JSON for programmatic access
            if output_format != OutputFormat.JSON:
                json_report = report_generator.generate(analysis, OutputFormat.JSON)
                json_path = output_path.with_suffix('.json')
                json_path.write_text(json_report, encoding='utf-8')
                print(f"[OK] JSON data saved to: {json_path}")
        else:
            print(report)
        
        # Print before/after comparison summary
        print("\n" + "="*60)
        print("BEFORE/AFTER COMPARISON")
        print("="*60)
        print(f"Current ATS Score: {comparison['original_stats']['ats_score']}")
        print(f"Target ATS Score:  {comparison['target_stats']['ats_score']}")
        print(f"\nImprovement Areas:")
        for area in comparison['improvement_areas']:
            print(f"  - {area}")
        
        if comparison['sample_improvements']:
            print(f"\nSample Improvements:")
            for sample in comparison['sample_improvements'][:2]:
                print(f"\n  BEFORE: {sample['before']}")
                print(f"  AFTER:   {sample['after']}")
                print(f"  REASON: {sample['reason']}")
        
        # Return exit code based on score
        if analysis.ats_score < 50:
            sys.exit(1)  # Critical issues
        elif analysis.ats_score < 70:
            sys.exit(2)  # Warnings
        else:
            sys.exit(0)  # Good
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(3)
    except FileReadError as e:
        logger.error(f"File read error: {e}")
        print(f"[ERROR] Reading file: {e}", file=sys.stderr)
        sys.exit(4)
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"[ERROR] Missing dependency: {e}", file=sys.stderr)
        print("Install with: pip install PyPDF2 python-docx", file=sys.stderr)
        sys.exit(5)
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(99)


if __name__ == '__main__':
    main()
