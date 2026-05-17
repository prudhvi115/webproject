import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry
import time

# Disable insecure request warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_robust_session():
    """
    Creates a requests session with robust retry logic and timeouts.
    Handles SSLEOFError and other connection issues gracefully.
    """
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # Total retries
        backoff_factor=1,  # Wait 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def make_gemini_request(url, payload, headers, timeout=45):
    """
    Wrapper to make a request to Gemini API with robust error handling.
    """
    session = get_robust_session()
    
    try:
        # Standard request with verify=True (default) but using our robust session
        response = session.post(url, json=payload, headers=headers, timeout=timeout)
        return response
    except requests.exceptions.SSLError as e:
        print(f"SSL Error encountered: {e}. Retrying without verification (fallback)...")
        # Extreme fallback for local dev environments with proxy issues
        try:
             response = session.post(url, json=payload, headers=headers, timeout=timeout, verify=False)
             return response
        except Exception as e2:
            raise e2
    except Exception as e:
        raise e
