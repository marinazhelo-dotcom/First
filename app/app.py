import httpx
from typing import Dict, Any

def fetch_developer_data():
    url = "https://api.github.com/users/github"
    
    try:
        # Think of this like a Guzzle HTTP GET request
        response = httpx.get(url)
        print(type(response))
        response.raise_for_status() # Throws an exception if status >= 400
        
        # In PHP, this would be json_decode($response->getBody(), true);
        data = response.json()
        items = data.items()
        for key, item in items:
            print(key, item)
            print("--------------------------------")
        
        print(f"Company Name: {data.get('name')}")
        print(f"Location: {data.get('location')}")
        
    except httpx.HTTPStatusError as e:
        print(f"API Error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# This boilerplate mimics PHP's entry point execution, 
# ensuring the script only runs if executed directly (not imported elsewhere)
if __name__ == "__main__":
    fetch_developer_data()
