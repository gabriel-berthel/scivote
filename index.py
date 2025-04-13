import requests
import xml.etree.ElementTree as ET
import time

search_query = 'cs'
max_results = 125
base_url = "http://export.arxiv.org/api/query?{}"
query_url = base_url.format(f"search_query={search_query}&start=0&max_results={max_results}")

response = requests.get(query_url)

if response.status_code == 200:
    try:
        root = ET.fromstring(response.content)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        
        for entry in entries:
            arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1]
            add_url = f"http://localhost:8000/api/add/{arxiv_id}"
            post_response = requests.get(add_url)
            
            print(f"POST Request to: {add_url}")
            print(f"Response Status Code: {post_response.status_code}")
            print(f"Response Content: {post_response.text}")
            
            if post_response.status_code == 200:
                print(f"Successfully added article with arXiv ID: {arxiv_id}")
            else:
                print(f"Failed to add article with arXiv ID: {arxiv_id}")
            
            time.sleep(1)
    except Exception as e:
        print(f"Error parsing the response: {e}")
else:
    print(f"Failed to fetch data. HTTP Status code: {response.status_code}")
