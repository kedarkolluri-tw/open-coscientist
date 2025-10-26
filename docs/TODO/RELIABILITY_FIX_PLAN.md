# Reliability Fix: Concrete Implementation Plan

**Goal**: Fix critical reliability issues preventing successful report generation (currently 0% success rate)

**Timeline**: 2 weeks (Phase 1 Critical Fixes only)

---

## Current State Analysis

### ✅ **What EXISTS**:
- **Basic retry logic** in `robust_parsing.py` (max 3 retries for parsing only)
- **Token limit handling** with LLM-based compaction
- **Catastrophic validation** in `common.py` (crashes on empty responses)

### ❌ **What's MISSING**:
- No retry logic for **LLM API calls** (timeouts, rate limits, network failures)
- No timeout management for **long-running operations**
- No circuit breakers to prevent cascading failures
- No graceful degradation when agents fail
- No alternative fallback providers when primary LLM is down

---

## Phase 1: Critical Fixes (Week 1-2)

### **Sprint 1: Retry & Timeout Infrastructure** (Days 1-3)

#### Task 1.1: Create `coscientist/resilience.py` (New Module)

**File to create**: `coscientist/resilience.py`

```python
"""
Resilience utilities: retry logic, timeouts, circuit breakers.
"""
import logging
import time
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class ResilienceConfig:
    """Configuration for resilience features."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_backoff: float = 1.0,
        max_backoff: float = 60.0,
        timeout: float = 30.0,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout: float = 300.0
    ):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.timeout = timeout
        self.circuit_breaker_failure_threshold = circuit_breaker_failure_threshold
        self.circuit_breaker_recovery_timeout = circuit_breaker_recovery_timeout


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 300.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker logic."""
        if self.state == "open":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise CircuitBreakerOpen("Circuit breaker is OPEN")
            else:
                self.state = "half_open"
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None


def retry_with_backoff(
    max_retries: int = 3,
    base_backoff: float = 1.0,
    max_backoff: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry logic with exponential backoff.
    
    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts
    base_backoff : float
        Base backoff time in seconds
    max_backoff : float
        Maximum backoff time in seconds
    exceptions : tuple
        Exception types to catch and retry
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        backoff = min(
                            base_backoff * (2 ** attempt),
                            max_backoff
                        )
                        logger.warning(
                            f"[{func.__name__}] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {backoff}s..."
                        )
                        time.sleep(backoff)
                    else:
                        logger.error(
                            f"[{func.__name__}] All {max_retries} attempts failed. "
                            f"Last error: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def with_timeout(timeout: float):
    """
    Decorator for timeout protection.
    
    Parameters
    ----------
    timeout : float
        Timeout in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            class TimeoutError(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
            
            if timeout > 0:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
        
        return wrapper
    return decorator


# Module-level circuit breakers
_llm_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=300.0
)

_embedding_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=180.0
)


def robust_llm_call(llm, messages, config=None, **kwargs):
    """
    Robust LLM call with retry, timeout, and circuit breaker.
    
    Wraps standard LLM invoke() with resilience features.
    """
    if config is None:
        config = ResilienceConfig()
    
    @retry_with_backoff(
        max_retries=config.max_retries,
        base_backoff=config.base_backoff,
        max_backoff=config.max_backoff,
        exceptions=(Exception,)
    )
    @with_timeout(timeout=config.timeout)
    def _call():
        return _llm_circuit_breaker.call(llm.invoke, messages, config, **kwargs)
    
    return _call()
```

**Implementation checklist**:
- [ ] Create file `coscientist/resilience.py`
- [ ] Implement `CircuitBreaker` class
- [ ] Implement `retry_with_backoff` decorator
- [ ] Implement `with_timeout` decorator
- [ ] Implement `robust_llm_call` wrapper
- [ ] Add module-level circuit breakers

---

#### Task 1.2: Integrate Retry Logic into Framework

**Files to modify**:
- `coscientist/framework.py`
- `coscientist/supervisor_agent.py`
- `coscientist/generation_agent.py`
- `coscientist/reflection_agent.py`

