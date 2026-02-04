#!/usr/bin/env python3
"""
AI Resume Optimizer
===================
Optimizes CVs for ATS systems and human recruiters.
Generates tailored cover letters.

Usage: python resume_optimizer.py input.pdf --job "Software Engineer" --output optimized.pdf
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json

class ResumeOptimizer:
    """AI-powered resume optimization tool."""
    
    # ATS-friendly keywords by industry
    KEYWORDS = {
        'tech': ['agile', 'scrum', 'python', 'javascript', 'cloud', 'aws', 'api', 'git', 'ci/cd'],
        'sales': ['crm', 'pipeline', 'quota', 'b2b', 'b2c', 'negotiation', 'closing', 'prospecting'],
        'marketing': ['seo', 'sem', 'google analytics', 'content strategy', 'social media', 'roi'],
        'admin': ['excel', 'outlook', 'crm', 'data entry', 'scheduling', 'multitasking'],
        'finance': ['accounting', 'excel', 'budgeting', 'forecasting', 'gaap', 'erp'],
    }
    
    # Power verbs for resumes
    POWER_VERBS = [
        'achieved', 'improved', 'trained', 'managed', 'created', 'resolved',
        'volunteered', 'influenced', 'increased', 'decreased', 'launched',
        'generated', 'negotiated', 'streamlined', 'transformed'
    ]
    
    def __init__(self):
        self.suggestions = []
        self.score = 0
    
    def analyze_resume(self, text: str, job_title: str = "") -> Dict:
        """Analyze a resume and provide optimization suggestions."""
        analysis = {
            'word_count': len(text.split()),
            'has_contact_info': self._check_contact_info(text),
            'has_summary': self._check_summary(text),
            'bullet_points': self._count_bullets(text),
            'power_verbs': self._count_power_verbs(text),
            'industry_keywords': self._check_keywords(text, job_title),
            'ats_score': 0,
            'suggestions': []
        }
        
        # Calculate ATS score
        analysis['ats_score'] = self._calculate_ats_score(analysis)
        analysis['suggestions'] = self._generate_suggestions(analysis)
        
        return analysis
    
    def _check_contact_info(self, text: str) -> bool:
        """Check if resume has contact information."""
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        has_phone = bool(re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text))
        return has_email and has_phone
    
    def _check_summary(self, text: str) -> bool:
        """Check if resume has a professional summary."""
        summary_keywords = ['summary', 'professional summary', 'profile', 'about me', 'objective']
        return any(keyword in text.lower() for keyword in summary_keywords)
    
    def _count_bullets(self, text: str) -> int:
        """Count bullet points in resume."""
        bullet_patterns = [r'•', r'\*', r'-', r'○', r'▪']
        count = 0
        for pattern in bullet_patterns:
            count += len(re.findall(pattern, text))
        return count
    
    def _count_power_verbs(self, text: str) -> int:
        """Count usage of power verbs."""
        text_lower = text.lower()
        count = 0
        for verb in self.POWER_VERBS:
            count += len(re.findall(r'\b' + verb + r'\b', text_lower))
        return count
    
    def _check_keywords(self, text: str, job_title: str) -> Dict[str, int]:
        """Check for industry-specific keywords."""
        text_lower = text.lower()
        found_keywords = {}
        
        # Detect industry from job title or use general
        industry = self._detect_industry(job_title)
        keywords = self.KEYWORDS.get(industry, self.KEYWORDS['tech'])
        
        for keyword in keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            if count > 0:
                found_keywords[keyword] = count
        
        return found_keywords
    
    def _detect_industry(self, job_title: str) -> str:
        """Detect industry from job title."""
        job_lower = job_title.lower()
        
        if any(word in job_lower for word in ['software', 'developer', 'engineer', 'programmer', 'it']):
            return 'tech'
        elif any(word in job_lower for word in ['sales', 'account executive', 'business development']):
            return 'sales'
        elif any(word in job_lower for word in ['marketing', 'content', 'seo', 'social media']):
            return 'marketing'
        elif any(word in job_lower for word in ['accountant', 'finance', 'analyst', 'controller']):
            return 'finance'
        elif any(word in job_lower for word in ['admin', 'assistant', 'coordinator', 'office']):
            return 'admin'
        else:
            return 'tech'
    
    def _calculate_ats_score(self, analysis: Dict) -> int:
        """Calculate overall ATS compatibility score."""
        score = 0
        
        # Contact info (20 points)
        if analysis['has_contact_info']:
            score += 20
        
        # Summary (15 points)
        if analysis['has_summary']:
            score += 15
        
        # Bullet points (15 points) - ideal: 10-20
        bullets = analysis['bullet_points']
        if 10 <= bullets <= 20:
            score += 15
        elif 5 <= bullets < 10:
            score += 10
        elif bullets > 20:
            score += 10
        
        # Power verbs (20 points)
        if analysis['power_verbs'] >= 5:
            score += 20
        elif analysis['power_verbs'] >= 3:
            score += 10
        
        # Keywords (30 points)
        keyword_count = len(analysis['industry_keywords'])
        if keyword_count >= 5:
            score += 30
        elif keyword_count >= 3:
            score += 20
        elif keyword_count >= 1:
            score += 10
        
        return min(score, 100)
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if not analysis['has_contact_info']:
            suggestions.append("❌ Add email and phone number at the top")
        
        if not analysis['has_summary']:
            suggestions.append("❌ Add a 2-3 sentence professional summary")
        
        if analysis['bullet_points'] < 5:
            suggestions.append("⚠️ Add more bullet points to describe achievements")
        elif analysis['bullet_points'] > 25:
            suggestions.append("⚠️ Too many bullet points - focus on top 10-15 achievements")
        
        if analysis['power_verbs'] < 3:
            suggestions.append("⚠️ Use more action verbs (achieved, improved, managed, created)")
        
        if len(analysis['industry_keywords']) < 3:
            suggestions.append("⚠️ Add more industry-specific keywords for ATS optimization")
        
        if analysis['word_count'] > 600:
            suggestions.append("⚠️ Resume is too long - aim for 400-500 words")
        elif analysis['word_count'] < 200:
            suggestions.append("⚠️ Resume is too short - add more detail")
        
        return suggestions
    
    def generate_cover_letter(self, resume_text: str, job_title: str, company: str) -> str:
        """Generate a tailored cover letter."""
        # Extract key achievements from resume
        achievements = self._extract_achievements(resume_text)
        
        template = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my background and expertise, I am confident I can make an immediate impact on your team.

{achievements}

I am particularly drawn to {company} because of its reputation for innovation and excellence. I believe my skills and experience align perfectly with your needs, and I am excited about the opportunity to contribute to your continued success.

I would welcome the opportunity to discuss how I can add value to your team. Thank you for considering my application.

Sincerely,
[Your Name]
"""
        return template
    
    def _extract_achievements(self, text: str) -> str:
        """Extract key achievements from resume text."""
        # Simple extraction - in real implementation would use AI
        sentences = re.split(r'[.!?]+', text)
        achievement_sentences = []
        
        for sentence in sentences:
            if any(verb in sentence.lower() for verb in self.POWER_VERBS):
                if len(sentence.strip()) > 20:  # Not too short
                    achievement_sentences.append(sentence.strip())
        
        if achievement_sentences:
            return " ".join(achievement_sentences[:3])  # Top 3 achievements
        else:
            return "Throughout my career, I have consistently delivered results and exceeded expectations in every role I have held."


