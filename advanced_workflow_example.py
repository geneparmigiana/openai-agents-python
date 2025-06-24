"""
Advanced Workflow Example

This demonstrates how to build sophisticated multi-agent workflows using
the core primitives we've established.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any

from agents import Agent, function_tool, RunContextWrapper, ModelSettings

from workflow_primitives import (
    WorkflowSystemBuilder, StateScope, BaseWorkflow, WorkflowContext, 
    WorkflowResult, WorkflowStatus, MemoryStateBackend
)


# =============================================================================
# 1. SPECIALIZED AGENTS WITH CHAIN OF THOUGHT
# =============================================================================

@dataclass
class ReasoningStep:
    """Structure for chain of thought reasoning"""
    thought: str
    action: str
    observation: str
    confidence: float


@dataclass
class ChainOfThought:
    """Complete reasoning chain"""
    steps: List[ReasoningStep]
    final_answer: str
    overall_confidence: float


# Create specialized agents with different capabilities
research_agent = Agent(
    name="Research Specialist",
    instructions="""
    You are a research specialist who excels at finding and synthesizing information.
    
    Think step by step for each research task:
    1. Break down the research question into key components
    2. Identify the best sources and methods for each component  
    3. Synthesize findings into coherent insights
    4. Rate your confidence in each finding
    
    Always provide detailed reasoning for your conclusions.
    """
)

analysis_agent = Agent(
    name="Analysis Specialist", 
    instructions="""
    You are an analysis specialist who excels at pattern recognition and insight generation.
    
    For each analysis task:
    1. Identify key patterns and trends in the data
    2. Determine statistical significance and confidence levels
    3. Generate actionable insights and recommendations
    4. Highlight potential risks or limitations
    
    Be precise and quantitative in your analysis.
    """,
    output_type=ChainOfThought  # Structured output for explicit reasoning
)

synthesis_agent = Agent(
    name="Synthesis Specialist",
    instructions="""
    You are a synthesis specialist who combines multiple sources into coherent outputs.
    
    Your process:
    1. Review all input sources for consistency and quality
    2. Identify complementary and conflicting information
    3. Create a unified narrative that addresses all key points
    4. Ensure logical flow and clear conclusions
    
    Produce high-quality, publication-ready content.
    """
)


# =============================================================================
# 2. STATEFUL WORKFLOWS WITH CHECKPOINTING
# =============================================================================

class StatefulResearchWorkflow(BaseWorkflow):
    """Research workflow with state management and checkpointing"""
    
    def __init__(self):
        super().__init__(
            name="stateful_research",
            description="Comprehensive research workflow with state persistence"
        )
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute research workflow with checkpointing"""
        
        try:
            # Stage 1: Research Planning (with checkpoint)
            if not await context.state_manager.has_checkpoint("research_plan"):
                research_plan = await self._create_research_plan(input_data, context)
                await context.state_manager.save_checkpoint("research_plan", research_plan)
            else:
                research_plan = await context.state_manager.load_checkpoint("research_plan") or ""
            
            # Stage 2: Data Collection (with checkpoint)  
            if not await context.state_manager.has_checkpoint("research_data"):
                research_data = await self._collect_research_data(research_plan, context)
                await context.state_manager.save_checkpoint("research_data", research_data)
            else:
                research_data = await context.state_manager.load_checkpoint("research_data") or ""
            
            # Stage 3: Analysis (with checkpoint)
            if not await context.state_manager.has_checkpoint("analysis"):
                analysis_result = await self._analyze_data(research_data, context)
                await context.state_manager.save_checkpoint("analysis", analysis_result)
            else:
                loaded_analysis = await context.state_manager.load_checkpoint("analysis")
                analysis_result = loaded_analysis if loaded_analysis else ChainOfThought(steps=[], final_answer="", overall_confidence=0.0)
            
            # Stage 4: Final Synthesis
            final_report = await self._synthesize_findings(
                research_plan, research_data, analysis_result, context
            )
            
            # Store final result in persistent state
            await context.state_manager.set(
                "final_report",
                final_report,
                scope=StateScope.PERSISTENT
            )
            
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.COMPLETED,
                result=final_report,
                metadata={
                    "stages_completed": 4,
                    "checkpoints_used": 3,
                    "session_id": context.session_id
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )
    
    async def _create_research_plan(self, input_data: Any, context: WorkflowContext) -> str:
        """Create research plan using research agent"""
        from agents import Runner
        
        result = await Runner.run(
            research_agent,
            f"Create a detailed research plan for: {input_data}",
            context=context.create_agent_context()
        )
        return result.final_output
    
    async def _collect_research_data(self, plan: str, context: WorkflowContext) -> str:
        """Simulate data collection based on plan"""
        from agents import Runner
        
        result = await Runner.run(
            research_agent,
            f"Based on this plan, simulate collecting research data: {plan}",
            context=context.create_agent_context()
        )
        return result.final_output
    
    async def _analyze_data(self, data: str, context: WorkflowContext) -> ChainOfThought:
        """Analyze data using analysis agent"""
        from agents import Runner
        
        result = await Runner.run(
            analysis_agent,
            f"Analyze this research data: {data}",
            context=context.create_agent_context()
        )
        return result.final_output
    
    async def _synthesize_findings(
        self, plan: str, data: str, analysis: ChainOfThought, context: WorkflowContext
    ) -> str:
        """Synthesize all findings into final report"""
        from agents import Runner
        
        synthesis_input = f"""
        Research Plan: {plan}
        
        Research Data: {data}
        
        Analysis Results: {analysis.final_answer}
        Confidence: {analysis.overall_confidence}
        
        Create a comprehensive final report.
        """
        
        result = await Runner.run(
            synthesis_agent,
            synthesis_input,
            context=context.create_agent_context()
        )
        return result.final_output


