#!/usr/bin/env python3
"""
Quick test to verify OpenRouter API connection
Run this first to check if your API key and models are working
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_api_key():
    """Check if API key is set"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env file")
        print("\n📝 Create a .env file with:")
        print("   OPENROUTER_API_KEY=your_key_here")
        print("\n🔑 Get a free key at: https://openrouter.ai/keys")
        return False
    
    if not api_key.startswith("sk-or-"):
        print("⚠️  Warning: API key doesn't look right")
        print(f"   Should start with 'sk-or-' but got: {api_key[:10]}...")
        return False
    
    print(f"✅ API key found: {api_key[:15]}...")
    return True

def test_models():
    """Test each model in the FREE_MODELS list"""
    import requests
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-2.5-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
    ]
    
    print("\n🧪 Testing models...\n")
    
    working_models = []
    
    for model in models:
        short_name = model.split("/")[-1]
        print(f"Testing {short_name}...", end=" ")
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Working")
                working_models.append(model)
            elif response.status_code == 404:
                print("❌ 404 (model not available)")
            elif response.status_code == 401:
                print("❌ 401 (invalid API key)")
                return False
            elif response.status_code == 429:
                print("⚠️  429 (rate limited, but key is valid)")
                working_models.append(model)
            else:
                print(f"❌ {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if not working_models:
        print("\n❌ No models are working!")
        print("\n💡 Possible solutions:")
        print("   1. Check your API key is valid")
        print("   2. Visit https://openrouter.ai/models?max_price=0 to see current free models")
        print("   3. Update FREE_MODELS list in utils/llm_client.py")
        return False
    
    print(f"\n✅ {len(working_models)} model(s) working:")
    for model in working_models:
        print(f"   - {model}")
    
    return True

def test_full_request():
    """Test a complete LLM request"""
    print("\n🚀 Testing full LLM request...")
    
    try:
        from utils.llm_client import call_llm
        
        response = call_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'API test successful' and nothing else.",
            max_retries=1
        )
        
        print(f"✅ Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("  OpenRouter API Test")
    print("=" * 60)
    
    # Test 1: API Key
    if not test_api_key():
        sys.exit(1)
    
    # Test 2: Models
    if not test_models():
        sys.exit(1)
    
    # Test 3: Full request
    if not test_full_request():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Your setup is ready.")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Run: python main.py --url https://arxiv.org/pdf/1706.03762.pdf")
    print("   2. Or run Flask app: python app.py")
    print("   3. Or see DEPLOYMENT.md for hosting options")

if __name__ == "__main__":
    main()