**Changes needed**:
1. Wrap all `llm.invoke()` calls with `robust_llm_call()`
2. Add timeout configuration for long operations
3. Add error logging with context

**Example modification** in `framework.py`:

```python
# BEFORE:
response = llm.invoke(prompt)

# AFTER:
from coscientist.resilience import robust_llm_call, ResilienceConfig

config = ResilienceConfig(
    max_retries=3,
    base_backoff=2.0,
    timeout=30.0
)

try:
    response = robust_llm_call(llm, prompt, config)
except Exception as e:
    logger.error(f"LLM call failed after retries: {e}")
    raise
```

**Implementation checklist**:
- [ ] Update `supervisor_agent.py` to use `robust_llm_call`
- [ ] Update `generation_agent.py` to use `robust_llm_call`
- [ ] Update `reflection_agent.py` to use `robust_llm_call`
- [ ] Update all other agent files
- [ ] Add timeout configuration for each operation type
- [ ] Test with simulated failures

---

#### Task 1.3: Add Timeout Management for Operations

**File to create**: `coscientist/timeout_manager.py`

```python
"""
Timeout management for long-running operations.
"""
from typing import Dict, Callable, Any
from contextlib import contextmanager
import signal

class TimeoutManager:
    """Manages timeouts for different operation types."""
    
    OPERATION_TIMEOUTS = {
        'llm_call': 30.0,           # 30 seconds
        'generation': 300.0,         # 5 minutes
        'reflection': 180.0,         # 3 minutes
        'tournament': 600.0,         # 10 minutes
        'meta_review': 300.0,        # 5 minutes
        'literature_review': 900.0,  # 15 minutes
    }
    
    @classmethod
    def execute_with_timeout(
        cls,
        operation: Callable,
        operation_type: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with configured timeout."""
        timeout = cls.OPERATION_TIMEOUTS.get(operation_type, 60.0)
        
        @contextmanager
        def timeout_context():
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation '{operation_type}' timed out after {timeout}s")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            yield
            signal.alarm(0)
        
        try:
            with timeout_context():
                return operation(*args, **kwargs)
        except TimeoutError:
            logger.error(f"Operation {operation_type} timed out after {timeout}s")
            raise
```

**Implementation checklist**:
- [ ] Create file `coscientist/timeout_manager.py`
- [ ] Implement `TimeoutManager` class
- [ ] Integrate into `framework.py` for long operations
- [ ] Test timeout scenarios

---

### **Sprint 2: Graceful Error Recovery** (Days 4-6)

#### Task 2.1: Implement Graceful Error Wrappers

**File to create**: `coscientist/error_recovery.py`

```python
"""
Graceful error recovery and fallback strategies.
"""
import logging
from typing import Callable, Any, Optional, List

logger = logging.getLogger(__name__)


class GracefulAgentWrapper:
    """Wrapper for agents with graceful error recovery."""
    
    def __init__(
        self,
        agent_name: str,
        fallback_strategy: Callable = None,
        continue_on_error: bool = False
    ):
        self.agent_name = agent_name
        self.fallback_strategy = fallback_strategy
        self.continue_on_error = continue_on_error
    
    def execute_with_fallback(self, operation: Callable, *args, **kwargs):
        """Execute with fallback on error."""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"[{self.agent_name}] Error: {e}")
            
            if self.fallback_strategy:
                logger.info(f"[{self.agent_name}] Trying fallback strategy...")
                try:
                    return self.fallback_strategy(*args, **kwargs)
                except Exception as e2:
                    logger.error(f"[{self.agent_name}] Fallback also failed: {e2}")
            
            if not self.continue_on_error:
                raise
            
            logger.warning(f"[{self.agent_name}] Continuing with degraded functionality...")
            return self._handle_partial_failure(*args, **kwargs)
    
    def _handle_partial_failure(self, *args, **kwargs):
        """Handle partial failure with degraded functionality."""
        logger.warning(f"[{self.agent_name}] Executing with degraded functionality")
        # Return minimal valid result to allow system to continue
        return None


class LLMFallbackManager:
    """Manages fallback LLMs when primary LLM fails."""
    
    def __init__(self, primary_llm, fallback_llms: List[Any]):
        self.primary_llm = primary_llm
        self.fallback_llms = fallback_llms
        self.current_fallback_index = 0
    
    def get_llm(self):
        """Get primary LLM, or fallback if primary is failing."""
        return self.primary_llm  # TODO: Implement health check logic
    
    def use_fallback(self):
        """Switch to next fallback LLM."""
        if self.current_fallback_index < len(self.fallback_llms):
            fallback_llm = self.fallback_llms[self.current_fallback_index]
            logger.warning(f"Switching to fallback LLM {self.current_fallback_index}")
            self.current_fallback_index += 1
            return fallback_llm
        else:
            raise RuntimeError("All LLM fallbacks exhausted")
```

