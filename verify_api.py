
import requests
import os

# Create dummy files for upload
with open("test_file_1.txt", "w") as f:
    f.write("This is test data 1")
with open("test_file_2.txt", "w") as f:
    f.write("This is test data 2")

url = "http://127.0.0.1:8000/api/transfer/"

files = {
    'data_1': open('test_file_1.txt', 'rb'),
    'data_2': open('test_file_2.txt', 'rb')
}

data = {
    'from_corporate_id': 'CORP1',
    'from_client_id': 'CLIENT1',
    'to_corporate_id': 'CORP2',
    'to_client_id': 'CLIENT2',
    'type': 'DATA_SYNC'
}

print("Testing POST request...")
try:
    response = requests.post(url, data=data, files=files)
    print(f"POST Status Code: {response.status_code}")
    print(f"POST Response: {response.json()}")
except Exception as e:
    print(f"POST Failed: {e}")

print("\nTesting GET request...")
try:
    response = requests.get(url)
    print(f"GET Status Code: {response.status_code}")
    print(f"GET Response: {response.json()}")
except Exception as e:
    print(f"GET Failed: {e}")

# Cleanup
# os.remove("test_file_1.txt")
# os.remove("test_file_2.txt")
