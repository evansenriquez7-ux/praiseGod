import os
import sys
from google import genai

def main():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment. The script will try to rely on application default credentials or other env vars.")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        sys.exit(1)

    print("=== Testing Gemini API ===")
    
    try:
        # We can simulate a back and forth using a simple loop or just generate_content with multiple messages
        # Let's try the chat abstraction
        chat = client.chats.create(model="gemma-4-31b-it")
        
        user_messages = [
            "Hello! I am having trouble with a math problem.",
            "Can you explain how to add 1/2 and 1/3?",
            "What if I multiply them instead?"
        ]
        
        import time
        for msg in user_messages:
            print(f"\nUser: {msg}")
            
            # Retry logic for 503 errors
            for attempt in range(5):
                try:
                    response = chat.send_message(msg)
                    print(f"Gemini: {response.text}")
                    break
                except Exception as api_err:
                    if "503" in str(api_err) or "429" in str(api_err):
                        print(f"Encountered {api_err}. Retrying in {2**attempt}s...")
                        time.sleep(2**attempt)
                    else:
                        raise api_err
            
    except Exception as e:
        print(f"Error during API call: {e}")

if __name__ == "__main__":
    main()