**Implementation checklist**:
- [ ] Create file `coscientist/error_recovery.py`
- [ ] Implement `GracefulAgentWrapper` class
- [ ] Implement `LLMFallbackManager` class
- [ ] Wrap critical agents with graceful wrappers
- [ ] Add fallback strategies for each agent type
- [ ] Test recovery scenarios

---

#### Task 2.2: Update Framework to Use Graceful Recovery

**File to modify**: `coscientist/framework.py`

**Changes needed**:
1. Wrap critical operations in graceful error handlers
2. Add partial failure handling
3. Don't crash entire system on single agent failure

**Example modification**:

```python
# In run() method:
try:
    _ = await getattr(self, current_action)()
except Exception as e:
    logger.error(f"Action '{current_action}' failed: {e}")
    
    # DON'T CRASH - Try to continue
    if self.state_manager.total_actions >= 3:
        # If we've made some progress, try to continue
        logger.warning("Continuing with remaining actions...")
    else:
        # If we haven't made progress, this is critical
        raise
```

**Implementation checklist**:
- [ ] Wrap supervisor loop in try-except
- [ ] Handle individual action failures gracefully
- [ ] Continue execution when possible
- [ ] Log errors but don't crash entire system
- [ ] Test partial failure scenarios

---

### **Sprint 3: Testing & Validation** (Days 7-10)

#### Task 3.1: Create Failure Simulation Tests

**File to create**: `tests/test_reliability.py`

```python
"""
Test resilience features: retry logic, timeouts, circuit breakers.
"""
import pytest
from unittest.mock import Mock, patch
from coscientist.resilience import retry_with_backoff, CircuitBreaker


def test_retry_logic():
    """Test retry with exponential backoff."""
    call_count = 0
    
    @retry_with_backoff(max_retries=3, base_backoff=0.1)
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("Simulated failure")
        return "success"
    
    result = failing_function()
    assert result == "success"
    assert call_count == 3


def test_circuit_breaker():
    """Test circuit breaker opens after threshold."""
    breaker = CircuitBreaker(failure_threshold=2)
    call_count = 0
    
    def failing_func():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Always fails")
    
    # First two failures should go through
    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(failing_func)
    
    # Circuit should now be open
    with pytest.raises(CircuitBreakerOpen):
        breaker.call(failing_func)
    
    assert breaker.state == "open"
    assert call_count == 2


def test_timeout_handling():
    """Test timeout management."""
    from coscientist.timeout_manager import TimeoutManager
    
    def long_operation():
        import time
        time.sleep(10)  # Takes 10 seconds
    
    with pytest.raises(TimeoutError):
        TimeoutManager.execute_with_timeout(
            long_operation,
            'llm_call'  # 30 second timeout
        )
```

**Implementation checklist**:
- [ ] Create file `tests/test_reliability.py`
- [ ] Test retry logic with different scenarios
- [ ] Test circuit breaker behavior
- [ ] Test timeout handling
- [ ] Test graceful error recovery
- [ ] Run all tests and fix failures

