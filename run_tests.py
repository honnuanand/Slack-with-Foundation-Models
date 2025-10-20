#!/usr/bin/env python3
"""
Test runner script for the Slack Foundation Models project
Provides various test execution options and generates comprehensive reports
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
import json


def run_command(cmd, description):
    """Run a shell command and handle output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ {description} failed!")
        print(f"Error output:\n{result.stderr}")
        return False
    else:
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print(result.stdout)
        return True


def install_dependencies():
    """Install test dependencies"""
    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pytest-timeout>=2.1.0",
        "pytest-asyncio>=0.21.0",
        "coverage>=7.0.0",
    ]

    print("\n📦 Installing test dependencies...")
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")


def run_unit_tests():
    """Run unit tests only"""
    return run_command(
        "pytest tests/ -m 'not integration and not performance' -v",
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests only"""
    return run_command(
        "pytest tests/ -m integration -v",
        "Integration Tests"
    )


def run_performance_tests():
    """Run performance tests only"""
    return run_command(
        "pytest tests/ -m performance -v",
        "Performance Tests"
    )


def run_all_tests():
    """Run all tests with coverage"""
    return run_command(
        "pytest tests/ -v --cov --cov-report=term-missing --cov-report=html",
        "All Tests with Coverage"
    )


def run_specific_file(file_path):
    """Run tests in a specific file"""
    return run_command(
        f"pytest {file_path} -v --cov --cov-report=term-missing",
        f"Tests in {file_path}"
    )


def run_specific_test(test_path):
    """Run a specific test"""
    return run_command(
        f"pytest {test_path} -v",
        f"Specific test: {test_path}"
    )


def generate_coverage_report():
    """Generate detailed coverage report"""
    commands = [
        ("coverage run -m pytest tests/", "Collecting coverage data"),
        ("coverage report", "Coverage summary"),
        ("coverage html", "HTML coverage report"),
        ("coverage xml", "XML coverage report"),
        ("coverage json", "JSON coverage report"),
    ]

    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False

    print("\n📊 Coverage reports generated:")
    print("  - HTML report: htmlcov/index.html")
    print("  - XML report: coverage.xml")
    print("  - JSON report: coverage.json")
    return True


def run_quick_check():
    """Run a quick test check (fast tests only)"""
    return run_command(
        "pytest tests/ -m 'not slow and not integration' -v --tb=short",
        "Quick Test Check"
    )


def run_ci_tests():
    """Run tests suitable for CI/CD pipeline"""
    return run_command(
        "pytest tests/ -m 'not skip_ci' -v --cov --cov-fail-under=80 --junitxml=test-results.xml",
        "CI/CD Tests"
    )


def check_test_quality():
    """Check test quality metrics"""
    print("\n🔍 Checking test quality...")

    # Count tests
    result = subprocess.run(
        "pytest tests/ --collect-only -q",
        shell=True,
        capture_output=True,
        text=True
    )
    test_count = len([line for line in result.stdout.split('\n') if 'test' in line])
    print(f"  Total tests found: {test_count}")

    # Check coverage
    run_command(
        "coverage report --skip-covered --show-missing",
        "Coverage Analysis"
    )

    return True


def create_test_report():
    """Create a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.txt"

    with open(report_file, 'w') as f:
        f.write("SLACK FOUNDATION MODELS - TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")

        # Run tests and capture output
        result = subprocess.run(
            "pytest tests/ -v --tb=short --cov --cov-report=term",
            shell=True,
            capture_output=True,
            text=True
        )

        f.write("TEST RESULTS:\n")
        f.write("-"*40 + "\n")
        f.write(result.stdout)
        f.write("\n")

        if result.stderr:
            f.write("ERRORS:\n")
            f.write("-"*40 + "\n")
            f.write(result.stderr)
            f.write("\n")

    print(f"\n📄 Test report saved to: {report_file}")
    return report_file


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Test runner for Slack Foundation Models project"
    )

    parser.add_argument(
        "command",
        choices=[
            "all", "unit", "integration", "performance",
            "quick", "ci", "coverage", "quality", "report", "install"
        ],
        help="Test command to run"
    )

    parser.add_argument(
        "--file",
        help="Run tests in a specific file"
    )

    parser.add_argument(
        "--test",
        help="Run a specific test (e.g., tests/test_chat_cli.py::TestColors::test_color_codes)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    print("\n🚀 Slack Foundation Models - Test Runner")
    print("="*60)

    # Handle specific file or test
    if args.file:
        success = run_specific_file(args.file)
    elif args.test:
        success = run_specific_test(args.test)
    else:
        # Handle commands
        commands = {
            "all": run_all_tests,
            "unit": run_unit_tests,
            "integration": run_integration_tests,
            "performance": run_performance_tests,
            "quick": run_quick_check,
            "ci": run_ci_tests,
            "coverage": generate_coverage_report,
            "quality": check_test_quality,
            "report": create_test_report,
            "install": install_dependencies,
        }

        command_func = commands.get(args.command)
        if command_func:
            success = command_func()
        else:
            print(f"❌ Unknown command: {args.command}")
            success = False

    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ Test execution completed successfully!")
    else:
        print("❌ Test execution failed!")
        sys.exit(1)

    # Show coverage report location if it exists
    if os.path.exists("htmlcov/index.html"):
        print("\n📊 View detailed coverage report:")
        print(f"   open htmlcov/index.html")


if __name__ == "__main__":
    main()