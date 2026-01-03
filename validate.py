#!/usr/bin/env python3
"""
Validation script to check if the Agent Orchestrator is properly set up.
Run this before starting the service to catch configuration issues early.
"""
import os
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        return False, f"Python 3.9+ required, found {version.major}.{version.minor}"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_openai_key():
    """Check if OpenAI API key is set"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return False, "OPENAI_API_KEY not set"
    if not key.startswith("sk-"):
        return False, "OPENAI_API_KEY doesn't look valid (should start with 'sk-')"
    return True, f"Key found: {key[:10]}..."


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "langgraph",
        "langchain_core",
        "langchain_openai",
        "openai",
        "httpx",
        "pytest",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    return True, "All required packages installed"


def check_project_structure():
    """Check if all required files exist"""
    project_root = Path(__file__).parent
    required_files = [
        "app/main.py",
        "app/models.py",
        "app/graph.py",
        "app/llm.py",
        "app/rules.py",
        "app/tools.py",
        "app/state.py",
        "tests/test_graph.py",
        "requirements.txt",
        "README.md",
    ]
    
    missing = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing.append(file_path)
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    return True, "All required files present"


def check_imports():
    """Check if core modules can be imported"""
    try:
        from app.models import AgentState, Car, ZonePolicy
        from app.graph import build_graph
        from app.llm import LLMClient
        from app.rules import decide_eligibility
        from app.tools import list_user_cars
        from app.state import SessionStore
        return True, "All core modules import successfully"
    except ImportError as e:
        return False, f"Import error: {str(e)}"


def main():
    """Run all validation checks"""
    print("🔍 Agent Orchestrator - Validation Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("OpenAI API Key", check_openai_key),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Module Imports", check_imports),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}: Error during check - {str(e)}")
            all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("✅ All checks passed! Ready to start the service.")
        print()
        print("Next steps:")
        print("  1. Run: ./start.sh")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Test: ./test_api.sh")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Set API key: export OPENAI_API_KEY='sk-...'")
        print("  • Activate venv: source venv/bin/activate")
        return 1


if __name__ == "__main__":
    sys.exit(main())