def main():
    parser = argparse.ArgumentParser(description='AI Resume Optimizer')
    parser.add_argument('file', help='Resume file (txt or pdf)')
    parser.add_argument('--job', '-j', help='Target job title', default='')
    parser.add_argument('--company', '-c', help='Target company', default='')
    parser.add_argument('--output', '-o', help='Output file for report', default='resume_analysis.json')
    parser.add_argument('--cover-letter', action='store_true', help='Generate cover letter')
    
    args = parser.parse_args()
    
    optimizer = ResumeOptimizer()
    
    # Read file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    try:
        text = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Analyze
    analysis = optimizer.analyze_resume(text, args.job)
    
    # Print results
    print("\n" + "="*50)
    print("RESUME ANALYSIS REPORT")
    print("="*50)
    print(f"\n📊 ATS Compatibility Score: {analysis['ats_score']}/100")
    print(f"📝 Word Count: {analysis['word_count']}")
    print(f"✅ Contact Info: {'Yes' if analysis['has_contact_info'] else 'No'}")
    print(f"✅ Professional Summary: {'Yes' if analysis['has_summary'] else 'No'}")
    print(f"• Bullet Points: {analysis['bullet_points']}")
    print(f"⚡ Power Verbs Used: {analysis['power_verbs']}")
    
    print(f"\n🏷️ Industry Keywords Found: {len(analysis['industry_keywords'])}")
    for keyword, count in analysis['industry_keywords'].items():
        print(f"   - {keyword}: {count}x")
    
    print(f"\n💡 Suggestions:")
    for suggestion in analysis['suggestions']:
        print(f"   {suggestion}")
    
    # Generate cover letter if requested
    if args.cover_letter and args.job and args.company:
        print(f"\n" + "="*50)
        print("COVER LETTER")
        print("="*50)
        cover_letter = optimizer.generate_cover_letter(text, args.job, args.company)
        print(cover_letter)
    
    # Save analysis
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full analysis saved to: {args.output}")


if __name__ == '__main__':
    main()
