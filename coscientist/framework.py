"""
The overall framework that takes a CoscientistStateManager from global_state.py,
setups the agents, and organizes the multi-agent system. The framework will be controlled
by a supervisor agent.
"""

import asyncio
import logging
import math
import os
import random

import numpy as np
from langchain_anthropic import ChatAnthropic
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from coscientist.evolution_agent import build_evolution_agent
from coscientist.final_report_agent import build_final_report_agent
from coscientist.generation_agent import (
    CollaborativeConfig,
    IndependentConfig,
    build_generation_agent,
)
from coscientist.global_state import CoscientistStateManager, log_progress
from coscientist.status_manager import StatusManager, ResearchStatus
from coscientist.literature_review_agent import build_literature_review_agent
from coscientist.meta_review_agent import build_meta_review_agent
from coscientist.reasoning_types import ReasoningType
from coscientist.reflection_agent import build_deep_verification_agent
from coscientist.supervisor_agent import build_supervisor_agent
from coscientist.validation import (
    ValidationError,
    validate_researcher_config,
    validate_gpt_researcher_config_sync,
)

# Load all LLM configuration from researcher_config.json
# NO HARDCODED DEFAULTS - config file is the single source of truth
from coscientist.config_loader import (
    create_llms_from_config,
    create_embeddings_from_config,
    validate_all_config,
    ConfigurationError
)

# Load LLMs from config - this will CRASH if config is wrong
_CONFIG_LLMS = create_llms_from_config()
_LLM_POOL = _CONFIG_LLMS['pool']  # Dict of unique LLMs by model name


class CoscientistConfig:
    """
    Configuration for the Coscientist system.

    Note that the config for GPTResearcher which is used throughout the system
    is defined in `researcher_config.json`.

    Attributes
    ----------
    literature_review_agent_llm : BaseChatModel
        The language model for the literature review. This LLM decides on the research
        subtopics for GPTResearcher.
    generation_agent_llms : dict[str, BaseChatModel]
        The language models for the generation agents
    reflection_agent_llms : dict[str, BaseChatModel]
        The language models for the reflection agents
    evolution_agent_llms : dict[str, BaseChatModel]
        The language models for the evolution agents
    meta_review_agent_llm : BaseChatModel
        The language model for the meta-review. Gemini works best because of the long
        context window that isn't severely rate limited like other providers.
    proximity_agent_embedding_model : Embeddings
        The embedding model for the proximity agent
    specialist_fields : list[str]
        The fields of expertise for generation agents. This list should be expanded
        by the configuration agent.

    """

    def __init__(
        self,
        literature_review_agent_llm: BaseChatModel = None,
        generation_agent_llms: dict[str, BaseChatModel] = None,
        reflection_agent_llms: dict[str, BaseChatModel] = None,
        evolution_agent_llms: dict[str, BaseChatModel] = None,
        meta_review_agent_llm: BaseChatModel = None,
        supervisor_agent_llm: BaseChatModel = None,
        final_report_agent_llm: BaseChatModel = None,
        proximity_agent_embedding_model: Embeddings = None,
        specialist_fields: list[str] | None = None,
    ):
        """
        Initialize Coscientist configuration.

        ALL parameters default to None and are loaded from researcher_config.json.
        Pass explicit values ONLY if you need to override the config.
        """
        # Get SMART_LLM from config as default for single-agent tasks
        default_llm = _CONFIG_LLMS['SMART_LLM']

        # Use config defaults for all LLMs
        self.literature_review_agent_llm = literature_review_agent_llm or default_llm
        self.meta_review_agent_llm = meta_review_agent_llm or default_llm
        self.supervisor_agent_llm = supervisor_agent_llm or default_llm
        self.final_report_agent_llm = final_report_agent_llm or default_llm

        # For agent pools, use all unique LLMs from config
        self.generation_agent_llms = generation_agent_llms or _LLM_POOL
        self.reflection_agent_llms = reflection_agent_llms or _LLM_POOL
        self.evolution_agent_llms = evolution_agent_llms or _LLM_POOL

        # Load embeddings from config
        self.proximity_agent_embedding_model = proximity_agent_embedding_model or create_embeddings_from_config()

        # Default fields
        self.specialist_fields = specialist_fields or ["biology"]


