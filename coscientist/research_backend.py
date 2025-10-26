"""
Configurable research backend supporting multiple providers:
- OpenAI Deep Research (o3/o4-mini)
- Perplexity API
- GPT-Researcher (legacy fallback)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Optional, Protocol, Dict, Any

logger = logging.getLogger(__name__)


class ResearchBackend(str, Enum):
    """Available research backends."""
    OPENAI_DEEP_RESEARCH = "openai_deep_research"
    PERPLEXITY = "perplexity"
    GPT_RESEARCHER = "gpt_researcher"


class ResearchProvider(Protocol):
    """Interface for research backends."""
    
    async def conduct_research(self, query: str, task_id: str) -> str:
        """
        Start research and return response_id (background) or result (blocking).
        
        Parameters
        ----------
        query : str
            Research query
        task_id : str
            Unique identifier for this task
            
        Returns
        -------
        str
            Response ID (if background) or final report (if blocking)
        """
        ...
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """
        Get result if ready, None if still running.
        
        Parameters
        ----------
        task_id : str
            Task identifier from conduct_research
            
        Returns
        -------
        Optional[str]
            Report if complete, None if still running
        """
        ...
    
    def supports_background_mode(self) -> bool:
        """Whether this provider supports async background execution."""
        ...
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress information for active task.
        
        Returns
        -------
        dict
            Progress info: {"status": str, "details": str, "percent": int}
        """
        ...


class OpenAIDeepResearchProvider:
    """OpenAI o3-deep-research / o4-mini-deep-research backend."""
    
    def __init__(self, config: dict, output_dir: str):
        from openai import OpenAI
        self.client = OpenAI(timeout=3600)
        self.model = config.get("OPENAI_DEEP_RESEARCH_MODEL", "o3-deep-research")
        self.background = config.get("OPENAI_DEEP_RESEARCH_BACKGROUND", True)
        self.output_dir = output_dir
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Initialized OpenAI Deep Research provider: model={self.model}, background={self.background}")
    
    def supports_background_mode(self) -> bool:
        return self.background
    
    async def conduct_research(self, query: str, task_id: str) -> str:
        """Start deep research task."""
        from coscientist.global_state import log_progress
        
        log_progress(self.output_dir, "RESEARCH_START", f"{task_id}: {query[:80]}...")
        logger.info(f"Starting OpenAI Deep Research: {task_id}")
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=query,
                background=self.background,
                tools=[{"type": "web_search_preview"}]
            )
            
            if self.background:
                self.active_tasks[task_id] = {
                    "response_id": response.id,
                    "query": query,
                    "started_at": time.time(),
                    "last_check": time.time()
                }
                logger.info(f"Background task started: {task_id} -> {response.id}")
                return response.id
            else:
                # Blocking mode - return result immediately
                log_progress(self.output_dir, "RESEARCH_DONE", f"{task_id}: Complete")
                return response.output_text
                
        except Exception as e:
            log_progress(self.output_dir, "RESEARCH_ERROR", f"{task_id}: {str(e)}")
            logger.error(f"OpenAI Deep Research failed for {task_id}: {e}")
            raise
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Poll for task completion."""
        from coscientist.global_state import log_progress
        
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return None
        
        task = self.active_tasks[task_id]
        
        try:
            response = self.client.responses.retrieve(task["response_id"])
            task["last_check"] = time.time()
            
            if response.status == "completed":
                elapsed = time.time() - task["started_at"]
                report = self._extract_report(response)
                log_progress(self.output_dir, "RESEARCH_DONE", 
                            f"{task_id}: Complete in {elapsed:.0f}s, {len(report)} chars")
                logger.info(f"Task {task_id} completed in {elapsed:.0f}s")
                del self.active_tasks[task_id]
                return report
                
            elif response.status == "failed":
                error = getattr(response, 'error', 'Unknown error')
                log_progress(self.output_dir, "RESEARCH_ERROR", f"{task_id}: {error}")
                logger.error(f"Task {task_id} failed: {error}")
                del self.active_tasks[task_id]
                return f"# Research Error\n\n{error}"
                
            else:
                # Still running - log progress
                progress = self.get_progress(task_id)
                if progress["details"]:
                    log_progress(self.output_dir, "RESEARCH_PROGRESS", 
                                f"{task_id}: {progress['details']}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking task {task_id}: {e}")
            return None
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Get current progress for task."""
        if task_id not in self.active_tasks:
            return {"status": "unknown", "details": "", "percent": 0}
        
        task = self.active_tasks[task_id]
        
        try:
            response = self.client.responses.retrieve(task["response_id"])
            
            if not hasattr(response, 'output') or not response.output:
                elapsed = time.time() - task["started_at"]
                return {
                    "status": "initializing",
                    "details": f"Initializing... ({elapsed:.0f}s elapsed)",
                    "percent": 5
                }
            
            # Parse structured output
            searches = [item for item in response.output if item.get("type") == "web_search_call"]
            completed = [s for s in searches if s.get("status") == "completed"]
            
            if searches:
                percent = int((len(completed) / len(searches)) * 90) + 5  # 5-95%
                current_action = searches[-1].get("action", {}) if searches else {}
                action_type = current_action.get("type", "")
                
                if action_type == "search":
                    details = f"Searching: {current_action.get('query', '')[:50]}..."
                elif action_type == "open_page":
                    details = f"Reading: {current_action.get('url', '')[:50]}..."
                else:
                    details = f"{len(completed)}/{len(searches)} searches complete"
                
                return {
                    "status": "researching",
                    "details": details,
                    "percent": percent
                }
            
            elapsed = time.time() - task["started_at"]
            return {
                "status": "working",
                "details": f"Processing... ({elapsed:.0f}s elapsed)",
                "percent": 10
            }
            
        except Exception as e:
            logger.debug(f"Could not parse progress for {task_id}: {e}")
            elapsed = time.time() - task["started_at"]
            return {
                "status": "running",
                "details": f"Running... ({elapsed:.0f}s elapsed)",
                "percent": 25
            }
    
    def _extract_report(self, response) -> str:
        """Extract report text with citations from response."""
        if hasattr(response, 'output_text'):
            return response.output_text
        
        # Parse structured output for message with annotations
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if item.get("type") == "message":
                    content = item.get("content", [])
                    for part in content:
                        if part.get("type") == "output_text":
                            text = part.get("text", "")
                            # TODO: Format annotations as markdown citations
                            return text
        
        return "# Research Complete\n\nNo output text found."


