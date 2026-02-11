"""
Groq LLM Client
Simple wrapper for Groq API
"""

import os
from typing import Optional


class LLMClient:
    """
    Groq LLM client for career agent system
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY environment variable)
            model: Model name (default: llama-3.3-70b-versatile)
            
        Where to get API key:
            1. Go to: https://console.groq.com/keys
            2. Sign up/Login
            3. Create new API key
            4. Copy and paste here OR set as environment variable
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Groq API key not found!\n"
                "Please either:\n"
                "1. Pass api_key when creating LLMClient: LLMClient(api_key='your_key')\n"
                "2. Set environment variable: export GROQ_API_KEY='your_key'\n"
                "\n"
                "Get your API key at: https://console.groq.com/keys"
            )
        
        self.model = model
        
        # Initialize Groq client
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Groq library not installed!\n"
                "Install it with: pip install groq"
            )
    
    def generate(self, 
                prompt: str,
                max_tokens: int = 1000,
                temperature: float = 0.7) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            
        Returns:
            Generated text
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI career advisor assistant. Always output valid JSON when requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("="*60)
    print("GROQ LLM CLIENT TEST")
    print("="*60)
    
    # Test 1: Check if API key is set
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n❌ GROQ_API_KEY not found!")
        print("\n📝 To set your API key:")
        print("   Linux/Mac: export GROQ_API_KEY='your_key_here'")
        print("   Windows: set GROQ_API_KEY=your_key_here")
        print("\n🔑 Get your API key at: https://console.groq.com/keys")
        exit(1)
    
    print("\n✅ API key found!")
    
    # Test 2: Initialize client
    try:
        client = LLMClient()
        print("✅ Client initialized successfully!")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        exit(1)
    
    # Test 3: Generate response
    test_prompt = '''List 3 skills needed for a Data Analyst role.
Output ONLY this JSON format:
{
  "skills": ["skill1", "skill2", "skill3"]
}'''
    
    try:
        print("\n📤 Sending test prompt...")
        response = client.generate(test_prompt, max_tokens=200)
        print("\n✅ Response received:")
        print(response)
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        exit(1)