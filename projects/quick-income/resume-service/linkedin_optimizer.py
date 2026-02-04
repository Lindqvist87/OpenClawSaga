#!/usr/bin/env python3
"""
LinkedIn Profile Optimizer - Production Ready
Analyzes and optimizes LinkedIn profiles for better visibility and engagement.

Usage:
    python linkedin_optimizer.py profile.txt --format human
    python linkedin_optimizer.py profile.txt --format json --output report.json
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats."""
    TXT = "txt"
    MD = "md"


@dataclass
class LinkedInScoreBreakdown:
    """Breakdown of LinkedIn profile score."""
    headline: int = 0  # 15 points
    about: int = 0     # 20 points
    experience: int = 0 # 20 points
    skills: int = 0    # 15 points
    engagement: int = 0 # 15 points
    completeness: int = 0 # 15 points
    
    def total(self) -> int:
        return (self.headline + self.about + self.experience + 
                self.skills + self.engagement + self.completeness)
    
    def to_dict(self) -> Dict:
        return {
            'headline': self.headline,
            'about': self.about,
            'experience': self.experience,
            'skills': self.skills,
            'engagement': self.engagement,
            'completeness': self.completeness,
            'total': self.total()
        }


@dataclass
class LinkedInAnalysisResult:
    """Result of LinkedIn profile analysis."""
    # Basic info
    file_path: str = ""
    file_format: str = ""
    file_size_bytes: int = 0
    analysis_timestamp: str = ""
    text_hash: str = ""
    
    # Language
    detected_language: str = "sv"
    
    # Profile Components
    has_headline: bool = False
    has_about: bool = False
    has_experience: bool = False
    has_education: bool = False
    has_skills: bool = False
    has_photo: bool = False  # Mentioned in text
    has_banner: bool = False  # Mentioned in text
    has_contact_info: bool = False
    has_custom_url: bool = False
    
    # Content Quality
    headline_length: int = 0
    about_length: int = 0
    about_word_count: int = 0
    experience_entries: int = 0
    skills_count: int = 0
    
    # Keywords
    keywords_found: Dict[str, int] = None
    keywords_missing: List[str] = None
    keyword_coverage: float = 0.0
    
    # Scores
    profile_score: int = 0
    score_breakdown: LinkedInScoreBreakdown = None
    
    # Recommendations
    critical_issues: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
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
            self.score_breakdown = LinkedInScoreBreakdown()