class PerplexityProvider:
    """Perplexity API backend."""
    
    def __init__(self, config: dict, output_dir: str):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI SDK required for Perplexity (pip install openai)")
        
        api_key = config.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY not set in config")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        self.model = config.get("PERPLEXITY_MODEL", "sonar-pro")
        self.output_dir = output_dir
        
        logger.info(f"Initialized Perplexity provider: model={self.model}")
    
    def supports_background_mode(self) -> bool:
        return False  # Perplexity is fast (~30s), no need for background
    
    async def conduct_research(self, query: str, task_id: str) -> str:
        """Conduct research via Perplexity."""
        from coscientist.global_state import log_progress
        
        log_progress(self.output_dir, "RESEARCH_START", f"{task_id}: Perplexity search")
        logger.info(f"Starting Perplexity research: {task_id}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": query}]
            )
            
            result = response.choices[0].message.content
            log_progress(self.output_dir, "RESEARCH_DONE", f"{task_id}: Complete, {len(result)} chars")
            logger.info(f"Perplexity research complete: {task_id}")
            
            # TODO: Extract citations from response if available
            return result
            
        except Exception as e:
            log_progress(self.output_dir, "RESEARCH_ERROR", f"{task_id}: {str(e)}")
            logger.error(f"Perplexity research failed for {task_id}: {e}")
            raise
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Perplexity is blocking, no polling needed."""
        raise NotImplementedError("Perplexity is blocking, use conduct_research directly")
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Perplexity doesn't support progress tracking."""
        return {"status": "running", "details": "Searching...", "percent": 50}


