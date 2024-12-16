#!/bin/bash

# Base URL for the API
API_URL="http://localhost:8000/api/v1/receipts"

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Receipt Scanner API Endpoints${NC}\n"

# Function to make API calls and format the response
call_api() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3

    echo -e "\n${GREEN}Testing $method $endpoint${NC}"
    echo "----------------------------------------"

    if [ "$method" = "POST" ] && [ ! -z "$data" ]; then
        curl -X "$method" "$API_URL$endpoint" \
            -H "accept: application/json" \
            -H "Content-Type: multipart/form-data" \
            -F "$data" | json_pp
    else
        curl -X "$method" "$API_URL$endpoint" | json_pp
    fi

    echo "----------------------------------------"
}

# 1. List Categories
echo -e "\n${GREEN}1. Testing Category Endpoints${NC}"
call_api "/categories/"
call_api "/categories/?skip=0&limit=5"

# 2. List Receipts (Basic)
echo -e "\n${GREEN}2. Testing Receipt List Endpoints${NC}"
call_api "/"
call_api "/?skip=0&limit=5"

# 3. List Receipts with Items
echo -e "\n${GREEN}3. Testing Receipt List with Items Endpoints${NC}"
call_api "/full/"
call_api "/full/?skip=0&limit=5"

# 4. Get Single Receipt (replace 1 with an existing receipt ID)
echo -e "\n${GREEN}4. Testing Single Receipt Endpoint${NC}"
call_api "/1"

# 5. Scan Receipt
echo -e "\n${GREEN}5. Testing Receipt Scan Endpoint${NC}"
echo "To test receipt scanning, uncomment the line below and replace the path with your receipt image:"
# UNCOMMENT AND MODIFY THE LINE BELOW TO TEST RECEIPT SCANNING
call_api "/scan/" POST "file=@uploads/receipt1.jpg"

# Additional examples of how to test receipt scanning:
echo -e "\n${GREEN}Other ways to test receipt scanning:${NC}"
echo "1. Using curl directly:"
echo "curl -X POST http://localhost:8000/api/v1/receipts/scan/ -H 'accept: application/json' -H 'Content-Type: multipart/form-data' -F 'file=@uploads/receipt1.jpg'"
