"""
LLM Client with timeout, retry, and circuit breaker logic.
Supports Azure OpenAI and open-source models via abstraction layer.
"""

import time
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.config import Settings


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False
    
    def call(self) -> bool:
        """Check if circuit is open (True = OPEN, don't call LLM)."""
        if not self.is_open:
            return False
        
        # Reset after timeout
        if self.last_failure_time and \
           datetime.now() > self.last_failure_time + timedelta(seconds=self.timeout_seconds):
            self.is_open = False
            self.failure_count = 0
            return False
        
        return True
    
    def record_failure(self) -> None:
        """Record a failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
    
    def record_success(self) -> None:
        """Reset on success."""
        self.failure_count = 0
        self.is_open = False


class LLMClient:
    """
    Abstracted LLM client for routing calls to Azure OpenAI, open-source models, etc.
    Includes retry logic, timeouts, and cost controls.
    """
    
    def __init__(self, settings: Settings, logger: logging.Logger):
        self.settings = settings
        self.logger = logger
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        # Mock mode for testing (stubbed)
        self.mock_mode = not settings.api_key or settings.api_key == "mock"
    
    def call_llm(self, prompt: str, system_prompt: str, request_id: str) -> Dict[str, Any]:
        """
        Call the LLM with retries and timeout handling.
        
        Args:
            prompt: User input (ticket text)
            system_prompt: System instructions
            request_id: Correlation ID
        
        Returns:
            {
                "success": bool,
                "response": str or None,
                "tokens_estimate": int,
                "latency_ms": int,
                "error": str or None
            }
        """
        
        # Check circuit breaker
        if self.circuit_breaker.call():
            self.logger.warning(f"[{request_id}] Circuit breaker OPEN, LLM unavailable")
            return {
                "success": False,
                "response": None,
                "tokens_estimate": 0,
                "latency_ms": 0,
                "error": "LLM service unavailable (circuit open)"
            }
        
        # Mock mode for development/testing
        if self.mock_mode:
            return self._mock_llm_call(prompt, request_id)
        
        # Real LLM call with retry
        for attempt in range(self.settings.max_retries + 1):
            start_time = time.time()
            try:
                result = self._call_with_timeout(prompt, system_prompt, request_id)
                latency_ms = int((time.time() - start_time) * 1000)
                
                self.circuit_breaker.record_success()
                
                self.logger.info(
                    f"[{request_id}] LLM call succeeded",
                    extra={"latency_ms": latency_ms, "attempt": attempt + 1}
                )
                
                return {
                    "success": True,
                    "response": result,
                    "tokens_estimate": self._estimate_tokens(prompt, result),
                    "latency_ms": latency_ms,
                    "error": None
                }
            
            except TimeoutError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                self.logger.warning(
                    f"[{request_id}] LLM timeout on attempt {attempt + 1}/{self.settings.max_retries + 1}",
                    extra={"latency_ms": latency_ms}
                )
                
                if attempt < self.settings.max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    self.logger.info(f"[{request_id}] Retrying after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.circuit_breaker.record_failure()
                    return {
                        "success": False,
                        "response": None,
                        "tokens_estimate": 0,
                        "latency_ms": latency_ms,
                        "error": f"LLM timeout after {self.settings.max_retries + 1} attempts"
                    }
            
            except Exception as e:
                self.circuit_breaker.record_failure()
                self.logger.error(
                    f"[{request_id}] LLM call failed: {str(e)}",
                    extra={"attempt": attempt + 1}
                )
                return {
                    "success": False,
                    "response": None,
                    "tokens_estimate": 0,
                    "latency_ms": 0,
                    "error": str(e)
                }
        
        return {
            "success": False,
            "response": None,
            "tokens_estimate": 0,
            "latency_ms": 0,
            "error": "Unknown error"
        }
    
    def _call_with_timeout(self, prompt: str, system_prompt: str, request_id: str) -> str:
        """Call LLM with timeout enforcement (stub)."""
        # In production, use requests library with timeout parameter
        # import requests
        # response = requests.post(
        #     self.settings.llm_endpoint,
        #     json={"messages": [{"role": "system", "content": system_prompt},
        #                        {"role": "user", "content": prompt}]},
        #     headers={"Authorization": f"Bearer {self.settings.api_key}"},
        #     timeout=self.settings.timeout_seconds
        # )
        # return response.json()["choices"][0]["message"]["content"]
        
        # Stub: simulate LLM response
        raise NotImplementedError("Real LLM integration requires API key and endpoint")
    
    def _mock_llm_call(self, prompt: str, request_id: str) -> Dict[str, Any]:
        """Mock LLM call for testing."""
        # Simulate processing
        time.sleep(0.1)
        
        mock_response = {
            "summary": "Customer requests billing help for recent charges.",
            "category": "Billing",
            "priority": "Medium",
            "queue": "Billing Ops",
            "confidence": 0.92,
            "needs_human_review": False
        }
        
        return {
            "success": True,
            "response": json.dumps(mock_response),
            "tokens_estimate": len(prompt.split()) + 50,
            "latency_ms": 100,
            "error": None
        }
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """Rough token count estimate (4 chars ≈ 1 token)."""
        return (len(prompt) + len(response)) // 4