class GPTResearcherProvider:
    """Traditional GPT-Researcher backend (legacy fallback)."""
    
    def __init__(self, config: dict, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        logger.info("Initialized GPT-Researcher provider (legacy)")
    
    def supports_background_mode(self) -> bool:
        return False  # GPT-Researcher is always blocking
    
    async def conduct_research(self, query: str, task_id: str) -> str:
        """Conduct research via GPT-Researcher."""
        from gpt_researcher import GPTResearcher
        from gpt_researcher.utils.enum import Tone
        from coscientist.global_state import log_progress
        import os
        
        log_progress(self.output_dir, "RESEARCH_START", f"{task_id}: GPT-Researcher (legacy)")
        logger.info(f"Starting GPT-Researcher (legacy): {task_id}")
        
        try:
            researcher = GPTResearcher(
                query=query,
                report_type="research_report",
                report_format="markdown",
                verbose=False,
                tone=Tone.Objective,
                config_path=os.path.join(os.path.dirname(__file__), "researcher_config.json"),
            )
            
            # Blocking call (10-40 min)
            _ = await asyncio.wait_for(researcher.conduct_research(), timeout=900.0)
            report = await asyncio.wait_for(researcher.write_report(), timeout=60.0)
            
            log_progress(self.output_dir, "RESEARCH_DONE", f"{task_id}: Complete, {len(report)} chars")
            logger.info(f"GPT-Researcher complete: {task_id}")
            return report
            
        except asyncio.TimeoutError:
            msg = "GPT-Researcher timed out after 15 minutes"
            log_progress(self.output_dir, "RESEARCH_ERROR", f"{task_id}: {msg}")
            logger.error(f"GPT-Researcher timeout: {task_id}")
            return f"# Research Timeout\n\n{msg}"
            
        except Exception as e:
            log_progress(self.output_dir, "RESEARCH_ERROR", f"{task_id}: {str(e)}")
            logger.error(f"GPT-Researcher failed for {task_id}: {e}")
            raise
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """GPT-Researcher doesn't support polling."""
        raise NotImplementedError("GPT-Researcher is blocking, use conduct_research directly")
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """GPT-Researcher doesn't provide progress."""
        return {"status": "running", "details": "Web scraping in progress...", "percent": 50}


class HybridResearchProvider:
    """
    Uses primary provider with optional fallback.
    Supports: OpenAI Deep Research, Perplexity, GPT-Researcher
    """
    
    def __init__(self, config: dict, output_dir: str):
        backend = config.get("RESEARCH_BACKEND", "openai_deep_research")
        fallback_enabled = config.get("GPT_RESEARCHER_FALLBACK_ENABLED", False)
        
        logger.info(f"Initializing Hybrid Research Provider: backend={backend}, fallback={fallback_enabled}")
        
        # Create primary provider
        if backend == ResearchBackend.OPENAI_DEEP_RESEARCH:
            self.primary = OpenAIDeepResearchProvider(config, output_dir)
        elif backend == ResearchBackend.PERPLEXITY:
            self.primary = PerplexityProvider(config, output_dir)
        elif backend == ResearchBackend.GPT_RESEARCHER:
            self.primary = GPTResearcherProvider(config, output_dir)
        else:
            raise ValueError(f"Unknown research backend: {backend}")
        
        # Create fallback provider (GPT-Researcher) ONLY if enabled
        self.fallback = GPTResearcherProvider(config, output_dir) if fallback_enabled else None
        self.config = config
        self.output_dir = output_dir
    
    def supports_background_mode(self) -> bool:
        return self.primary.supports_background_mode()
    
    async def conduct_research(self, query: str, task_id: str) -> str:
        """Conduct research with primary - NO FALLBACK, fail fast."""
        try:
            return await self.primary.conduct_research(query, task_id)
        except Exception as e:
            logger.error(f"Research backend FAILED: {e}")
            # NO FALLBACK - Just raise immediately
            raise RuntimeError(f"Research failed for {task_id}: {e}") from e
    
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get result from primary provider."""
        return await self.primary.get_result(task_id)
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Get progress from primary provider."""
        return self.primary.get_progress(task_id)


def create_research_provider(config: dict, output_dir: str) -> ResearchProvider:
    """
    Factory for research backends.
    
    Parameters
    ----------
    config : dict
        Configuration from researcher_config.json
    output_dir : str
        Output directory for progress logging
        
    Returns
    -------
    ResearchProvider
        Configured research provider
    """
    return HybridResearchProvider(config, output_dir)