---

#### Task 3.2: Add Configuration for Resilience

**File to modify**: `coscientist/researcher_config.json`

**Add resilience configuration section**:

```json
{
  "RESILIENCE": {
    "MAX_RETRIES": 3,
    "BASE_BACKOFF": 2.0,
    "MAX_BACKOFF": 60.0,
    "LLM_CALL_TIMEOUT": 30.0,
    "GENERATION_TIMEOUT": 300.0,
    "REFLECTION_TIMEOUT": 180.0,
    "TOURNAMENT_TIMEOUT": 600.0,
    "CIRCUIT_BREAKER_THRESHOLD": 5,
    "CIRCUIT_BREAKER_RECOVERY": 300.0,
    "GRACEFUL_ERROR_HANDLING": true
  }
}
```

**Implementation checklist**:
- [ ] Add resilience config to `researcher_config.json`
- [ ] Update `config_loader.py` to load resilience config
- [ ] Use config values in resilience functions
- [ ] Document configuration options

---

### **Sprint 4: Integration & Testing** (Days 11-14)

#### Task 4.1: End-to-End Reliability Testing

**Test scenarios to implement**:

1. **API Timeout Simulation**
   ```python
   # Simulate API timeout during generation
   # System should retry and recover
   ```

2. **Rate Limit Simulation**
   ```python
   # Simulate rate limit exceeded
   # System should back off and retry
   ```

3. **Partial System Failure**
   ```python
   # One agent fails, others continue
   # System should complete with degraded results
   ```

4. **Network Failure Recovery**
   ```python
   # Network drops during tournament
   # System should retry and continue
   ```

**Implementation checklist**:
- [ ] Create test suite for failure scenarios
- [ ] Run end-to-end tests with simulated failures
- [ ] Verify system recovers and continues
- [ ] Measure success rate improvement
- [ ] Document test results

---

#### Task 4.2: Update Documentation

**Files to update**:
- `docs/architecture/ROBUST_PARSING_ARCHITECTURE.md` (update with resilience section)
- `README.md` (add reliability section)

**Implementation checklist**:
- [ ] Document resilience features
- [ ] Add troubleshooting guide
- [ ] Update configuration documentation
- [ ] Add best practices section

---

## Success Criteria

### **Quantitative Metrics**:
- [ ] **Report Generation Success Rate**: >80% (currently ~0%)
- [ ] **API Call Success Rate**: >95%
- [ ] **Mean Time to Recovery**: <2 minutes
- [ ] **Error Recovery Rate**: >90%

### **Qualitative Metrics**:
- [ ] System doesn't crash on single API failure
- [ ] System continues with degraded functionality
- [ ] Users get meaningful error messages
- [ ] System completes research even with partial failures

---

## Testing Checklist

### **Before Deployment**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Failure simulation tests pass
- [ ] Manual test with real research topic succeeds
- [ ] Documentation is updated

### **After Deployment**:
- [ ] Monitor success rate in production
- [ ] Track error recovery metrics
- [ ] Collect user feedback
- [ ] Iterate based on results

---

## Risk Mitigation

### **Potential Issues**:
1. **Timeout too aggressive**: May kill valid operations
   - **Mitigation**: Test with realistic durations, add buffer

2. **Circuit breaker too sensitive**: May block healthy LLMs
   - **Mitigation**: Adjust thresholds based on monitoring

3. **Retry logic causing billing**: May retry too many times
   - **Mitigation**: Add max retry limits, track costs

4. **Graceful recovery hiding real bugs**: May mask real issues
   - **Mitigation**: Log all errors, set up alerts

---

## Next Steps After Phase 1

Once Phase 1 is complete and working:

1. **Measure Impact**: Track success rate improvements
2. **Collect Feedback**: Get user input on reliability
3. **Plan Phase 2**: Consider health monitoring and parallel execution
4. **Iterate**: Improve based on real-world usage

---

**This plan provides concrete, implementable steps to fix the critical reliability issues preventing successful report generation.**
