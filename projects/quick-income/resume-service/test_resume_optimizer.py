# Resume Optimizer Testing Suite
# Tests edge cases and validates functionality

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from resume_optimizer import (
    ResumeOptimizer, ReportGenerator, AnalysisResult, ATSScoreBreakdown,
    FileReadError, FileFormat, OutputFormat, create_sample_resume
)

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def test_empty_file():
    """Test handling of empty files."""
    print("Testing empty file handling...")
    optimizer = ResumeOptimizer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("")
        temp_path = Path(f.name)
    
    try:
        optimizer.read_file(temp_path)
        print(f"  {FAIL} Should have raised ValueError for empty file")
    except ValueError as e:
        print(f"  {PASS} Correctly raised ValueError: {e}")
    finally:
        temp_path.unlink()


def test_large_file():
    """Test handling of oversized files."""
    print("Testing large file handling...")
    optimizer = ResumeOptimizer()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("x" * (11 * 1024 * 1024))  # 11MB
        temp_path = Path(f.name)
    
    try:
        optimizer.read_file(temp_path)
        print(f"  {FAIL} Should have raised ValueError for large file")
    except ValueError as e:
        print(f"  {PASS} Correctly raised ValueError: {e}")
    finally:
        temp_path.unlink()


def test_nonexistent_file():
    """Test handling of non-existent files."""
    print("Testing non-existent file handling...")
    optimizer = ResumeOptimizer()
    
    try:
        optimizer.read_file(Path("/nonexistent/path/resume.txt"))
        print(f"  {FAIL} Should have raised FileNotFoundError")
    except FileNotFoundError:
        print(f"  {PASS} Correctly raised FileNotFoundError")


def test_swedish_phone_detection():
    """Test Swedish phone number formats."""
    print("Testing Swedish phone format detection...")
    optimizer = ResumeOptimizer()
    
    swedish_phones = [
        ("070-123 45 67", True),
        ("+46 70 123 45 67", True),
        ("0701234567", True),
        ("0723-456789", True),
        ("not a phone", False),
    ]
    
    for phone, expected in swedish_phones:
        result = optimizer._check_phone(f"Contact: {phone}")
        status = PASS if result == expected else FAIL
        print(f"  {status}: {phone} -> {result}")


def test_email_detection():
    """Test email address detection."""
    print("Testing email detection...")
    optimizer = ResumeOptimizer()
    
    emails = [
        ("john@example.com", True),
        ("john.doe@company.co.uk", True),
        ("invalid email", False),
        ("test@localhost", False),
    ]
    
    for email, expected in emails:
        result = optimizer._check_email(f"Email: {email}")
        status = PASS if result == expected else FAIL
        print(f"  {status}: {email}")


def test_ats_scoring():
    """Test ATS scoring algorithm."""
    print("Testing ATS scoring...")
    optimizer = ResumeOptimizer()
    
    # Create a minimal valid analysis
    analysis = AnalysisResult(
        file_path="test.txt",
        file_format="txt",
        file_size_bytes=1000,
        text_hash="abc123",
        analysis_timestamp="2024-01-01T00:00:00"
    )
    
    # Test with good content
    analysis.word_count = 450
    analysis.has_email = True
    analysis.has_phone = True
    analysis.has_contact_info = True
    analysis.has_summary = True
    analysis.has_experience = True
    analysis.has_education = True
    analysis.has_skills_section = True
    analysis.bullet_points = 15
    analysis.power_verb_variety = 8
    analysis.quantified_achievements = 5
    analysis.keyword_coverage = 40
    analysis.bullet_quality_score = 75
    
    score, breakdown = optimizer._calculate_detailed_ats_score(analysis, "test")
    
    print(f"  Total Score: {score}/100")
    print(f"    Contact Info: {breakdown.contact_info}/15")
    print(f"    Structure: {breakdown.structure}/20")
    print(f"    Content: {breakdown.content_quality}/20")
    print(f"    Keywords: {breakdown.keywords}/20")
    print(f"    Formatting: {breakdown.formatting}/10")
    print(f"    Readability: {breakdown.readability}/15")
    
    if score >= 70:
        print(f"  {PASS} Good ATS score achieved")
    else:
        print(f"  {WARN} Score {score} is below 70")


