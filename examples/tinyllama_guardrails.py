"""
Hexarch Guardrails + TinyLlama Integration
Protects API calls to your TinyLlama model with policy-driven guardrails
"""
import os
import requests
from dotenv import load_dotenv, find_dotenv
from hexarch_guardrails import Guardian, PolicyViolation
from typing import Optional, Dict, Any

# Load environment variables (.env.local preferred)
load_dotenv(find_dotenv(".env.local"))
load_dotenv(find_dotenv())

# Initialize Guardian with TinyLlama policies
guardian = Guardian()

# TinyLlama API endpoints
TINYLLAMA_INTERNAL = "http://localhost:8000"
TINYLLAMA_EXTERNAL = "http://api.codexscrolls.io"


class TinyLlamaGuarded:
    """Wrapper for TinyLlama API with Hexarch Guardrails protection"""
    
    def __init__(self, api_url: str = TINYLLAMA_EXTERNAL, enforce: bool = True):
        self.api_url = api_url
        self.enforce = enforce
        self.guardian = Guardian()
    
    @staticmethod
    def _check_policy(policy_id: str):
        """Decorator for policy protection"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                decision = guardian.evaluate_policy(
                    policy_id,
                    {"function": func.__name__, "params": kwargs}
                )
                
                if not decision.get("allowed", True):
                    raise PolicyViolation(f"Policy '{policy_id}' denied: {decision.get('reason')}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def health_check(self) -> Dict[str, Any]:
        """Check TinyLlama API health"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Health check failed: {e}")
    
    @_check_policy("rate_limit")
    def chat(
        self,
        message: str,
        model: str = "tinyllama",
        temperature: float = 0.7,
        num_predict: int = 128,
        system: Optional[str] = None
    ) -> str:
        """
        Call TinyLlama chat endpoint with rate limiting protection
        
        Args:
            message: Question/prompt for the model
            model: Model name (default: tinyllama)
            temperature: Creativity level (0-1)
            num_predict: Max tokens to generate
            system: System prompt (optional)
        
        Returns:
            Model's response text
        
        Raises:
            PolicyViolation: If policy denies the request
        """
        payload = {
            "message": message,
            "model": model,
            "temperature": temperature,
            "num_predict": num_predict,
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Chat request failed: {e}")
    
    @_check_policy("rate_limit")
    def chat_with_voice(
        self,
        message: str,
        model: str = "tinyllama",
        temperature: float = 0.7,
        num_predict: int = 128,
        voice: bool = True,
        output_file: Optional[str] = None
    ) -> str:
        """
        Call TinyLlama chat-with-voice endpoint with rate limiting
        
        Args:
            message: Question/prompt
            model: Model name
            temperature: Creativity level
            num_predict: Max tokens
            voice: Enable voice (always True for this endpoint)
            output_file: Optional file to save MP3 response
        
        Returns:
            Path to MP3 file or response text
        """
        payload = {
            "message": message,
            "model": model,
            "temperature": temperature,
            "num_predict": num_predict,
            "voice": voice
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/chat-with-voice",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # If requesting voice, save MP3
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                return output_file
            
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"Voice request failed: {e}")
    
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(
                f"{self.api_url}/api/models",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list models: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            response = requests.get(
                f"{self.api_url}/api/stats",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get stats: {e}")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("🛡️  TinyLlama + Hexarch Guardrails Integration")
    print("=" * 60)
    print()
    
    # Initialize protected client
    llama = TinyLlamaGuarded(api_url=TINYLLAMA_EXTERNAL)
    
    # Example 1: Basic health check
    print("✓ Example 1: Health Check")
    try:
        health = llama.health_check()
        print(f"  API Status: OK")
        print(f"  Response: {health}")
    except Exception as e:
        print(f"  Status: {e}")
    print()
    
    # Example 2: Protected chat call
    print("✓ Example 2: Protected Chat Call")
    try:
        response = llama.chat(
            message="What is machine learning in one sentence?",
            temperature=0.5
        )
        print(f"  Question: What is machine learning?")
        print(f"  Response: {response[:100]}...")
    except PolicyViolation as e:
        print(f"  ❌ Policy blocked: {e}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Example 3: System prompt
    print("✓ Example 3: With System Prompt")
    try:
        response = llama.chat(
            message="Explain Python",
            system="You are a programming expert. Keep answers concise.",
            temperature=0.7,
            num_predict=64
        )
        print(f"  Question: Explain Python")
        print(f"  Response: {response[:100]}...")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Example 4: Voice response
    print("✓ Example 4: Voice Response")
    try:
        output_file = llama.chat_with_voice(
            message="Hello world",
            output_file="response.mp3"
        )
        print(f"  Question: Hello world")
        print(f"  Voice saved to: {output_file}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Example 5: Get stats
    print("✓ Example 5: API Statistics")
    try:
        stats = llama.get_stats()
        print(f"  Stats: {stats}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    print("=" * 60)
    print("✨ Integration Demo Complete")
