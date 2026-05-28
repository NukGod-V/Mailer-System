import os
import time
import requests
import uuid
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
    
    # 2. Fire the payload (Patched URL)
    api_url = "http://localhost:5000/api/send_email" 
    
    # Patched Payload (Added Auth + List formatting for 'to')
    payload = {
        "from_role": "admin",
        "token": "pipeline-test-token-123", # Use the CI seeded token
        "to": [recipient], 
        "subject": "E2E Automated Pipeline Test",
        "body": "<p>If you can read this, the pipeline is intact.</p>"
    }

    # Patched Payload (Added Auth + List formatting for 'to')
    
    response = requests.post(api_url, json=payload)
    
    # Enhanced assertion to print exact Flask validation errors if it fails
    assert response.status_code in [200, 202], f"API failed with {response.status_code}: {response.text}"
    
    # 3. Wait for it to hit the Testmail server
    delivered_email = wait_for_testmail(tag=test_tag)
    
    # 4. Assert the payload integrity
    assert delivered_email['subject'] == "E2E Automated Pipeline Test"
    assert "<p>If you can read this, the pipeline is intact.</p>" in delivered_email['html']