def test_report_generation():
    """Test all report formats."""
    print("Testing report generation...")
    
    analysis = AnalysisResult(
        file_path="test.pdf",
        file_format="pdf",
        file_size_bytes=5000,
        text_hash="def456",
        analysis_timestamp="2024-01-01T00:00:00",
        word_count=450,
        ats_score=75,
        has_contact_info=True,
        has_email=True,
        has_phone=True,
        has_summary=True,
        detected_industry="tech"
    )
    analysis.keywords_found = {'python': 3, 'javascript': 2, 'react': 1}
    analysis.score_breakdown = ATSScoreBreakdown(
        contact_info=15, structure=18, content_quality=15,
        keywords=15, formatting=8, readability=14, total=75
    )
    analysis.suggestions = ["Add more keywords"]
    
    generator = ReportGenerator()
    
    formats = [
        (OutputFormat.JSON, "json"),
        (OutputFormat.HUMAN, "human"),
        (OutputFormat.MARKDOWN, "markdown"),
        (OutputFormat.HTML, "html"),
    ]
    
    for fmt, name in formats:
        try:
            report = generator.generate(analysis, fmt)
            if len(report) > 0:
                print(f"  {PASS} {name} format generated ({len(report)} chars)")
            else:
                print(f"  {FAIL} {name} format is empty")
        except Exception as e:
            print(f"  {FAIL} {name} error: {e}")


def test_keyword_extraction():
    """Test keyword extraction and suggestions."""
    print("Testing keyword extraction...")
    optimizer = ResumeOptimizer()
    
    # Tech resume sample
    tech_resume = """
    John Doe - Software Engineer
    
    EXPERIENCE
    Senior Developer at Tech Corp
    • Built web applications using Python and JavaScript
    • Managed AWS cloud infrastructure
    • Implemented REST APIs and microservices
    """
    
    result = optimizer._analyze_keywords(tech_resume, 'tech')
    
    print(f"  Keywords Found: {len(result['found'])}")
    print(f"  Coverage: {result['coverage']:.1f}%")
    print(f"  Missing: {len(result['missing'])}")
    
    if 'python' in result['found']:
        print(f"  {PASS} Python keyword detected")
    else:
        print(f"  {FAIL} Python keyword not detected")


def test_swedish_cv():
    """Test Swedish CV handling."""
    print("Testing Swedish CV handling...")
    optimizer = ResumeOptimizer(language='sv')
    
    swedish_cv = """
    Anna Svensson
    Stockholm
    anna.svensson@email.se | 070-123 45 67
    
    SAMMANFATTNING
    Erfaren systemutvecklare med kunskap inom Python och JavaScript.
    
    ERFARENHET
    Systemutvecklare pa Tech AB
    • Utvecklade webbapplikationer
    • Ledde ett team av 3 utvecklare
    • Forbattrade prestanda med 40%
    
    UTBILDNING
    Civilingenjor, KTH
    
    KOMPETENSER
    Python, JavaScript, AWS, Docker
    """
    
    analysis = optimizer.analyze_resume(swedish_cv, "Systemutvecklare")
    
    print(f"  Language: {analysis.detected_language}")
    print(f"  Word Count: {analysis.word_count}")
    print(f"  ATS Score: {analysis.ats_score}")
    print(f"  Power Verbs: {analysis.power_verbs}")
    print(f"  Has Summary: {analysis.has_summary}")
    print(f"  Has Experience: {analysis.has_experience}")
    
    if analysis.detected_language == 'sv':
        print(f"  {PASS} Swedish language handled")
    else:
        print(f"  {WARN} Language not detected as Swedish")


def test_full_analysis():
    """Test full analysis workflow."""
    print("Testing full analysis workflow...")
    optimizer = ResumeOptimizer()
    
    # Create sample resume file
    sample = create_sample_resume()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(sample)
        temp_path = Path(f.name)
    
    try:
        # Read and analyze
        text, file_format = optimizer.read_file(temp_path)
        analysis = optimizer.analyze_resume(text, "Software Engineer")
        
        print(f"  File Format: {file_format.value}")
        print(f"  Word Count: {analysis.word_count}")
        print(f"  ATS Score: {analysis.ats_score}")
        print(f"  Keywords: {len(analysis.keywords_found)}")
        print(f"  Suggestions: {len(analysis.suggestions)}")
        
        # Generate report
        generator = ReportGenerator()
        report = generator.generate(analysis, OutputFormat.HUMAN)
        
        if len(report) > 500:
            print(f"  {PASS} Full workflow completed")
        else:
            print(f"  {FAIL} Report too short")
            
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
    finally:
        temp_path.unlink()


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("RESUME OPTIMIZER TEST SUITE")
    print("="*60)
    print()
    
    tests = [
        test_empty_file,
        test_large_file,
        test_nonexistent_file,
        test_swedish_phone_detection,
        test_email_detection,
        test_ats_scoring,
        test_report_generation,
        test_keyword_extraction,
        test_swedish_cv,
        test_full_analysis,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1
        print()
    
    print("="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