class LinkedInOptimizer:
    """LinkedIn profile optimization tool."""
    
    VERSION = "1.0.0"
    
    # LinkedIn best practices
    HEADLINE_MAX = 220
    HEADLINE_OPTIMAL = 120
    ABOUT_MAX = 2600
    ABOUT_OPTIMAL_MIN = 300
    ABOUT_OPTIMAL_MAX = 1500
    
    # Keywords for different industries
    KEYWORDS = {
        'tech': ['software', 'developer', 'engineer', 'programming', 'python', 'javascript', 
                'agile', 'scrum', 'cloud', 'aws', 'azure', 'devops', 'full-stack', 'backend', 'frontend'],
        'marketing': ['marketing', 'digital', 'seo', 'sem', 'social media', 'content', 
                     'brand', 'campaign', 'analytics', 'growth', 'strategy', 'communications'],
        'sales': ['sales', 'business development', 'account management', 'b2b', 'b2c', 
                 'revenue', 'quota', 'pipeline', 'closing', 'negotiation'],
        'finance': ['finance', 'accounting', 'financial analysis', 'budget', 'forecasting', 
                   'investment', 'risk', 'compliance', 'audit', 'reporting'],
        'hr': ['hr', 'human resources', 'recruiting', 'talent acquisition', 'onboarding', 
              'employee relations', 'performance management', 'culture'],
        'healthcare': ['healthcare', 'patient care', 'clinical', 'medical', 'nursing', 
                      'treatment', 'diagnosis', 'care coordination'],
        'consulting': ['consulting', 'strategy', 'transformation', 'analysis', 'problem solving',
                      'project management', 'stakeholder management']
    }
    
    # Power words for headlines
    POWER_WORDS = [
        'expert', 'specialist', 'leader', 'strategist', 'innovator', 'driven',
        'passionate', 'experienced', 'certified', 'award-winning', 'results-oriented',
        'creative', 'analytical', 'collaborative', 'dynamic'
    ]
    
    def __init__(self, language: str = "sv"):
        self.language = language
        logger.info(f"Initializing LinkedInOptimizer v{self.VERSION} (lang: {language})")
    
    def read_file(self, file_path: Path) -> Tuple[str, FileFormat]:
        """Read LinkedIn profile text file."""
        logger.info(f"Reading file: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            raise ValueError(f"File too large: {file_size} bytes (max 10MB)")
        
        # Detect format
        suffix = file_path.suffix.lower()
        if suffix == '.md':
            file_format = FileFormat.MD
        else:
            file_format = FileFormat.TXT
        
        # Read content
        text = file_path.read_text(encoding='utf-8')
        
        if not text.strip():
            raise ValueError("File is empty")
        
        logger.info(f"Detected format: {file_format.value}")
        return text, file_format
    
    def analyze_profile(self, text: str, industry: str = "") -> LinkedInAnalysisResult:
        """Analyze LinkedIn profile text."""
        import hashlib
        from datetime import datetime
        
        result = LinkedInAnalysisResult()
        result.analysis_timestamp = datetime.now().isoformat()
        result.text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        
        # Detect language
        result.detected_language = self._detect_language(text)
        
        # Analyze profile components
        result.has_headline = self._check_headline(text)
        result.has_about = self._check_about(text)
        result.has_experience = self._check_experience(text)
        result.has_education = self._check_education(text)
        result.has_skills = self._check_skills(text)
        result.has_contact_info = self._check_contact_info(text)
        result.has_custom_url = self._check_custom_url(text)
        
        # Content metrics
        result.headline_length = self._get_headline_length(text)
        result.about_length = len(self._get_about_text(text))
        result.about_word_count = len(self._get_about_text(text).split())
        result.experience_entries = self._count_experience_entries(text)
        result.skills_count = self._count_skills(text)
        
        # Industry detection
        if not industry:
            industry = self._detect_industry(text)
        
        # Keyword analysis
        keyword_analysis = self._analyze_keywords(text, industry)
        result.keywords_found = keyword_analysis['found']
        result.keywords_missing = keyword_analysis['missing']
        result.keyword_coverage = keyword_analysis['coverage']
        
        # Calculate scores
        result.score_breakdown = self._calculate_score(result)
        result.profile_score = result.score_breakdown.total()
        
        # Generate recommendations
        result.critical_issues = self._generate_critical_issues(result, text)
        result.warnings = self._generate_warnings(result, text)
        result.suggestions = self._generate_suggestions(result, text)
        
        logger.info(f"Analysis complete. Profile Score: {result.profile_score}")
        return result
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is Swedish or English."""
        swedish_indicators = ['och', 'att', 'det', 'som', 'på', 'den', 'med', 'är', 
                             'års', 'erfarenhet', 'arbete', 'utbildning', 'kompetens']
        text_lower = text.lower()
        swedish_count = sum(1 for word in swedish_indicators if word in text_lower)
        return 'sv' if swedish_count >= 3 else 'en'
    
    def _check_headline(self, text: str) -> bool:
        """Check if profile has a headline."""
        lines = text.strip().split('\n')
        # Headline is usually the second line (after name)
        if len(lines) >= 2:
            headline = lines[1].strip()
            return len(headline) > 5 and not headline.startswith('http')
        return False
    
    def _get_headline_length(self, text: str) -> int:
        """Get headline character length."""
        lines = text.strip().split('\n')
        if len(lines) >= 2:
            return len(lines[1].strip())
        return 0
    
    def _check_about(self, text: str) -> bool:
        """Check if profile has About section."""
        patterns = ['om mig', 'about', 'sammanfattning', 'summary', 'bakgrund', 'background']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _get_about_text(self, text: str) -> str:
        """Extract About section text."""
        lines = text.split('\n')
        about_start = -1
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(x in line_lower for x in ['om mig', 'about', 'sammanfattning', 'summary']):
                about_start = i + 1
                break
        
        if about_start > 0:
            # Collect text until next section
            about_lines = []
            for line in lines[about_start:]:
                if line.strip().upper() in ['ERFARENHET', 'EXPERIENCE', 'UTBILDNING', 'EDUCATION']:
                    break
                about_lines.append(line)
            return ' '.join(about_lines)
        
        return ""
    
    def _check_experience(self, text: str) -> bool:
        """Check if profile has Experience section."""
        patterns = ['erfarenhet', 'experience', 'arbete', 'work', 'anställning', 'employment']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _count_experience_entries(self, text: str) -> int:
        """Count number of experience entries."""
        # Look for date patterns like "2020 - 2023" or "Jan 2020 - Present"
        date_patterns = [
            r'\d{4}\s*[-–]\s*(\d{4}|nu|present|current)',
            r'(jan|feb|mar|apr|maj|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}',
        ]
        count = 0
        for pattern in date_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return min(count, 10)  # Cap at 10
    
    def _check_education(self, text: str) -> bool:
        """Check if profile has Education section."""
        patterns = ['utbildning', 'education', 'studier', 'studies', 'universitet', 'university']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _check_skills(self, text: str) -> bool:
        """Check if profile has Skills section."""
        patterns = ['kompetenser', 'skills', 'färdigheter', 'expertis', 'expertise']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _count_skills(self, text: str) -> int:
        """Count number of skills listed."""
        # Look for bullet points or comma-separated skills
        skill_patterns = [r'•', r'·', r'-', r'\n\n']
        text_lower = text.lower()
        
        # Find skills section
        skills_start = -1
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(x in line.lower() for x in ['kompetenser', 'skills', 'färdigheter']):
                skills_start = i
                break
        
        if skills_start >= 0:
            # Count items in skills section
            skills_text = '\n'.join(lines[skills_start:skills_start+20])
            bullet_count = skills_text.count('•') + skills_text.count('·') + skills_text.count('-')
            comma_count = skills_text.count(',')
            return max(bullet_count, comma_count // 3, 5)  # Estimate
        
        return 0
    
    def _check_contact_info(self, text: str) -> bool:
        """Check if contact info is available."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+46|0)\s?7[\d][-\s]?\d{2,3}[-\s]?\d{2,3}'
        return bool(re.search(email_pattern, text)) or bool(re.search(phone_pattern, text))
    
    def _check_custom_url(self, text: str) -> bool:
        """Check if profile has custom LinkedIn URL."""
        # Check for linkedin.com/in/ (custom) vs linkedin.com/in/name-12345/ (default)
        linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9-]+)'
        match = re.search(linkedin_pattern, text)
        if match:
            url_part = match.group(1)
            # Custom URLs are usually just name without numbers
            return not re.search(r'-\d+$', url_part)
        return False
    
    def _detect_industry(self, text: str) -> str:
        """Detect industry from profile content."""
        text_lower = text.lower()
        scores = {}
        
        for industry, keywords in self.KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[industry] = score
        
        return max(scores, key=scores.get) if scores else 'general'
    
    def _analyze_keywords(self, text: str, industry: str) -> Dict:
        """Analyze keyword usage."""
        text_lower = text.lower()
        keywords = self.KEYWORDS.get(industry, self.KEYWORDS['tech'])
        
        found = {}
        missing = []
        
        for keyword in keywords:
            count = len(re.findall(rf'\b{re.escape(keyword)}\b', text_lower))
            if count > 0:
                found[keyword] = count
            else:
                missing.append(keyword)
        
        coverage = (len(found) / len(keywords) * 100) if keywords else 0.0
        
        return {
            'found': found,
            'missing': missing[:5],  # Top 5 missing
            'coverage': coverage
        }
    
    def _calculate_score(self, result: LinkedInAnalysisResult) -> LinkedInScoreBreakdown:
        """Calculate detailed LinkedIn profile score."""
        breakdown = LinkedInScoreBreakdown()
        
        # 1. Headline (15 points)
        if result.has_headline:
            if result.headline_length >= 80 and result.headline_length <= self.HEADLINE_MAX:
                breakdown.headline = 15
            elif result.headline_length >= 40:
                breakdown.headline = 10
            else:
                breakdown.headline = 5
        
        # 2. About Section (20 points)
        if result.has_about:
            if result.about_word_count >= 100 and result.about_word_count <= 400:
                breakdown.about = 20
            elif result.about_word_count >= 50:
                breakdown.about = 15
            elif result.about_word_count >= 20:
                breakdown.about = 10
            else:
                breakdown.about = 5
        
        # 3. Experience (20 points)
        if result.has_experience:
            if result.experience_entries >= 3:
                breakdown.experience = 20
            elif result.experience_entries >= 2:
                breakdown.experience = 15
            elif result.experience_entries >= 1:
                breakdown.experience = 10
        
        # 4. Skills (15 points)
        if result.has_skills:
            if result.skills_count >= 10:
                breakdown.skills = 15
            elif result.skills_count >= 5:
                breakdown.skills = 10
            else:
                breakdown.skills = 5
        
        # 5. Engagement factors (15 points)
        if result.has_custom_url:
            breakdown.engagement += 5
        if result.has_contact_info:
            breakdown.engagement += 5
        if result.keyword_coverage >= 20:
            breakdown.engagement += 5
        
        # 6. Completeness (15 points)
        sections_filled = sum([
            result.has_headline,
            result.has_about,
            result.has_experience,
            result.has_education,
            result.has_skills
        ])
        breakdown.completeness = sections_filled * 3  # 3 points per section
        
        return breakdown
    
    def _generate_critical_issues(self, result: LinkedInAnalysisResult, text: str) -> List[str]:
        """Generate critical issues."""
        issues = []
        
        if not result.has_headline:
            issues.append("Saknar headline - det är det första folk ser på din profil")
        elif result.headline_length < 40:
            issues.append("Headline är för kort - använd hela utrymmet för att beskriva dig")
        
        if not result.has_about:
            issues.append("Saknar About-sektion - detta är din chans att berätta din story")
        elif result.about_word_count < 50:
            issues.append("About-sektionen är för kort - minimum 50 ord rekommenderas")
        
        if not result.has_experience:
            issues.append("Ingen erfarenhet listad - lägg till minst en tjänst")
        
        return issues
    
    def _generate_warnings(self, result: LinkedInAnalysisResult, text: str) -> List[str]:
        """Generate warnings."""
        warnings = []
        
        if not result.has_custom_url:
            warnings.append("Ingen custom LinkedIn URL - skapa en på linkedin.com/in/ditt-namn")
        
        if result.experience_entries < 2:
            warnings.append("Få erfarenhetsposter - lägg till fler om möjligt")
        
        if result.skills_count < 5:
            warnings.append("Få skills listade - lägg till minst 5 relevanta kompetenser")
        
        if not result.has_education:
            warnings.append("Utbildning saknas - lägg till om tillämpligt")
        
        if result.keyword_coverage < 20:
            warnings.append("Låg keyword-täckning - lägg till fler branschspecifika termer")
        
        return warnings
    
    def _generate_suggestions(self, result: LinkedInAnalysisResult, text: str) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if result.headline_length < 80:
            suggestions.append("Utöka din headline - inkludera roll + expertis + nyckelord")
        
        if result.about_word_count < 150:
            suggestions.append("Förläng About-sektionen - berätta om dina styrkor och passioner")
        
        if result.keywords_missing:
            suggestions.append(f"Lägg till keywords: {', '.join(result.keywords_missing[:3])}")
        
        suggestions.append("Lägg till en professionell profilbild om du inte har en")
        suggestions.append("Be om recommendations från kollegor och chefer")
        suggestions.append("Engagera dig regelbundet - gilla, kommentera och dela inlägg")
        
        if self.language == 'sv':
            suggestions.append("Överväg att skriva på engelska för att nå en internationell publik")
        
        return suggestions