class CoscientistFramework:
    """
    The framework that takes a CoscientistStateManager from global_state.py,
    setups the agents, and organizes the multi-agent system. The framework will be controlled
    by a supervisor agent.
    """

    def __init__(
        self, config: CoscientistConfig, state_manager: CoscientistStateManager
    ):
        # CRITICAL: Validate configuration before doing ANY work
        # This ensures catastrophic failure if configs are wrong
        self._validate_configuration()

        self.config = config
        self.state_manager = state_manager
        
        # Initialize research provider at framework level
        # This will be used by ALL agents (literature_review, reflection, etc.)
        from coscientist.research_backend import create_research_provider
        from coscientist.config_loader import load_researcher_config
        
        research_config = load_researcher_config()
        output_dir = state_manager._state._output_dir
        self.research_provider = create_research_provider(research_config, output_dir)
        
        logging.info(f"Research provider initialized: {research_config.get('RESEARCH_BACKEND', 'openai_deep_research')}")

    def _validate_configuration(self) -> None:
        """
        Validate critical configurations at framework initialization.

        Uses the strict validation from config_loader which makes REAL API calls.
        This will CRASH immediately if anything is wrong.

        NO TRY/EXCEPT - Let errors propagate and kill the process.
        """
        # This function makes real API calls and crashes if anything fails
        validate_all_config()

    def list_generation_llm_names(self) -> list[str]:
        """
        List the names of the generation agents.
        """
        return list(self.config.generation_agent_llms.keys())

    def list_generation_modes(self) -> list[str]:
        """
        List the names of the generation modes.
        """
        return ["independent", "collaborative"]

    def list_reflection_llm_names(self) -> list[str]:
        """
        List the names of the reflection agents.
        """
        return list(self.config.reflection_agent_llms.keys())

    def list_evolution_llm_names(self) -> list[str]:
        """
        List the names of the evolution agents.
        """
        return list(self.config.evolution_agent_llms.keys())

    def list_evolution_modes(self) -> list[str]:
        """
        List the names of the evolution modes.
        """
        return ["evolve_from_feedback", "out_of_the_box"]

    def list_specialist_fields(self) -> list[str]:
        """
        List the names of the specialist fields.
        """
        return self.config.specialist_fields

    def list_reasoning_types(self) -> list[str]:
        """
        List the names of the reasoning types.
        """
        return list(ReasoningType.__members__.keys())

    def get_semantic_communities(
        self, resolution: float = 1.0, min_weight: float = 0.85
    ) -> list[set[str]]:
        """
        Get the semantic communities of the hypotheses.
        """
        self.state_manager.proximity_graph.update_edges()
        return self.state_manager.proximity_graph.get_semantic_communities(
            resolution=resolution, min_weight=min_weight
        )

    def process_reflection_queue(self) -> None:
        """
        Process all hypotheses in the reflection queue through deep verification.

        This method pops hypotheses from the reflection queue until it's empty,
        runs them through deep verification, and adds the reviewed hypotheses
        to the state manager.
        """
        while not self.state_manager.reflection_queue_is_empty:
            # This pops from the reflection queue until it's empty
            initial_reflection_state = self.state_manager.next_reflection_state()
            llm_name = random.choice(self.list_reflection_llm_names())
            reflection_agent = build_deep_verification_agent(
                llm=self.config.reflection_agent_llms[llm_name],
                review_llm=self.config.meta_review_agent_llm,
                parallel=False,
                checkpointer=None,
            )
            final_reflection_state = reflection_agent.invoke(initial_reflection_state)
            if final_reflection_state["passed_initial_filter"]:
                self.state_manager.add_reviewed_hypothesis(
                    final_reflection_state["reviewed_hypothesis"]
                )
                self.state_manager.advance_reviewed_hypothesis()

    def _generate_new_hypothesis(self, timeout: float = 300.0) -> None:
        """
        Run the hypothesis generation for a given mode and config.

        Parameters
        ----------
        timeout : float
            Timeout in seconds for hypothesis generation. Default is 300 (5 minutes).
        """
        # TODO: The mode and roles should be selected by the supervisor agent.
        # Randomly pick a mode, a reasoning type, and a specialist field.
        mode = random.choice(self.list_generation_modes())
        if mode == "independent":
            llm_name = random.choice(self.list_generation_llm_names())
            reasoning_type = random.choice(self.list_reasoning_types())
            specialist_field = random.choice(self.list_specialist_fields())
            config = IndependentConfig(
                llm=self.config.generation_agent_llms[llm_name],
                reasoning_type=getattr(ReasoningType, reasoning_type),
                field=specialist_field,
            )
            first_agent_name = None
        elif mode == "collaborative":
            llm_names = np.random.choice(self.list_generation_llm_names(), 2).tolist()
            specialist_fields = np.random.choice(
                self.list_specialist_fields(), 2
            ).tolist()
            reasoning_types = np.random.choice(self.list_reasoning_types(), 2).tolist()

            agent_names = [
                f"{llm_name}_{field}"
                for llm_name, field in zip(llm_names, specialist_fields)
            ]
            config = CollaborativeConfig(
                agent_names=agent_names,
                agent_fields=dict(zip(agent_names, specialist_fields)),
                agent_reasoning_types={
                    name: getattr(ReasoningType, reasoning_type)
                    for name, reasoning_type in zip(agent_names, reasoning_types)
                },
                llms={
                    name: self.config.generation_agent_llms[llm_name]
                    for name, llm_name in zip(agent_names, llm_names)
                },
                max_turns=10,
            )
            first_agent_name = agent_names[0]

        # TODO: Make this async
        generation_agent = build_generation_agent(mode, config)
        initial_generation_state = self.state_manager.next_generation_state(
            mode, first_agent_name
        )

        # Note: Since this is a sync method being called from async context,
        # we can't use asyncio.wait_for here. The timeout should be implemented
        # in the agent itself or by making this method async.
        logging.info(f"Starting hypothesis generation with mode: {mode}")
        try:
            final_generation_state = generation_agent.invoke(initial_generation_state)
            self.state_manager.add_generated_hypothesis(
                final_generation_state["hypothesis"]
            )
            logging.info("Hypothesis generation completed successfully")
        except Exception as e:
            logging.error(f"Hypothesis generation failed: {e}")
            raise

    async def start(self, n_hypotheses: int = 8) -> None:
        """
        Starts the Coscientist system with a fixed number of initial
        hypotheses.
        """
        assert n_hypotheses >= 2, "Must generate at least two hypotheses to start"
        if self.state_manager.is_started:
            raise ValueError(
                "Coscientist system has already been started. "
                f"Use one of {self.available_actions()} instead!"
            )

        # Perform the initial literature review.
        if not self.state_manager.has_literature_review:
            literature_review_agent = build_literature_review_agent(
                self.config.literature_review_agent_llm
            )
            initial_lit_review_state = self.state_manager.next_literature_review_state(
                # TODO: Make this configurable
                max_subtopics=5
            )
            final_lit_review_state = await literature_review_agent.ainvoke(
                initial_lit_review_state
            )
            self.state_manager.update_literature_review(final_lit_review_state)

        # TODO: Make this async
        _ = await self.generate_new_hypotheses(
            n_hypotheses=max(0, n_hypotheses - self.state_manager.total_hypotheses)
        )

        # Run the EloTournament
        # The top k for the bracket should the nearest power of
        # 2 less than the number of hypotheses and no more than 16.
        k_bracket = min(16, 2 ** math.floor(math.log2(n_hypotheses)))
        # TODO: Figure out the right LLM for this job; should it be different from meta-review?
        # Feels like it should be fixed for the sake of consistency though
        _ = await self.run_tournament(k_bracket=k_bracket)
        _ = await self.run_meta_review(k_bracket=k_bracket)

    async def generate_new_hypotheses(
        self, n_hypotheses: int = 2, timeout_per_hypothesis: float = 300.0
    ) -> None:
        """
        Generate new hypotheses.

        Parameters
        ----------
        n_hypotheses : int
            Number of hypotheses to generate.
        timeout_per_hypothesis : float
            Timeout in seconds for each hypothesis generation. Default is 300 (5 minutes).
        """
        for i in range(n_hypotheses):
            try:
                logging.info(f"Generating hypothesis {i+1}/{n_hypotheses}")
                # Run the sync method in an executor with timeout
                await asyncio.wait_for(
                    asyncio.to_thread(self._generate_new_hypothesis),
                    timeout=timeout_per_hypothesis,
                )
                self.state_manager.advance_hypothesis(kind="generated")
            except asyncio.TimeoutError:
                logging.error(
                    f"Hypothesis generation {i+1}/{n_hypotheses} timed out after "
                    f"{timeout_per_hypothesis} seconds. Skipping."
                )
            except Exception as e:
                logging.error(
                    f"Hypothesis generation {i+1}/{n_hypotheses} failed: {e}. Skipping."
                )

        # Now run through the review queue and perform deep verification
        self.process_reflection_queue()
        self.state_manager.update_proximity_graph_edges()

    async def evolve_hypotheses(self, n_hypotheses: int = 4) -> None:
        """
        Takes the top (n_hypotheses // 2) hypotheses and evolves them. Also
        randomly selects (n_hypotheses // 2) hypotheses to evolve.
        """
        assert n_hypotheses >= 2, "Must evolve at least two hypotheses"
        assert self.state_manager.is_started, "Coscientist system must be started first"
        evolution_candidate_uids = (
            self.state_manager.get_tournament_hypotheses_for_evolution()
        )
        if len(evolution_candidate_uids) < n_hypotheses:
            logging.warning(
                f"Only {len(evolution_candidate_uids)} hypotheses are qualified for evolution. "
                f"Evolving {len(evolution_candidate_uids)} hypotheses."
            )
            n_hypotheses = len(evolution_candidate_uids)

        # The first uids are the top ranked hypotheses
        top_ranked_uids = evolution_candidate_uids[: (n_hypotheses // 2)]
        # The rest are randomly selected
        random_uids = np.random.choice(
            evolution_candidate_uids[(n_hypotheses // 2) :],
            size=n_hypotheses // 2,
            replace=False,
        ).tolist()

        # Evolve the top ranked and random hypotheses based on feedback
        for uid in top_ranked_uids + random_uids:
            initial_evolution_state = self.state_manager.next_evolution_state(
                mode="evolve_from_feedback", uid_to_evolve=uid
            )
            llm_name = random.choice(self.list_evolution_llm_names())
            evolution_agent = build_evolution_agent(
                mode="evolve_from_feedback",
                llm=self.config.evolution_agent_llms[llm_name],
            )
            final_evolution_state = evolution_agent.invoke(initial_evolution_state)
            self.state_manager.add_evolved_hypothesis(
                final_evolution_state["evolved_hypothesis"]
            )
            self.state_manager.advance_hypothesis(kind="evolved")

        # Run one round instance of evolving the top ranked hypotheses
        # into something new
        out_of_box_initial_state = self.state_manager.next_evolution_state(
            mode="out_of_the_box",
            top_k=n_hypotheses // 2,
        )
        llm_name = random.choice(self.list_evolution_llm_names())
        evolution_agent = build_evolution_agent(
            mode="out_of_the_box", llm=self.config.evolution_agent_llms[llm_name]
        )
        out_of_box_state = evolution_agent.invoke(out_of_box_initial_state)
        self.state_manager.add_evolved_hypothesis(
            out_of_box_state["evolved_hypothesis"]
        )

        # Move the evolved hypotheses to the reflection queue
        self.state_manager.advance_hypothesis(kind="evolved")

        # TODO: Do we have to worry about reflecting on hypotheses that are
        # already in the reflection queue but weren't advanced yet?
        # Do we always want to run reflection immediately after a hypothesis
        # is generated?
        self.process_reflection_queue()

        # Move the reviewed hypothesis to the EloTournament.
        self.state_manager.update_proximity_graph_edges()

    async def expand_literature_review(self) -> None:
        """
        Expands the literature review by adding more subtopics.
        """
        initial_lit_review_state = self.state_manager.next_literature_review_state(
            # TODO: Make this configurable
            max_subtopics=5
        )
        literature_review_agent = build_literature_review_agent(
            self.config.literature_review_agent_llm
        )
        final_lit_review_state = await literature_review_agent.ainvoke(
            initial_lit_review_state
        )
        self.state_manager.update_literature_review(final_lit_review_state)

    async def run_tournament(self, k_bracket: int = 8) -> None:
        k_bracket = min(
            k_bracket,
            2 ** math.floor(math.log2(self.state_manager.num_tournament_hypotheses)),
        )
        self.state_manager.run_tournament(
            llm=self.config.meta_review_agent_llm, k_bracket=k_bracket
        )

    async def run_meta_review(self, k_bracket: int = 8) -> None:
        initial_meta_review_state = self.state_manager.next_meta_review_state(
            top_k=k_bracket
        )
        meta_review_agent = build_meta_review_agent(self.config.meta_review_agent_llm)
        final_meta_review_state = meta_review_agent.invoke(initial_meta_review_state)
        self.state_manager.update_meta_review(final_meta_review_state)

    async def finish(self) -> None:
        initial_final_report_state = self.state_manager.next_final_report_state(top_k=3)
        final_report_agent = build_final_report_agent(
            self.config.final_report_agent_llm
        )
        final_report_state = final_report_agent.invoke(initial_final_report_state)
        self.state_manager.update_final_report(final_report_state)

    @classmethod
    def available_actions(self) -> list[str]:
        """
        List the available actions for the Coscientist system.
        """
        return [
            "generate_new_hypotheses",
            "evolve_hypotheses",
            "expand_literature_review",
            "run_tournament",
            "run_meta_review",
            "finish",
        ]

    async def run(self, max_iterations: int = 20) -> tuple[str, str]:
        """
        Runs the coscientist system until it is finished.

        Parameters
        ----------
        max_iterations : int
            Maximum number of supervisor iterations to prevent infinite loops.
            Default is 20.
        """
        # Get output directory for progress tracking
        output_dir = self.state_manager._state._output_dir
        status_manager = StatusManager(output_dir)
        
        # Start off with 4 hypotheses
        if not self.state_manager.is_started:
            log_progress(output_dir, "START", "Literature Review and initial hypothesis generation")
            status_manager.update_status(ResearchStatus.RUNNING)
            _ = await self.start(n_hypotheses=4)
            log_progress(output_dir, "DONE", f"Literature review complete, {len(self.state_manager._state.generated_hypotheses)} hypotheses generated")

        supervisor_agent = build_supervisor_agent(self.config.supervisor_agent_llm)

        current_action = None
        iteration = 0
        while not self.state_manager.is_finished and iteration < max_iterations:
            iteration += 1
            logging.info(f"Supervisor iteration {iteration}/{max_iterations}")
            log_progress(output_dir, "ITERATION", f"{iteration}/{max_iterations}: Starting")

            initial_supervisor_state = self.state_manager.next_supervisor_state()
            final_supervisor_state = supervisor_agent.invoke(initial_supervisor_state)
            current_action = final_supervisor_state["action"]
            logging.info(f"Supervisor decided action: {current_action}")
            log_progress(output_dir, "ACTION", f"{current_action}")
            
            # Log current status
            num_reviewed = len(self.state_manager._state.reviewed_hypotheses)
            num_hypotheses = len(self.state_manager._state.generated_hypotheses)
            progress_pct = int((iteration / max_iterations) * 100)
            log_progress(output_dir, "STATUS", f"{num_reviewed} reviewed, {num_hypotheses} total hypotheses, {progress_pct}% complete")

            assert (
                current_action in self.available_actions()
            ), f"Invalid action: {current_action}. Available actions: {self.available_actions()}"
            self.state_manager.update_supervisor_decision(final_supervisor_state)
            self.state_manager.add_action(current_action)
            _ = await getattr(self, current_action)()

        if iteration >= max_iterations:
            logging.warning(
                f"Reached maximum iterations ({max_iterations}). "
                f"System may not have fully completed."
            )
            status_manager.update_status(ResearchStatus.PAUSED, error=f"Reached max iterations ({max_iterations})")
        else:
            status_manager.update_status(ResearchStatus.COMPLETED)

        return self.state_manager.final_report, self.state_manager.meta_reviews[-1]
