"""
Reasoning as a Service - Modular Reasoning Patterns

This demonstrates how to outsource reasoning to external MCP servers or agents,
creating a modular, scalable reasoning architecture.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from agents import Agent, function_tool, RunContextWrapper
from workflow_primitives import (
    WorkflowSystemBuilder, BaseWorkflow, WorkflowContext, 
    WorkflowResult, WorkflowStatus, MemoryStateBackend
)


# =============================================================================
# 1. REASONING DATA STRUCTURES
# =============================================================================

@dataclass
class ReasoningRequest:
    """Structure for reasoning requests"""
    problem: str
    context: Dict[str, Any]
    reasoning_type: str  # "analytical", "creative", "logical", "causal"
    depth: str  # "quick", "standard", "deep"
    constraints: Optional[List[str]] = None


@dataclass
class ReasoningStep:
    """Individual reasoning step"""
    step_number: int
    thought: str
    reasoning_type: str
    evidence: List[str]
    confidence: float
    next_questions: Optional[List[str]] = None


@dataclass
class ReasoningResult:
    """Complete reasoning result"""
    request_id: str
    reasoning_chain: List[ReasoningStep]
    final_conclusion: str
    overall_confidence: float
    reasoning_method: str
    alternative_perspectives: Optional[List[str]] = None
    limitations: Optional[List[str]] = None


# =============================================================================
# 2. REASONING MCP SERVER (Specialized Reasoning Service)
# =============================================================================

def create_reasoning_mcp_server():
    """Create a specialized MCP server focused entirely on reasoning"""
    
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP not available - install with: pip install mcp")
        return None
    
    reasoning_server = FastMCP("Advanced Reasoning Service")
    
    @reasoning_server.tool()
    async def analytical_reasoning(
        problem: str, 
        context: str = "", 
        depth: str = "standard"
    ) -> str:
        """Perform analytical reasoning on a problem"""
        
        # This would typically call a specialized reasoning model
        # For demo, we'll simulate with structured reasoning
        reasoning_request = ReasoningRequest(
            problem=problem,
            context={"additional_info": context},
            reasoning_type="analytical",
            depth=depth
        )
        
        # Simulate reasoning process
        steps = [
            ReasoningStep(
                step_number=1,
                thought=f"Breaking down the problem: {problem}",
                reasoning_type="decomposition",
                evidence=["Problem structure analysis"],
                confidence=0.8
            ),
            ReasoningStep(
                step_number=2,
                thought="Identifying key variables and relationships",
                reasoning_type="analysis", 
                evidence=["Variable identification", "Relationship mapping"],
                confidence=0.85
            ),
            ReasoningStep(
                step_number=3,
                thought="Synthesizing findings into conclusion",
                reasoning_type="synthesis",
                evidence=["Integration of findings"],
                confidence=0.9
            )
        ]
        
        result = ReasoningResult(
            request_id="analytical_001",
            reasoning_chain=steps,
            final_conclusion=f"Based on analytical reasoning, the optimal approach to '{problem}' involves systematic decomposition and evidence-based analysis.",
            overall_confidence=0.85,
            reasoning_method="analytical_decomposition"
        )
        
        return json.dumps(result.__dict__, indent=2)
    
    @reasoning_server.tool()
    async def creative_reasoning(
        problem: str,
        context: str = "",
        brainstorm_count: int = 5
    ) -> str:
        """Perform creative/lateral reasoning on a problem"""
        
        # Simulate creative reasoning process
        steps = [
            ReasoningStep(
                step_number=1,
                thought="Exploring unconventional perspectives",
                reasoning_type="divergent",
                evidence=["Alternative viewpoints", "Analogical thinking"],
                confidence=0.7,
                next_questions=["What if we reversed the assumption?", "How would nature solve this?"]
            ),
            ReasoningStep(
                step_number=2,
                thought="Generating multiple creative solutions",
                reasoning_type="generative",
                evidence=["Brainstorming session", "Cross-domain inspiration"],
                confidence=0.75
            )
        ]
        
        result = ReasoningResult(
            request_id="creative_001",
            reasoning_chain=steps,
            final_conclusion=f"Creative exploration of '{problem}' reveals {brainstorm_count} innovative approaches, with emphasis on paradigm shifts and cross-domain solutions.",
            overall_confidence=0.75,
            reasoning_method="creative_divergent",
            alternative_perspectives=[
                "Biomimetic approach", 
                "Reverse engineering solution",
                "Analogical transfer from other domains"
            ]
        )
        
        return json.dumps(result.__dict__, indent=2)
    
    @reasoning_server.tool()
    async def logical_reasoning(
        premises: str,
        conclusion: str,
        reasoning_type: str = "deductive"
    ) -> str:
        """Perform formal logical reasoning"""
        
        steps = [
            ReasoningStep(
                step_number=1,
                thought="Formalizing premises into logical structure",
                reasoning_type="formalization",
                evidence=["Premise extraction", "Logic notation"],
                confidence=0.95
            ),
            ReasoningStep(
                step_number=2, 
                thought="Applying logical inference rules",
                reasoning_type=reasoning_type,
                evidence=["Modus ponens", "Syllogistic reasoning"],
                confidence=0.9
            )
        ]
        
        result = ReasoningResult(
            request_id="logical_001",
            reasoning_chain=steps,
            final_conclusion=f"Logical analysis confirms: {conclusion} follows from premises with high certainty",
            overall_confidence=0.92,
            reasoning_method=f"formal_{reasoning_type}",
            limitations=["Assumes premise validity", "Classical logic constraints"]
        )
        
        return json.dumps(result.__dict__, indent=2)
    
    return reasoning_server


# =============================================================================
# 3. REASONING AGENTS (Specialized Reasoning Capabilities)
# =============================================================================

# Create specialized reasoning agents
strategic_reasoner = Agent(
    name="Strategic Reasoner",
    instructions="""
    You are a strategic reasoning specialist. Your expertise:
    
    1. Long-term strategic planning and analysis
    2. Scenario planning and risk assessment  
    3. Multi-stakeholder perspective analysis
    4. Strategic option evaluation
    
    Always provide:
    - Clear reasoning chains
    - Multiple scenario considerations
    - Risk/benefit analysis
    - Confidence levels for each conclusion
    """,
    output_type=ReasoningResult
)

systems_reasoner = Agent(
    name="Systems Reasoner", 
    instructions="""
    You are a systems thinking specialist. Your expertise:
    
    1. Systems analysis and modeling
    2. Feedback loop identification
    3. Emergent behavior prediction
    4. Complex system optimization
    
    Always consider:
    - System boundaries and interfaces
    - Feedback loops and delays
    - Unintended consequences
    - Leverage points for change
    """,
    output_type=ReasoningResult
)

causal_reasoner = Agent(
    name="Causal Reasoner",
    instructions="""
    You are a causal reasoning specialist. Your expertise:
    
    1. Causal relationship identification
    2. Confounding factor analysis
    3. Causal mechanism explanation
    4. Intervention effect prediction
    
    Focus on:
    - Distinguishing correlation from causation
    - Identifying mediating variables
    - Assessing causal strength
    - Predicting intervention outcomes
    """,
    output_type=ReasoningResult
)


# =============================================================================
# 4. REASONING ORCHESTRATOR TOOLS
# =============================================================================

@function_tool
async def request_analytical_reasoning(
    problem: str,
    context: str = "",
    depth: str = "standard",
    runner_context: Optional[RunContextWrapper[Dict[str, Any]]] = None
) -> str:
    """Request analytical reasoning from external reasoning service"""
    
    # This would call the reasoning MCP server
    # For demo, we'll simulate the call
    reasoning_request = {
        "problem": problem,
        "context": context,
        "depth": depth,
        "type": "analytical"
    }
    
    # Simulate MCP call result
    return f"Analytical reasoning completed for: {problem}. Systematic analysis suggests a multi-stage approach with 85% confidence."


@function_tool
async def request_strategic_reasoning(
    problem: str,
    context: str = "",
    runner_context: Optional[RunContextWrapper[Dict[str, Any]]] = None
) -> str:
    """Request strategic reasoning from specialized agent"""
    
    from agents import Runner
    
    workflow_context = runner_context.context.get('workflow_context') if runner_context else None
    agent_context = workflow_context.create_agent_context() if workflow_context else {}
    
    result = await Runner.run(
        strategic_reasoner,
        f"Provide strategic reasoning for: {problem}. Context: {context}",
        context=agent_context
    )
    
    reasoning_result = result.final_output
    return f"Strategic analysis: {reasoning_result.final_conclusion} (Confidence: {reasoning_result.overall_confidence})"


@function_tool
async def request_systems_reasoning(
    problem: str,
    context: str = "",
    runner_context: Optional[RunContextWrapper[Dict[str, Any]]] = None
) -> str:
    """Request systems thinking analysis"""
    
    from agents import Runner
    
    workflow_context = runner_context.context.get('workflow_context') if runner_context else None
    agent_context = workflow_context.create_agent_context() if workflow_context else {}
    
    result = await Runner.run(
        systems_reasoner,
        f"Analyze from systems perspective: {problem}. Context: {context}",
        context=agent_context
    )
    
    reasoning_result = result.final_output
    return f"Systems analysis: {reasoning_result.final_conclusion} (Confidence: {reasoning_result.overall_confidence})"


@function_tool
async def request_causal_reasoning(
    problem: str,
    context: str = "",
    runner_context: Optional[RunContextWrapper[Dict[str, Any]]] = None
) -> str:
    """Request causal reasoning analysis"""
    
    from agents import Runner
    
    workflow_context = runner_context.context.get('workflow_context') if runner_context else None
    agent_context = workflow_context.create_agent_context() if workflow_context else {}
    
    result = await Runner.run(
        causal_reasoner,
        f"Perform causal analysis for: {problem}. Context: {context}",
        context=agent_context
    )
    
    reasoning_result = result.final_output
    return f"Causal analysis: {reasoning_result.final_conclusion} (Confidence: {reasoning_result.overall_confidence})"


# =============================================================================
# 5. MULTI-REASONING ORCHESTRATOR AGENT
# =============================================================================

reasoning_orchestrator = Agent(
    name="Reasoning Orchestrator",
    instructions="""
    You are a reasoning orchestrator who coordinates multiple specialized reasoning services.
    
    Your capabilities:
    - request_analytical_reasoning: For systematic, logical analysis
    - request_strategic_reasoning: For strategic planning and scenarios
    - request_systems_reasoning: For systems thinking and complexity
    - request_causal_reasoning: For causal relationships and mechanisms
    
    For each problem:
    1. Determine which reasoning approaches are most appropriate
    2. Request reasoning from appropriate specialists
    3. Synthesize multiple reasoning perspectives
    4. Identify areas of agreement and disagreement
    5. Provide meta-reasoning about the reasoning process itself
    
    Always consider:
    - Which reasoning types are most relevant
    - How different reasoning approaches complement each other
    - Confidence levels and limitations of each approach
    - Integration challenges between different reasoning styles
    """,
    tools=[
        request_analytical_reasoning,
        request_strategic_reasoning, 
        request_systems_reasoning,
        request_causal_reasoning
    ]
)


# =============================================================================
# 6. REASONING-AWARE WORKFLOW
# =============================================================================

class MultiReasoningWorkflow(BaseWorkflow):
    """Workflow that leverages multiple external reasoning services"""
    
    def __init__(self):
        super().__init__(
            name="multi_reasoning",
            description="Comprehensive analysis using multiple reasoning approaches"
        )
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute workflow using multiple reasoning services"""
        
        try:
            from agents import Runner
            
            # Stage 1: Initial problem analysis
            initial_analysis = await Runner.run(
                reasoning_orchestrator,
                f"Analyze this problem and determine appropriate reasoning approaches: {input_data}",
                context=context.create_agent_context()
            )
            
            # Store reasoning approach decisions
            await context.state_manager.save_checkpoint("reasoning_plan", initial_analysis.final_output)
            
            # Stage 2: Execute multi-reasoning analysis
            comprehensive_analysis = await Runner.run(
                reasoning_orchestrator,
                f"Now perform comprehensive multi-reasoning analysis: {input_data}",
                context=context.create_agent_context()
            )
            
            # Stage 3: Meta-reasoning about the reasoning process
            meta_reasoning = await Runner.run(
                reasoning_orchestrator,
                f"Reflect on the reasoning process used and assess the quality of conclusions for: {input_data}",
                context=context.create_agent_context()
            )
            
            final_result = {
                "problem": input_data,
                "reasoning_plan": initial_analysis.final_output,
                "comprehensive_analysis": comprehensive_analysis.final_output,
                "meta_reasoning": meta_reasoning.final_output
            }
            
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.COMPLETED,
                result=final_result,
                metadata={
                    "reasoning_services_used": ["analytical", "strategic", "systems", "causal"],
                    "meta_reasoning_applied": True
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )


# =============================================================================
# 7. PRACTICAL AGENT WITH OUTSOURCED REASONING
# =============================================================================

# Create an agent that outsources all complex reasoning
practical_agent = Agent(
    name="Practical Problem Solver",
    instructions="""
    You are a practical problem solver who focuses on implementation and execution.
    
    For any complex reasoning tasks, you delegate to the reasoning orchestrator.
    Your strengths are:
    - Breaking down complex problems into actionable steps
    - Identifying when reasoning support is needed
    - Implementing solutions based on reasoning insights
    - Managing practical constraints and resources
    
    When you encounter complex reasoning needs:
    1. Clearly define the reasoning requirements
    2. Use the reasoning orchestrator for deep analysis
    3. Translate reasoning insights into practical actions
    4. Consider implementation constraints and feasibility
    """,
    tools=[
        request_analytical_reasoning,
        request_strategic_reasoning,
        request_systems_reasoning, 
        request_causal_reasoning
    ]
)


# =============================================================================
# 8. DEMONSTRATION
# =============================================================================

async def demonstrate_reasoning_as_service():
    """Demonstrate outsourced reasoning patterns"""
    
    print("🧠 Reasoning as a Service Demo\n")
    
    # 1. Create reasoning MCP server
    print("1️⃣ Creating Reasoning MCP Server...")
    reasoning_mcp = create_reasoning_mcp_server()
    if reasoning_mcp:
        print("✅ Reasoning MCP server created with analytical, creative, and logical reasoning tools\n")
    
    # 2. Build workflow system with reasoning capabilities
    print("2️⃣ Building Workflow System with Reasoning Services...")
    system = (WorkflowSystemBuilder()
              .with_state_backend(MemoryStateBackend())
              .register_workflow(MultiReasoningWorkflow())
              .register_agent_workflow("reasoning_orchestration", reasoning_orchestrator, "Multi-reasoning coordination")
              .register_agent_workflow("practical_solving", practical_agent, "Practical problem solving with reasoning support")
              .register_agent_tool("strategic_reasoner", strategic_reasoner, "Strategic reasoning specialist")
              .register_agent_tool("systems_reasoner", systems_reasoner, "Systems thinking specialist")
              .register_agent_tool("causal_reasoner", causal_reasoner, "Causal reasoning specialist"))
    
    workflow_engine, tool_registry, event_bus = system.build()
    print("✅ Workflow system built with reasoning specialists\n")
    
    # 3. Demo: Multi-reasoning workflow
    print("3️⃣ Running Multi-Reasoning Workflow...")
    reasoning_result = await workflow_engine.execute_workflow(
        "multi_reasoning",
        "How should a tech startup approach market entry in a competitive landscape?",
        session_id="reasoning_demo"
    )
    print(f"✅ Multi-reasoning analysis completed: {reasoning_result.is_success()}")
    if reasoning_result.is_success():
        result_data = reasoning_result.result
        print(f"📊 Reasoning services used: {reasoning_result.metadata.get('reasoning_services_used')}")
        print(f"🔍 Meta-reasoning applied: {reasoning_result.metadata.get('meta_reasoning_applied')}\n")
    
    # 4. Demo: Practical agent with reasoning support
    print("4️⃣ Running Practical Agent with Reasoning Support...")
    practical_result = await workflow_engine.execute_workflow(
        "practical_solving",
        "Design a scalable architecture for a real-time collaboration platform",
        session_id="practical_demo"
    )
    print(f"✅ Practical problem solving completed: {practical_result.is_success()}\n")
    
    # 5. Demo: Create composite MCP server
    print("5️⃣ Creating Composite MCP Server...")
    composite_mcp = system.create_mcp_server()
    if composite_mcp:
        print("✅ Composite MCP server created!")
        print("📡 Available services:")
        print("   - multi_reasoning: Comprehensive multi-perspective analysis")
        print("   - reasoning_orchestration: Coordinate multiple reasoning specialists") 
        print("   - practical_solving: Practical solutions with reasoning support")
        print("\n🌟 Now any external system can access sophisticated reasoning via simple MCP calls!")
    
    print("\n🎉 Reasoning as a Service demo completed!")
    
    return workflow_engine, tool_registry, reasoning_mcp


if __name__ == "__main__":
    asyncio.run(demonstrate_reasoning_as_service())