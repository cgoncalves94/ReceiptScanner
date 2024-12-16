#!/bin/bash

# Base URLs for the API
API_URL="http://localhost:8000/api/v1"
CATEGORIES_URL="$API_URL/categories"
RECEIPTS_URL="$API_URL/receipts"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to make API calls and format the response
call_api() {
    local url=$1
    local method=${2:-GET}
    local data=$3
    local content_type=${4:-"application/json"}

    echo -e "\n${GREEN}Testing $method $url${NC}"
    echo "----------------------------------------"

    if [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        curl -X "$method" "$url" \
            -H "accept: application/json" \
            -H "Content-Type: $content_type" \
            -d "$data" | json_pp
    else
        curl -X "$method" "$url" \
            -H "accept: application/json" | json_pp
    fi

    echo "----------------------------------------"
}

echo -e "${BLUE}Testing Category APIs${NC}"

# 1. Create a new category
echo -e "\n${GREEN}1. Creating a new category${NC}"
NEW_CATEGORY='{
    "name": "Groceries",
    "description": "Food and household items"
}'
call_api "$CATEGORIES_URL/" "POST" "$NEW_CATEGORY"

# 2. Create another category
echo -e "\n${GREEN}2. Creating another category${NC}"
NEW_CATEGORY='{
    "name": "Electronics",
    "description": "Electronic devices and accessories"
}'
call_api "$CATEGORIES_URL/" "POST" "$NEW_CATEGORY"

# 3. List all categories
echo -e "\n${GREEN}3. Listing all categories${NC}"
call_api "$CATEGORIES_URL/"

# 4. Get a specific category (replace 1 with an actual ID)
echo -e "\n${GREEN}4. Getting category by ID${NC}"
call_api "$CATEGORIES_URL/1"

# 5. Update a category (replace 1 with an actual ID)
echo -e "\n${GREEN}5. Updating a category${NC}"
UPDATE_CATEGORY='{
    "name": "Groceries & Food",
    "description": "Food, beverages, and household items"
}'
call_api "$CATEGORIES_URL/1" "PUT" "$UPDATE_CATEGORY"

# 6. List categories with pagination
echo -e "\n${GREEN}6. Listing categories with pagination${NC}"
call_api "$CATEGORIES_URL/?skip=0&limit=5"

# 7. Delete a category (replace 2 with an actual ID)
echo -e "\n${GREEN}7. Deleting a category${NC}"
call_api "$CATEGORIES_URL/2" "DELETE"

# 8. Verify deletion by listing all categories again
echo -e "\n${GREEN}8. Verifying deletion - listing all categories${NC}"
call_api "$CATEGORIES_URL/"

echo -e "\n${BLUE}Testing Receipt APIs${NC}"

# Test receipt endpoints
echo -e "\n${GREEN}1. Listing all receipts${NC}"
call_api "$RECEIPTS_URL/"

echo -e "\n${GREEN}2. Listing receipts with items${NC}"
call_api "$RECEIPTS_URL/full/"

# Example of how to scan a receipt (commented out)
echo -e "\n${GREEN}How to scan a receipt:${NC}"
echo 'curl -X POST "$RECEIPTS_URL/scan/" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@path/to/receipt.jpg"'
