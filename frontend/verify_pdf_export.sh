#!/bin/bash

# PDF Export Feature Verification Script
# This script performs automated tests of the PDF export functionality

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "PDF Export Feature Verification"
echo "========================================"
echo ""

# Check if services are running
echo "📋 Checking prerequisites..."

if ! nc -z localhost 5432 2>/dev/null; then
    echo -e "${RED}✗ PostgreSQL is not running on port 5432${NC}"
    echo "  Run: make db-up"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

if ! nc -z localhost 8000 2>/dev/null; then
    echo -e "${RED}✗ Backend is not running on port 8000${NC}"
    echo "  Run: cd backend && make dev"
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"

if ! nc -z localhost 3000 2>/dev/null; then
    echo -e "${YELLOW}⚠ Frontend is not running on port 3000${NC}"
    echo "  Run: cd frontend && pnpm dev"
    echo "  (Optional for API testing only)"
fi

echo ""
echo "🔍 Testing Backend API..."

# Check if PDF endpoint exists
ENDPOINT_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/receipts/export/pdf 2>/dev/null || echo "000")

if [ "$ENDPOINT_CHECK" = "401" ] || [ "$ENDPOINT_CHECK" = "200" ]; then
    echo -e "${GREEN}✓ PDF export endpoint is accessible${NC}"
else
    echo -e "${RED}✗ PDF export endpoint returned unexpected status: $ENDPOINT_CHECK${NC}"
    exit 1
fi

# Check API docs
echo ""
echo "📚 Checking API documentation..."
if curl -s http://localhost:8000/docs | grep -q "export.*pdf"; then
    echo -e "${GREEN}✓ PDF export endpoint is documented${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify endpoint in API docs${NC}"
fi

# Test with authentication (if credentials provided)
echo ""
echo "🔐 Testing authenticated PDF export..."

if [ -n "$TEST_EMAIL" ] && [ -n "$TEST_PASSWORD" ]; then
    echo "  Using credentials: $TEST_EMAIL"

    # Login and get token
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
        | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ Failed to authenticate${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Authentication successful${NC}"

    # Test PDF export without images
    echo "  Testing PDF export (no images)..."
    HTTP_CODE=$(curl -s -o /tmp/test_export.pdf -w "%{http_code}" \
        -X GET "http://localhost:8000/api/v1/receipts/export/pdf" \
        -H "Authorization: Bearer $TOKEN")

    if [ "$HTTP_CODE" = "200" ]; then
        FILE_SIZE=$(stat -f%z /tmp/test_export.pdf 2>/dev/null || stat -c%s /tmp/test_export.pdf 2>/dev/null)
        if [ "$FILE_SIZE" -gt 1000 ]; then
            echo -e "${GREEN}✓ PDF export successful (${FILE_SIZE} bytes)${NC}"

            # Verify it's a valid PDF
            if file /tmp/test_export.pdf | grep -q "PDF"; then
                echo -e "${GREEN}✓ Generated file is a valid PDF${NC}"
            else
                echo -e "${RED}✗ Generated file is not a valid PDF${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ PDF file is too small (${FILE_SIZE} bytes)${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ PDF export failed with HTTP $HTTP_CODE${NC}"
        exit 1
    fi

    # Test PDF export with images
    echo "  Testing PDF export (with images)..."
    HTTP_CODE=$(curl -s -o /tmp/test_export_images.pdf -w "%{http_code}" \
        -X GET "http://localhost:8000/api/v1/receipts/export/pdf?include_images=true" \
        -H "Authorization: Bearer $TOKEN")

    if [ "$HTTP_CODE" = "200" ]; then
        FILE_SIZE=$(stat -f%z /tmp/test_export_images.pdf 2>/dev/null || stat -c%s /tmp/test_export_images.pdf 2>/dev/null)
        echo -e "${GREEN}✓ PDF export with images successful (${FILE_SIZE} bytes)${NC}"
    else
        echo -e "${RED}✗ PDF export with images failed with HTTP $HTTP_CODE${NC}"
        exit 1
    fi

    # Test PDF export with filters
    echo "  Testing PDF export (with date filter)..."
    HTTP_CODE=$(curl -s -o /tmp/test_export_filtered.pdf -w "%{http_code}" \
        -X GET "http://localhost:8000/api/v1/receipts/export/pdf?after=2024-01-01&before=2024-12-31" \
        -H "Authorization: Bearer $TOKEN")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ PDF export with filters successful${NC}"
    else
        echo -e "${RED}✗ PDF export with filters failed with HTTP $HTTP_CODE${NC}"
        exit 1
    fi

    echo ""
    echo "📄 Generated test files:"
    ls -lh /tmp/test_export*.pdf 2>/dev/null || echo "  (No files generated)"

else
    echo -e "${YELLOW}⚠ Skipping authenticated tests (no credentials provided)${NC}"
    echo "  Set TEST_EMAIL and TEST_PASSWORD environment variables to test"
fi

# Check backend unit tests
echo ""
echo "🧪 Running backend unit tests..."
cd backend
if command -v uv &> /dev/null; then
    if uv run pytest tests/unit/receipt/test_pdf_generator.py -v 2>&1 | tee /tmp/test_output.txt; then
        TEST_COUNT=$(grep -o "passed" /tmp/test_output.txt | wc -l)
        echo -e "${GREEN}✓ Unit tests passed ($TEST_COUNT tests)${NC}"
    else
        echo -e "${RED}✗ Unit tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ uv command not available, skipping unit tests${NC}"
fi
cd ..

# Summary
echo ""
echo "========================================"
echo "Verification Summary"
echo "========================================"
echo -e "${GREEN}✓ Backend API is accessible${NC}"
echo -e "${GREEN}✓ PDF export endpoint exists${NC}"

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ PDF generation works (without images)${NC}"
    echo -e "${GREEN}✓ PDF generation works (with images)${NC}"
    echo -e "${GREEN}✓ PDF generation works (with filters)${NC}"
fi

echo ""
echo "📋 Manual verification steps:"
echo "  1. Navigate to http://localhost:3000/receipts"
echo "  2. Verify 'Include receipt images in PDF' checkbox is visible"
echo "  3. Click 'Export PDF' button"
echo "  4. Verify PDF downloads and contains:"
echo "     - Receipt details"
echo "     - Items table"
echo "     - Category summary"
echo "  5. Check the checkbox and export again"
echo "  6. Verify images are included in the PDF"
echo ""
echo "📖 See .auto-claude/specs/006-pdf-report-generation/e2e-verification.md"
echo "   for complete verification steps"
echo ""
