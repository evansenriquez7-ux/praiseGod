#!/bin/bash

# Download NYSED ELA released items for Grades 4-8, years 2022-2025
# Base URL pattern: https://www.nysedregents.org/ei/{year}/{year}-released-items-ela-g{grade}.pdf

BASE_DIR="data/raw/nysed/ela"
YEARS=(2022 2023 2024 2025)
GRADES=(4 5 6 7 8)

for YEAR in "${YEARS[@]}"; do
    for GRADE in "${GRADES[@]}"; do
        URL="https://www.nysedregents.org/ei/${YEAR}/${YEAR}-released-items-ela-g${GRADE}.pdf"
        OUTPUT_DIR="${BASE_DIR}/${YEAR}"
        OUTPUT_FILE="${OUTPUT_DIR}/${YEAR}-released-items-ela-g${GRADE}.pdf"
        
        # Create directory if it doesn't exist
        mkdir -p "${OUTPUT_DIR}"
        
        # Skip if file already exists
        if [ -f "${OUTPUT_FILE}" ]; then
            echo "EXISTS: ${OUTPUT_FILE}"
            continue
        fi
        
        # Download
        echo "Downloading: ${URL}"
        curl -L -o "${OUTPUT_FILE}" "${URL}" 2>&1 | grep -E '(Downloaded|Error|Failed)'
        
        # Check if download was successful
        if [ -f "${OUTPUT_FILE}" ] && [ -s "${OUTPUT_FILE}" ]; then
            echo "SUCCESS: ${OUTPUT_FILE}"
        else
            echo "FAILED: ${URL}"
            rm -f "${OUTPUT_FILE}"
        fi
        
        # Small delay to avoid rate limiting
        sleep 1
    done
done

echo ""
echo "Download complete. Summary:"
find "${BASE_DIR}" -name "*-released-items-ela-g*.pdf" | wc -l | xargs echo "Total PDFs:"