# =============================================================================
# 3. PARALLEL EXECUTION WORKFLOW
# =============================================================================

class ParallelAnalysisWorkflow(BaseWorkflow):
    """Workflow that runs multiple agents in parallel"""
    
    def __init__(self):
        super().__init__(
            name="parallel_analysis",
            description="Run multiple analysis approaches in parallel"
        )
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute multiple analysis agents in parallel"""
        from agents import Runner
        
        try:
            # Create different analysis prompts
            prompts = [
                f"Analyze from a technical perspective: {input_data}",
                f"Analyze from a business perspective: {input_data}",
                f"Analyze from a risk perspective: {input_data}",
            ]
            
            # Run analyses in parallel
            tasks = [
                Runner.run(analysis_agent, prompt, context=context.create_agent_context())
                for prompt in prompts
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Analysis {i+1} failed: {result}")
                else:
                    successful_results.append(result.final_output)
            
            # Synthesize parallel results
            if successful_results:
                # Format results safely
                result_summaries = []
                for i, result in enumerate(successful_results):
                    if hasattr(result, 'final_answer'):
                        result_summaries.append(f"Analysis {i+1}: {result.final_answer}")
                    else:
                        result_summaries.append(f"Analysis {i+1}: {str(result)}")
                
                synthesis_input = f"""
                Multiple analysis perspectives on: {input_data}
                
                Results:
                {chr(10).join(result_summaries)}
                
                Synthesize these perspectives into a unified analysis.
                """
                
                synthesis_result = await Runner.run(
                    synthesis_agent,
                    synthesis_input,
                    context=context.create_agent_context()
                )
                
                return WorkflowResult(
                    workflow_id=context.workflow_id,
                    status=WorkflowStatus.COMPLETED,
                    result=synthesis_result.final_output,
                    metadata={
                        "parallel_analyses": len(successful_results),
                        "failed_analyses": len(results) - len(successful_results)
                    }
                )
            else:
                return WorkflowResult(
                    workflow_id=context.workflow_id,
                    status=WorkflowStatus.FAILED,
                    error="All parallel analyses failed"
                )
                
        except Exception as e:
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )


# =============================================================================
# 4. AGENT-TO-AGENT COMMUNICATION WITH TOOLS
# =============================================================================

@function_tool
async def query_research_database(
    query: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Query the research database for information"""
    # Simulate database query
    return f"Database results for '{query}': [Simulated research data related to {query}]"


