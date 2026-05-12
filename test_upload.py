#!/usr/bin/env python3
"""
Test script for multiple file upload functionality
Usage: python test_upload.py
"""

import requests
import os
import sys

def test_single_upload():
    """Test single file upload"""
    url = "http://localhost:8000/documents/upload"

    # Try to find a PDF or Excel file in the uploads directory
    test_files = []
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            if filename.endswith(('.pdf', '.xlsx')):
                test_files.append(os.path.join("uploads", filename))

    if not test_files:
        print("❌ No test files found in uploads/ directory")
        return False

    test_file = test_files[0]
    print(f"Testing single upload with: {test_file}")

    with open(test_file, 'rb') as f:
        files = {'file': (os.path.basename(test_file), f, 'application/pdf')}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                print("✅ Single upload successful")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ Single upload failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during single upload: {e}")
            return False

def test_multiple_upload():
    """Test multiple files upload"""
    url = "http://localhost:8000/documents/upload-multiple"

    # Try to find PDF or Excel files in the uploads directory
    test_files = []
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            if filename.endswith(('.pdf', '.xlsx')):
                test_files.append(os.path.join("uploads", filename))

    if len(test_files) < 2:
        print(f"❌ Need at least 2 test files, found {len(test_files)}")
        return False

    print(f"Testing multiple upload with {len(test_files)} files")

    files = []
    for i, file_path in enumerate(test_files):
        f = open(file_path, 'rb')
        # Use tuple format: (field_name, (filename, file_object, content_type))
        files.append((f"files", (os.path.basename(file_path), f, 'application/pdf')))

    try:
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print("✅ Multiple upload successful")
            result = response.json()
            print(f"Uploaded: {result.get('uploaded_count', 0)} files")
            print(f"Skipped: {result.get('skipped_count', 0)} files")
            return True
        else:
            print(f"❌ Multiple upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during multiple upload: {e}")
        return False
    finally:
        # Close all opened files
        for _, (_, f, _) in files:
            f.close()

def test_extract_with_description_length():
    """Test extraction with different description lengths"""

    print("\n=== Testing description length options ===")

    # First upload a file
    upload_url = "http://localhost:8000/documents/upload"
    test_files = []
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            if filename.endswith(('.pdf', '.xlsx')):
                test_files.append(os.path.join("uploads", filename))

    if not test_files:
        print("❌ No test files found")
        return False

    # Upload a test file
    with open(test_files[0], 'rb') as f:
        files = {'file': (os.path.basename(test_files[0]), f, 'application/pdf')}
        try:
            response = requests.post(upload_url, files=files)
            if response.status_code != 200:
                print("❌ Upload failed")
                return False

            doc_id = response.json()['document']['id']
            print(f"✅ Uploaded document ID: {doc_id}")
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            return False

    # Test different description lengths
    lengths = ['short', 'medium', 'long']
    for length in lengths:
        print(f"\n--- Testing {length} description ---")
        extract_url = f"http://localhost:8000/documents/{doc_id}/extract"
        try:
            response = requests.post(extract_url, params={'description_length': length})
            if response.status_code == 200:
                spec = response.json()['specification']
                desc_fr = spec.get('description_fr', '')
                desc_en = spec.get('description_en', '')

                print(f"✅ {length} extraction successful")
                print(f"   FR length: {len(desc_fr)} chars")
                print(f"   EN length: {len(desc_en)} chars")

                # Show preview
                if desc_fr:
                    preview = desc_fr[:100] + "..." if len(desc_fr) > 100 else desc_fr
                    print(f"   FR preview: {preview}")
            else:
                print(f"❌ {length} extraction failed: {response.status_code}")
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error during {length} extraction: {e}")

    return True

def main():
    print("=== Testing Gomedia API ===")
    print("Make sure the server is running: uvicorn app.main:app --reload")

    # Test endpoints
    try:
        health = requests.get("http://localhost:8000/")
        if health.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API not responding")
            return
    except:
        print("❌ Cannot connect to API. Make sure server is running with: uvicorn app.main:app --reload")
        return

    # Run tests
    print("\n--- Test 1: Single File Upload ---")
    test_single_upload()

    print("\n--- Test 2: Multiple Files Upload ---")
    test_multiple_upload()

    print("\n--- Test 3: Description Length Options ---")
    test_extract_with_description_length()

    print("\n=== All tests completed ===")

if __name__ == "__main__":
    main()