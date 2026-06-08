import os
import time
import requests
import uuid
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def wait_for_testmail(tag: str, timeout: int = 60, interval: int = 5) -> dict:
    """
    Polls Testmail.app for an email matching the tag.
    """
    api_key = os.getenv("TESTMAIL_API_KEY")
    namespace = os.getenv("TESTMAIL_NAMESPACE")
    
    url = f"https://api.testmail.app/api/json?apikey={api_key}&namespace={namespace}&tag={tag}"
    
    start_time = time.time()
    print(f"\nPolling Testmail.app for tag: {tag}...")
    
    while (time.time() - start_time) < timeout:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') == 'success' and data.get('count', 0) > 0:
            print("✅ Email received!")
            return data['emails'][0]
            
        time.sleep(interval)
        
    raise TimeoutError(f"Email with tag '{tag}' did not arrive within {timeout} seconds.")


def test_end_to_end_delivery():
    # 1. Generate a unique tag to avoid clashing with older test runs
    test_tag = f"e2e-{uuid.uuid4().hex[:8]}"
    namespace = os.getenv("TESTMAIL_NAMESPACE")
    recipient = f"{namespace}.{test_tag}@inbox.testmail.app"
    
    # 2. Fire the payload
    api_url = "http://localhost:5000/api/send_email" 
    
    payload = {
        "from_role": "admin",
        "token": "pipeline-test-token-123", # Use the CI seeded token
        "to": [recipient], 
        "subject": "E2E Automated Pipeline Test",
        "body": "<p>If you can read this, the pipeline is intact.</p>"
    }
    
    print("\n🚀 Firing email through Flask API...")
    response = requests.post(api_url, json=payload)
    assert response.status_code in [200, 202], f"API failed with {response.status_code}: {response.text}"
    
    # 3. Wait for it to hit the Testmail server
    delivered_email = wait_for_testmail(tag=test_tag)
    
    # 4. Assert the payload integrity
    assert delivered_email['subject'] == "E2E Automated Pipeline Test"
    
    html_content = delivered_email['html']
    assert "<p>If you can read this, the pipeline is intact.</p>" in html_content
    
    # ---------------------------------------------------------
    # NEW: PHASE 5 - PIXEL INGESTION SIMULATION
    # ---------------------------------------------------------
    
    print("\n🔍 Scanning HTML for tracking pixel...")
    
    # Regex to find the dynamically generated image source URL
    # It looks for src=".../api/track/ANYTHING.png"
    pixel_match = re.search(r'src=["\'](.*?/api/track/[^"\']+\.png)["\']', html_content)
    
    assert pixel_match is not None, "❌ Tracking pixel was NOT injected into the email HTML!"
    
    pixel_url = pixel_match.group(1)
    print(f"🔗 Extracted Pixel URL: {pixel_url}")
    
    # 6. Simulate a user opening the email
    print("👁️ Simulating user 'Open' event by hitting the pixel...")
    pixel_response = requests.get(pixel_url)
    
    # 7. Assert the pixel endpoint worked perfectly
    assert pixel_response.status_code == 200, f"❌ Pixel hit failed! Expected 200 OK but got {pixel_response.status_code}"
    
    # Ensure the Flask app actually returned an invisible image, not a JSON error
    content_type = pixel_response.headers.get("Content-Type", "")
    assert "image" in content_type, f"❌ Pixel endpoint returned non-image Content-Type: {content_type}"
    
    print("✅ Pixel ingestion test passed! The open event was successfully processed by the server.")