@function_tool
async def store_research_finding(
    finding: str,
    category: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Store a research finding in the shared knowledge base"""
    workflow_context = context.context.get('workflow_context')
    if workflow_context:
        # Store in workflow state
        findings = await workflow_context.state_manager.get('research_findings', scope=StateScope.SESSION) or []
        findings.append({"finding": finding, "category": category})
        await workflow_context.state_manager.set('research_findings', findings, scope=StateScope.SESSION)
        return f"Stored finding in category '{category}'"
    return "Failed to store finding"


@function_tool
async def get_research_findings(
    category: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Retrieve research findings from shared knowledge base"""
    workflow_context = context.context.get('workflow_context')
    if workflow_context:
        findings = await workflow_context.state_manager.get('research_findings', scope=StateScope.SESSION) or []
        category_findings = [f for f in findings if f['category'] == category]
        return f"Findings for {category}: {category_findings}"
    return "No findings available"


# Create agents with shared tools
collaborative_researcher = Agent(
    name="Collaborative Researcher",
    instructions="""
    You are a collaborative researcher who uses shared tools to store and retrieve findings.
    Use the query_research_database tool to find information.
    Use store_research_finding to save important discoveries.
    Use get_research_findings to see what others have found.
    """,
    tools=[query_research_database, store_research_finding, get_research_findings]
)

collaborative_analyst = Agent(
    name="Collaborative Analyst", 
    instructions="""
    You are a collaborative analyst who builds on others' research.
    Use get_research_findings to see what researchers have discovered.
    Use store_research_finding to save your analytical insights.
    """,
    tools=[store_research_finding, get_research_findings]
)


# =============================================================================
# 5. PUTTING IT ALL TOGETHER - DEMO
# =============================================================================

async def run_advanced_demo():
    """Demonstrate the advanced workflow patterns"""
    
    print("🚀 Starting Advanced Workflow Demo\n")
    
    # 1. Build the workflow system
    system = (WorkflowSystemBuilder()
              .with_state_backend(MemoryStateBackend())
              .register_workflow(StatefulResearchWorkflow())
              .register_workflow(ParallelAnalysisWorkflow())
              .register_agent_workflow("collaborative_research", collaborative_researcher, "Research with shared tools")
              .register_agent_workflow("collaborative_analysis", collaborative_analyst, "Analysis with shared tools")
              .register_agent_tool("researcher", research_agent, "Expert research capabilities")
              .register_agent_tool("analyst", analysis_agent, "Expert analysis capabilities"))
    
    workflow_engine, tool_registry, event_bus = system.build()
    
    # 2. Demo: Stateful workflow with checkpointing
    print("1️⃣ Running Stateful Research Workflow...")
    research_result = await workflow_engine.execute_workflow(
        "stateful_research",
        "Impact of AI on software development productivity",
        session_id="demo_session_1"
    )
    print(f"✅ Research completed: {research_result.is_success()}")
    print(f"📊 Metadata: {research_result.metadata}\n")
    
    # 3. Demo: Parallel execution workflow
    print("2️⃣ Running Parallel Analysis Workflow...")
    parallel_result = await workflow_engine.execute_workflow(
        "parallel_analysis", 
        "Remote work trends in tech companies",
        session_id="demo_session_2"
    )
    print(f"✅ Parallel analysis completed: {parallel_result.is_success()}")
    print(f"📊 Metadata: {parallel_result.metadata}\n")
    
    # 4. Demo: Collaborative workflow with shared state
    print("3️⃣ Running Collaborative Research...")
    
    # First researcher gathers data
    research_collab_result = await workflow_engine.execute_workflow(
        "collaborative_research",
        "Research the benefits of microservices architecture",
        session_id="collab_session"
    )
    print(f"✅ Collaborative research completed: {research_collab_result.is_success()}")
    
    # Then analyst builds on the research
    analysis_collab_result = await workflow_engine.execute_workflow(
        "collaborative_analysis", 
        "Analyze the microservices research findings",
        session_id="collab_session"  # Same session to share state
    )
    print(f"✅ Collaborative analysis completed: {analysis_collab_result.is_success()}\n")
    
    # 5. Demo: Create composite agent using tool registry
    print("4️⃣ Creating Composite Agent...")
    super_agent = tool_registry.create_composite_agent(
        name="Research Director",
        instructions="You are a research director who orchestrates research and analysis tasks using your team of specialists.",
        tool_names=["researcher", "analyst"]
    )
    
    # Register and run composite workflow
    system.register_agent_workflow("research_direction", super_agent, "Director-level research orchestration")
    
    director_result = await workflow_engine.execute_workflow(
        "research_direction",
        "Conduct a comprehensive study on the future of work in tech",
        session_id="director_session"
    )
    print(f"✅ Research Director workflow completed: {director_result.is_success()}\n")
    
    # 6. Demo: Create MCP server
    print("5️⃣ Creating MCP Server...")
    mcp_server = system.create_mcp_server()
    if mcp_server:
        print("✅ MCP server created! All workflows are now available as MCP tools.")
        print("📡 Available workflows:")
        for workflow_name in workflow_engine.workflows.keys():
            print(f"   - {workflow_name}")
    else:
        print("⚠️  MCP not available (install with: pip install mcp)")
    
    print("\n🎉 Advanced workflow demo completed!")
    
    return workflow_engine, tool_registry, event_bus


if __name__ == "__main__":
    asyncio.run(run_advanced_demo())