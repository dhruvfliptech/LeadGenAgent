#!/usr/bin/env python3
"""
Test script for CAPTCHA integration and email extraction.
This script tests the components individually before full integration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.scrapers.captcha_solver import CaptchaSolver
from app.scrapers.email_extractor import EmailExtractor
from app.scrapers.craigslist_scraper import CraigslistScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_captcha_solver():
    """Test the CAPTCHA solver initialization and basic functionality."""
    logger.info("Testing CAPTCHA solver...")
    
    try:
        # Test with dummy API key
        captcha_solver = CaptchaSolver("dummy_api_key_for_testing")
        logger.info("✅ CAPTCHA solver initialized successfully")
        
        # Test cost tracking
        initial_cost = captcha_solver.get_total_cost()
        logger.info(f"✅ Initial cost tracking: ${initial_cost}")
        
        captcha_solver.reset_cost_tracking()
        reset_cost = captcha_solver.get_total_cost()
        logger.info(f"✅ Cost reset successfully: ${reset_cost}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CAPTCHA solver test failed: {str(e)}")
        return False


async def test_email_extractor():
    """Test the email extractor initialization."""
    logger.info("Testing email extractor...")
    
    try:
        # Create with dummy CAPTCHA solver
        captcha_solver = CaptchaSolver("dummy_api_key_for_testing")
        email_extractor = EmailExtractor(captcha_solver)
        logger.info("✅ Email extractor initialized successfully")
        
        # Test email validation
        test_emails = [
            ("test@example.com", True),
            ("invalid-email", False),
            ("user@craigslist.org", False),
            ("noreply@test.com", False),
            ("valid.email+tag@domain.co.uk", True)
        ]
        
        for email, expected in test_emails:
            result = email_extractor._is_valid_email(email)
            if result == expected:
                logger.info(f"✅ Email validation correct for '{email}': {result}")
            else:
                logger.error(f"❌ Email validation failed for '{email}': expected {expected}, got {result}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Email extractor test failed: {str(e)}")
        return False


async def test_scraper_integration():
    """Test the updated Craigslist scraper with email extraction capabilities."""
    logger.info("Testing scraper integration...")
    
    try:
        # Test scraper initialization without email extraction
        scraper = CraigslistScraper()
        logger.info("✅ Basic scraper initialized successfully")
        
        # Test scraper initialization with email extraction (dummy key)
        scraper_with_email = CraigslistScraper(
            captcha_api_key="dummy_api_key",
            enable_email_extraction=True
        )
        logger.info("✅ Scraper with email extraction initialized successfully")
        
        # Test cost tracking
        cost = scraper_with_email.get_captcha_cost()
        logger.info(f"✅ Cost tracking working: ${cost}")
        
        # Test cost reset
        scraper_with_email.reset_captcha_cost()
        reset_cost = scraper_with_email.get_captcha_cost()
        logger.info(f"✅ Cost reset working: ${reset_cost}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Scraper integration test failed: {str(e)}")
        return False


async def test_configuration():
    """Test configuration settings."""
    logger.info("Testing configuration...")
    
    try:
        from app.core.config import settings
        
        # Test CAPTCHA settings
        logger.info(f"✅ CAPTCHA timeout: {settings.CAPTCHA_TIMEOUT}")
        logger.info(f"✅ CAPTCHA max retries: {settings.CAPTCHA_MAX_RETRIES}")
        logger.info(f"✅ Enable email extraction: {settings.ENABLE_EMAIL_EXTRACTION}")
        logger.info(f"✅ Email extraction concurrency: {settings.EMAIL_EXTRACTION_MAX_CONCURRENT}")
        
        # Check if API key is configured
        api_key_configured = bool(settings.TWOCAPTCHA_API_KEY)
        logger.info(f"✅ CAPTCHA API key configured: {api_key_configured}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}")
        return False


async def test_dependencies():
    """Test that all required dependencies are available."""
    logger.info("Testing dependencies...")
    
    dependencies = [
        ("playwright", "playwright.async_api"),
        ("twocaptcha", "twocaptcha"),
        ("sqlalchemy", "sqlalchemy"),
        ("fastapi", "fastapi"),
        ("redis", "redis")
    ]
    
    all_good = True
    
    for dep_name, import_path in dependencies:
        try:
            __import__(import_path)
            logger.info(f"✅ {dep_name} available")
        except ImportError as e:
            logger.error(f"❌ {dep_name} not available: {str(e)}")
            all_good = False
    
    return all_good


async def main():
    """Run all tests."""
    logger.info("Starting CAPTCHA integration tests...")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("CAPTCHA Solver", test_captcha_solver),
        ("Email Extractor", test_email_extractor),
        ("Scraper Integration", test_scraper_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
        
        except Exception as e:
            logger.error(f"❌ {test_name} test ERROR: {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! CAPTCHA integration is ready.")
        return 0
    else:
        logger.error("🚨 Some tests failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)