class ReportGenerator:
    """Generate reports in various formats."""
    
    def __init__(self, language: str = "sv"):
        self.language = language
    
    def generate(self, analysis: LinkedInAnalysisResult, format_type: str) -> str:
        """Generate report in specified format."""
        if format_type == 'json':
            return self._generate_json(analysis)
        elif format_type == 'human':
            return self._generate_human(analysis)
        elif format_type == 'html':
            return self._generate_html(analysis)
        else:
            raise ValueError(f"Unknown format: {format_type}")
    
    def _generate_json(self, analysis: LinkedInAnalysisResult) -> str:
        """Generate JSON report."""
        data = {
            'metadata': {
                'version': LinkedInOptimizer.VERSION,
                'timestamp': analysis.analysis_timestamp,
                'language': analysis.detected_language
            },
            'profile_score': {
                'total': analysis.profile_score,
                'breakdown': analysis.score_breakdown.to_dict()
            },
            'components': {
                'headline': {
                    'present': analysis.has_headline,
                    'length': analysis.headline_length
                },
                'about': {
                    'present': analysis.has_about,
                    'word_count': analysis.about_word_count
                },
                'experience': {
                    'present': analysis.has_experience,
                    'entries': analysis.experience_entries
                },
                'skills': {
                    'present': analysis.has_skills,
                    'count': analysis.skills_count
                }
            },
            'keywords': {
                'found': analysis.keywords_found,
                'missing': analysis.keywords_missing,
                'coverage': analysis.keyword_coverage
            },
            'recommendations': {
                'critical': analysis.critical_issues,
                'warnings': analysis.warnings,
                'suggestions': analysis.suggestions
            }
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _generate_human(self, analysis: LinkedInAnalysisResult) -> str:
        """Generate human-readable report."""
        score_status = "STARK" if analysis.profile_score >= 80 else "BRA" if analysis.profile_score >= 60 else "BEHOVER ARBETE" if analysis.profile_score >= 40 else "KRITISK"
        
        report = f"""
{'='*60}
   LINKEDIN PROFILANALYS v{LinkedInOptimizer.VERSION}
{'='*60}

PROFILSCORE: {analysis.profile_score}/100 [{score_status}]

Poängfördelning:
  - Headline:        {analysis.score_breakdown.headline}/15
  - About:           {analysis.score_breakdown.about}/20
  - Erfarenhet:      {analysis.score_breakdown.experience}/20
  - Skills:          {analysis.score_breakdown.skills}/15
  - Engagement:      {analysis.score_breakdown.engagement}/15
  - Kompletthet:     {analysis.score_breakdown.completeness}/15

PROFILKOMPONENTER
  [{'X' if analysis.has_headline else ' '}] Headline ({analysis.headline_length} tecken)
  [{'X' if analysis.has_about else ' '}] About-sektion ({analysis.about_word_count} ord)
  [{'X' if analysis.has_experience else ' '}] Erfarenhet ({analysis.experience_entries} poster)
  [{'X' if analysis.has_education else ' '}] Utbildning
  [{'X' if analysis.has_skills else ' '}] Skills ({analysis.skills_count} st)
  [{'X' if analysis.has_custom_url else ' '}] Custom URL

NYCKELORD
  Täckning: {analysis.keyword_coverage:.1f}%
  Hittade: {len(analysis.keywords_found)}
  {', '.join(list(analysis.keywords_found.keys())[:5]) if analysis.keywords_found else 'Inga'}

"""
        
        if analysis.critical_issues:
            report += "KRITISKA ISSUES (Maste fixas)\n"
            for issue in analysis.critical_issues:
                report += f"  [!] {issue}\n"
            report += "\n"
        
        if analysis.warnings:
            report += "VARNINGAR\n"
            for warning in analysis.warnings:
                report += f"  [V] {warning}\n"
            report += "\n"
        
        if analysis.suggestions:
            report += "FÖRBÄTTRINGSFÖRSLAG\n"
            for suggestion in analysis.suggestions:
                report += f"  -> {suggestion}\n"
        
        report += f"\n{'='*60}\n"
        return report
    
    def _generate_html(self, analysis: LinkedInAnalysisResult) -> str:
        """Generate HTML report."""
        score_color = "#48bb78" if analysis.profile_score >= 80 else "#ed8936" if analysis.profile_score >= 60 else "#f56565"
        
        html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>LinkedIn Profilanalys</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .score {{ font-size: 48px; font-weight: bold; color: {score_color}; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .check {{ color: #48bb78; }}
        .cross {{ color: #f56565; }}
        .critical {{ background: #fed7d7; color: #c53030; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .warning {{ background: #feebc8; color: #c05621; padding: 10px; border-radius: 5px; margin: 5px 0; }}
        .suggestion {{ background: #c6f6d5; color: #276749; padding: 10px; border-radius: 5px; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LinkedIn Profilanalys</h1>
        <div class="score">{analysis.profile_score}/100</div>
    </div>
    
    <div class="card">
        <h2>Profilkomponenter</h2>
        <p><span class="{'check' if analysis.has_headline else 'cross'}">{'✓' if analysis.has_headline else '✗'}</span> Headline</p>
        <p><span class="{'check' if analysis.has_about else 'cross'}">{'✓' if analysis.has_about else '✗'}</span> About</p>
        <p><span class="{'check' if analysis.has_experience else 'cross'}">{'✓' if analysis.has_experience else '✗'}</span> Erfarenhet ({analysis.experience_entries} poster)</p>
        <p><span class="{'check' if analysis.has_skills else 'cross'}">{'✓' if analysis.has_skills else '✗'}</span> Skills ({analysis.skills_count})</p>
    </div>
"""
        
        if analysis.critical_issues:
            html += '<div class="card"><h2>Kritiska Issues</h2>'
            for issue in analysis.critical_issues:
                html += f'<div class="critical">{issue}</div>'
            html += '</div>'
        
        if analysis.warnings:
            html += '<div class="card"><h2>Varningar</h2>'
            for warning in analysis.warnings:
                html += f'<div class="warning">{warning}</div>'
            html += '</div>'
        
        if analysis.suggestions:
            html += '<div class="card"><h2>Förslag</h2>'
            for suggestion in analysis.suggestions:
                html += f'<div class="suggestion">{suggestion}</div>'
            html += '</div>'
        
        html += "</body></html>"
        return html


def main():
    """Main entry point."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(
        description='LinkedIn Profile Optimizer - Analyze and improve LinkedIn profiles',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file', help='LinkedIn profile text file')
    parser.add_argument('--industry', '-i', help='Target industry', default='')
    parser.add_argument('--output', '-o', help='Output file path', default='')
    parser.add_argument('--format', '-f', choices=['json', 'human', 'html'], 
                       default='human', help='Output format')
    parser.add_argument('--lang', '-l', choices=['sv', 'en', 'auto'], 
                       default='auto', help='Language')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    try:
        # Initialize optimizer
        optimizer = LinkedInOptimizer(language=args.lang)
        
        # Read file
        text, file_format = optimizer.read_file(file_path)
        
        # Analyze
        analysis = optimizer.analyze_profile(text, args.industry)
        analysis.file_path = str(file_path)
        analysis.file_format = file_format.value
        analysis.file_size_bytes = file_path.stat().st_size
        
        # Generate report
        generator = ReportGenerator(language=analysis.detected_language)
        report = generator.generate(analysis, args.format)
        
        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(report, encoding='utf-8')
            print(f"[OK] Rapport sparad: {output_path}")
        else:
            print(report)
        
        # Exit code based on score
        if analysis.profile_score < 50:
            exit(1)
        elif analysis.profile_score < 70:
            exit(2)
        else:
            exit(0)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"[ERROR] {e}")
        exit(1)


if __name__ == "__main__":
    main()
