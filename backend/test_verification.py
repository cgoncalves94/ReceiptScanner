#!/usr/bin/env python3
"""Quick verification script to check if test file is valid."""

import sys
import ast

def check_test_file():
    """Parse and validate the test file."""
    test_file = "tests/unit/receipt/test_pdf_generator.py"

    try:
        with open(test_file, 'r') as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content)

        # Count test functions
        test_functions = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
        ]

        print(f"✓ Test file is valid Python")
        print(f"✓ Found {len(test_functions)} test functions:")
        for test_name in test_functions:
            print(f"  - {test_name}")

        # Check for required imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append(node.module)

        required_modules = [
            'app.receipt.pdf_generator',
            'app.receipt.models',
            'app.category.models'
        ]

        print(f"\n✓ Required imports present:")
        for module in required_modules:
            if module in imports:
                print(f"  - {module}")
            else:
                print(f"  ✗ Missing: {module}")
                return False

        print(f"\n✓ All checks passed!")
        return True

    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_test_file()
    sys.exit(0 if success else 1)
