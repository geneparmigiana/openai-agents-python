# OpenAI Agents SDK

The OpenAI Agents SDK is a lightweight yet powerful framework for building multi-agent workflows. It is provider-agnostic, supporting the OpenAI Responses and Chat Completions APIs, as well as 100+ other LLMs.

<img src="https://cdn.openai.com/API/docs/images/orchestration.png" alt="Image of the Agents Tracing UI" style="max-height: 803px;">

> [!NOTE]
> Looking for the JavaScript/TypeScript version? Check out [Agents SDK JS/TS](https://github.com/openai/openai-agents-js).

### Core concepts:

1. [**Agents**](https://openai.github.io/openai-agents-python/agents): LLMs configured with instructions, tools, guardrails, and handoffs
2. [**Handoffs**](https://openai.github.io/openai-agents-python/handoffs/): A specialized tool call used by the Agents SDK for transferring control between agents
3. [**Guardrails**](https://openai.github.io/openai-agents-python/guardrails/): Configurable safety checks for input and output validation
4. [**Tracing**](https://openai.github.io/openai-agents-python/tracing/): Built-in tracking of agent runs, allowing you to view, debug and optimize your workflows

Explore the [examples](examples) directory to see the SDK in action, and read our [documentation](https://openai.github.io/openai-agents-python/) for more details.

## Get started

1. Set up your Python environment

```
python -m venv env
source env/bin/activate
```

2. Install Agents SDK

```
pip install openai-agents
```

For voice support, install with the optional `voice` group: `pip install 'openai-agents[voice]'`.

## Hello world example

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

(_If running this, ensure you set the `OPENAI_API_KEY` environment variable_)

(_For Jupyter notebook users, see [hello_world_jupyter.py](examples/basic/hello_world_jupyter.py)_)

## Handoffs example

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    asyncio.run(main())
```

## Functions example

```python
import asyncio

from agents import Agent, Runner, function_tool


@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."


agent = Agent(
    name="Hello world",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)
    # The weather in Tokyo is sunny.


if __name__ == "__main__":
    asyncio.run(main())
```

## The agent loop

When you call `Runner.run()`, we run a loop until we get a final output.

1. We call the LLM, using the model and settings on the agent, and the message history.
2. The LLM returns a response, which may include tool calls.
3. If the response has a final output (see below for more on this), we return it and end the loop.
4. If the response has a handoff, we set the agent to the new agent and go back to step 1.
5. We process the tool calls (if any) and append the tool responses messages. Then we go to step 1.

There is a `max_turns` parameter that you can use to limit the number of times the loop executes.

### Final output

Final output is the last thing the agent produces in the loop.

1.  If you set an `output_type` on the agent, the final output is when the LLM returns something of that type. We use [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) for this.
2.  If there's no `output_type` (i.e. plain text responses), then the first LLM response without any tool calls or handoffs is considered as the final output.

As a result, the mental model for the agent loop is:

1. If the current agent has an `output_type`, the loop runs until the agent produces structured output matching that type.
2. If the current agent does not have an `output_type`, the loop runs until the current agent produces a message without any tool calls/handoffs.

## Common agent patterns

The Agents SDK is designed to be highly flexible, allowing you to model a wide range of LLM workflows including deterministic flows, iterative loops, and more. See examples in [`examples/agent_patterns`](examples/agent_patterns).

## Tracing

The Agents SDK automatically traces your agent runs, making it easy to track and debug the behavior of your agents. Tracing is extensible by design, supporting custom spans and a wide variety of external destinations, including [Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents), [AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk), [Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk), [Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration), and [Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent). For more details about how to customize or disable tracing, see [Tracing](http://openai.github.io/openai-agents-python/tracing), which also includes a larger list of [external tracing processors](http://openai.github.io/openai-agents-python/tracing/#external-tracing-processors-list).

## Development (only needed if you need to edit the SDK/examples)

0. Ensure you have [`uv`](https://docs.astral.sh/uv/) installed.

```bash
uv --version
```

1. Install dependencies

```bash
make sync
```

2. (After making changes) lint/test

```
make tests  # run tests
make mypy   # run typechecker
make lint   # run linter
```

## Acknowledgements

We'd like to acknowledge the excellent work of the open-source community, especially:

-   [Pydantic](https://docs.pydantic.dev/latest/) (data validation) and [PydanticAI](https://ai.pydantic.dev/) (advanced agent framework)
-   [MkDocs](https://github.com/squidfunk/mkdocs-material)
-   [Griffe](https://github.com/mkdocstrings/griffe)
-   [uv](https://github.com/astral-sh/uv) and [ruff](https://github.com/astral-sh/ruff)

We're committed to continuing to build the Agents SDK as an open source framework so others in the community can expand on our approach.

# Self-Evolving Data Intelligence System

**Build data systems that learn and improve from every query**

## Overview

This framework enables you to build data intelligence systems that don't just answer queries—they **automatically evolve** to handle increasingly complex requests. Every user interaction teaches the system what it needs to become better.

### The Core Innovation

Traditional data systems are static: they answer the queries they're designed for, but struggle with new complexity. This framework creates **self-evolving systems** that:

- ✅ **Answer immediate queries** when possible
- 🧠 **Learn from every interaction** to identify system limitations  
- 🛠️ **Automatically generate improvements** (DBT models, pipelines, capabilities)
- 🚀 **Execute async work** to expand system capabilities
- 📈 **Become exponentially more capable** over time

### The Result

```
Query 1: "Buildings with >5 violations?" → 2500ms (slow, triggers improvements)
...system automatically creates DBT models, indexes, optimizations...
Query N: "Buildings with >5 violations?" → 200ms (fast, benefits from learning)
```

**Same query, 12.5x faster, zero manual intervention.**

## Core Architecture

### 1. Multi-Modal Reasoning Agents

Different types of reasoning require specialized agents:

```python
# Understanding: Natural language → Structured requirements
understanding_agent = Agent(
    instructions="Parse business queries into structured requirements",
    output_type=QueryUnderstanding
)

# Execution: Run queries, assess performance
data_execution_agent = Agent(
    instructions="Execute queries and identify performance bottlenecks",
    tools=[sql_execution_tool, performance_assessment_tool]
)

# Process Improvement: Design system enhancements  
process_improvement_agent = Agent(
    instructions="Create improvement tasks based on system limitations",
    tools=[create_improvement_task, assess_system_capabilities]
)

# Code Generation: Build the improvements
dbt_agent = Agent(
    instructions="Generate data models and transformations",
    tools=[generate_dbt_model, schedule_deployment]
)
```

### 2. Dynamic Workflow Generation

Workflows **emerge** from query complexity rather than being pre-defined:

```python
# Stage 1: Always - understand the query
understanding = await understanding_agent.run(user_query)

# Stage 2: Conditional - execute if possible
if understanding.complexity in [SIMPLE, MODERATE]:
    result = await data_execution_agent.run(understanding)
    
    # Dynamic complexity adjustment based on actual performance
    if performance_issues_detected(result):
        understanding.complexity = COMPLEX

# Stage 3: Conditional - create improvements if needed  
if understanding.complexity in [COMPLEX, IMPOSSIBLE]:
    improvements = await process_improvement_agent.run(understanding, result)
    
    # Stage 4: Dynamic - spawn async work based on improvements
    for task in improvements:
        if task.work_type == ASYNC_IMPROVEMENT:
            await spawn_background_workflow(task)
```

### 3. Multi-Temporal State Management

The system operates across multiple timescales with different state scopes:

```python
# Immediate: What's happening in this query?
await state.set("current_execution_metrics", metrics, scope=WORKFLOW)

# Learning: What patterns are we seeing?  
await state.set("query_patterns", patterns, scope=PERSISTENT)

# Capabilities: What can the system do?
await state.set("system_capabilities", capabilities, scope=GLOBAL)

# Evolution: How is the system improving?
await state.set("improvement_history", history, scope=PERSISTENT)
```

### 4. Capability-Driven Complexity Assessment

Query complexity isn't static—it depends on current system capabilities:

```python
@dataclass
class QueryUnderstanding:
    complexity: QueryComplexity  # SIMPLE | MODERATE | COMPLEX | IMPOSSIBLE
    required_capabilities: List[str]
    missing_capabilities: List[str]
    
    def assess_complexity(self, system_capabilities: Dict[str, bool]) -> QueryComplexity:
        if not self.missing_capabilities:
            return QueryComplexity.SIMPLE
        elif can_workaround(self.missing_capabilities):
            return QueryComplexity.MODERATE  
        elif can_build(self.missing_capabilities):
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.IMPOSSIBLE
```

## Scaling to Arbitrary Complexity

### Horizontal Scaling: Domain Specialization

Create specialized intelligence systems for different domains:

```python
# Financial Intelligence
financial_system = DataIntelligenceWorkflow(
    domain="finance",
    agents=[
        financial_understanding_agent,
        regulatory_compliance_agent,  
        risk_assessment_agent,
        trading_execution_agent
    ],
    capabilities=[
        "financial_data_access",
        "regulatory_reporting", 
        "risk_modeling",
        "market_data_integration"
    ]
)

# Real Estate Intelligence  
real_estate_system = DataIntelligenceWorkflow(
    domain="real_estate",
    agents=[
        property_understanding_agent,
        market_analysis_agent,
        violation_tracking_agent,
        zoning_compliance_agent
    ],
    capabilities=[
        "property_data_access",
        "market_analytics",
        "compliance_monitoring",
        "geospatial_analysis"
    ]
)
```

### Vertical Scaling: Capability Layers

Build capabilities in layers of increasing sophistication:

```python
# Layer 1: Basic Data Access
basic_capabilities = [
    "sql_query_execution",
    "data_source_connectivity", 
    "basic_aggregations"
]

# Layer 2: Performance Optimization
optimization_capabilities = [
    "query_performance_assessment",
    "index_optimization",
    "materialized_view_creation"
]

# Layer 3: Advanced Analytics
analytics_capabilities = [
    "statistical_analysis",
    "trend_identification", 
    "correlation_analysis"
]

# Layer 4: Machine Learning
ml_capabilities = [
    "predictive_modeling",
    "anomaly_detection",
    "recommendation_systems"
]

# Layer 5: Autonomous Operations
autonomous_capabilities = [
    "self_optimization",
    "proactive_maintenance",
    "capability_expansion_planning"
]
```

### Recursive Scaling: Systems Using Systems

Expose entire intelligence systems as MCP tools for composition:

```python
# Core real estate intelligence
core_system = DataIntelligenceWorkflow(name="core_real_estate")

# Compliance intelligence that uses core system
compliance_system = DataIntelligenceWorkflow(
    name="compliance_intelligence",
    tools=[
        mcp_tool("core_real_estate", "query_building_data"),
        mcp_tool("core_real_estate", "analyze_violation_patterns"),
        compliance_specific_tools
    ]
)

# Investment intelligence that uses both systems  
investment_system = DataIntelligenceWorkflow(
    name="investment_intelligence", 
    tools=[
        mcp_tool("core_real_estate", "market_analysis"),
        mcp_tool("compliance_intelligence", "risk_assessment"),
        investment_specific_tools
    ]
)
```

### Network Scaling: Multi-Organization Learning

Systems can learn from and contribute to ecosystem-wide intelligence:

```python
# Cross-system learning network
class IntelligenceNetwork:
    async def share_capability(self, capability: Capability):
        """Share successful capability with network"""
        await self.network.publish(CapabilityShareEvent(
            capability=capability,
            performance_metrics=capability.performance_data,
            implementation_guide=capability.implementation
        ))
    
    async def adopt_capability(self, capability: Capability):
        """Adopt proven capability from network"""
        if self.should_adopt(capability):
            await self.implement_capability(capability)
            await self.track_adoption_success(capability)
```

## Implementation Guide

### Phase 1: Foundation (Week 1-2)

**Core Query Processing**

```python
# 1. Set up basic architecture
system = (WorkflowSystemBuilder()
          .with_state_backend(MemoryStateBackend())  # Start simple
          .register_workflow(DataIntelligenceWorkflow()))

# 2. Implement understanding agent
understanding_agent = Agent(
    name="Query Understanding Agent",
    instructions="""
    Analyze business queries and determine:
    1. Intent and entities involved
    2. Required metrics and calculations  
    3. Current system capabilities vs requirements
    4. Query complexity based on capability gaps
    """,
    output_type=QueryUnderstanding
)

# 3. Add basic execution capabilities
@function_tool
async def sql_execution_tool(query: str) -> str:
    """Execute SQL against data warehouse"""
    # Connect to your actual data sources
    # Track performance metrics
    # Identify bottlenecks
    
# 4. Implement performance assessment
@function_tool  
async def performance_assessment_tool(result: str) -> str:
    """Analyze query performance and optimization opportunities"""
    # Parse execution plans
    # Identify missing indexes
    # Suggest improvements
```

### Phase 2: Evolution Engine (Week 3-4)

**Self-Improvement Capabilities**

```python
# 1. Process improvement agent
process_improvement_agent = Agent(
    instructions="""
    When queries are slow/complex:
    1. Identify root causes (missing indexes, metrics, etc.)
    2. Design improvement tasks  
    3. Prioritize based on impact and effort
    4. Create concrete work items for execution
    """,
    tools=[create_improvement_task, assess_system_capabilities]
)

# 2. DBT code generation agent
dbt_agent = Agent(
    instructions="""
    Generate data transformations to improve query performance:
    1. Pre-calculate expensive aggregations
    2. Create denormalized tables for common queries
    3. Build incremental models for efficiency
    4. Add proper indexing strategies
    """,
    tools=[generate_dbt_model, schedule_deployment]
)

# 3. Async task coordination
class ImprovementTaskExecutor:
    async def execute_improvement(self, task: ImprovementTask):
        if task.type == "dbt_model":
            await self.dbt_agent.generate_and_deploy(task)
        elif task.type == "index_creation":
            await self.database_agent.create_indexes(task)
        elif task.type == "pipeline_optimization":
            await self.pipeline_agent.optimize(task)
```

### Phase 3: Learning & Adaptation (Week 5-6)

**Pattern Recognition & Capability Management**

```python
# 1. Query pattern analysis
class QueryPatternAnalyzer:
    async def analyze_patterns(self) -> List[QueryPattern]:
        """Identify common query types and optimization opportunities"""
        # Analyze historical queries
        # Identify frequently requested entities/metrics
        # Detect performance bottlenecks  
        # Suggest proactive improvements

# 2. Capability gap identification  
class CapabilityAnalyzer:
    async def identify_gaps(self) -> List[CapabilityGap]:
        """Find differences between user needs and system capabilities"""
        # Compare required vs available capabilities
        # Prioritize gaps by user impact
        # Estimate implementation effort

# 3. Automatic improvement prioritization
class ImprovementPrioritizer:
    def prioritize_improvements(self, 
                              gaps: List[CapabilityGap],
                              patterns: List[QueryPattern]) -> List[ImprovementTask]:
        """Intelligently prioritize system improvements"""
        # Weight by user impact
        # Consider implementation effort  
        # Account for capability dependencies
        # Optimize for maximum system evolution
```

### Phase 4: Production & Scale (Week 7-8)

**Production Deployment & MCP Integration**

```python
# 1. Production state backends
production_state = PostgreSQLStateBackend(
    connection_string="postgresql://...",
    capability_table="system_capabilities",
    pattern_table="query_patterns", 
    improvement_table="improvement_tasks"
)

# 2. Distributed task execution
task_executor = CeleryTaskExecutor(
    broker="redis://...",
    workers=["dbt_worker", "database_worker", "ml_worker"]
)

# 3. MCP server deployment
mcp_server = system.create_mcp_server()
mcp_server.serve(
    host="0.0.0.0",
    port=8000,
    auth=BearerTokenAuth(token="...")
)

# 4. Monitoring & observability
system.add_trace_processor(DatadogTraceProcessor())
system.add_metric_collector(PrometheusMetrics())
system.add_alerting(SlackAlerter(webhook="..."))
```

## Key Patterns & Examples

### Pattern 1: Performance-Driven Evolution

```python
# User query triggers performance analysis
query = "SELECT COUNT(*) FROM buildings b JOIN violations v ON b.id = v.building_id WHERE v.count > 5"

# System detects: 2500ms execution time, missing indexes
performance_issues = [
    "Missing index on violations.building_id",
    "No pre-calculated violation counts", 
    "Complex join on large tables"
]

# System creates improvement tasks
improvements = [
    ImprovementTask(
        description="Create building_violation_metrics materialized view",
        creates_capabilities=["fast_building_violation_queries"],
        estimated_impact="10x query performance improvement"
    )
]

# System executes improvements asynchronously
# Future queries benefit automatically
```

### Pattern 2: Capability-Driven Routing

```python
# Query understanding checks current capabilities
understanding = QueryUnderstanding(
    intent="Predictive risk analysis",
    required_capabilities=["ml_pipeline", "feature_engineering", "model_serving"],
    missing_capabilities=["ml_pipeline", "feature_engineering"]
)

# System routes based on capability gaps
if understanding.missing_capabilities:
    # Route to improvement workflow
    workflow = ImprovementWorkflow(understanding)
else:
    # Route to execution workflow  
    workflow = ExecutionWorkflow(understanding)
```

### Pattern 3: Recursive System Composition

```python
# Building violation intelligence system
violation_system = DataIntelligenceWorkflow(
    name="violation_intelligence",
    capabilities=["violation_tracking", "compliance_monitoring"]
)

# Investment analysis system that uses violation intelligence
investment_system = DataIntelligenceWorkflow(
    name="investment_intelligence",
    tools=[
        mcp_tool("violation_intelligence", "assess_property_risk"),
        mcp_tool("market_data", "get_comparable_sales"),
        investment_analysis_tools
    ]
)

# Portfolio management system that uses investment intelligence
portfolio_system = DataIntelligenceWorkflow(
    name="portfolio_intelligence", 
    tools=[
        mcp_tool("investment_intelligence", "analyze_opportunity"),
        mcp_tool("financial_planning", "optimize_allocation"),
        portfolio_management_tools
    ]
)
```

## Getting Started

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd self-evolving-data-intelligence

# Install dependencies
pip install -e .

# Or using uv (recommended)
uv sync
```

### 2. Quick Start

```python
from agents import Agent, function_tool
from workflow_primitives import WorkflowSystemBuilder, DataIntelligenceWorkflow

# Create your first self-evolving data system
system = (WorkflowSystemBuilder()
          .with_state_backend(MemoryStateBackend())
          .register_workflow(DataIntelligenceWorkflow())
          .build())

# Process a query
result = await system.execute_workflow(
    "data_intelligence",
    "How many buildings have had more than 5 DOB violations?",
    session_id="demo"
)

print(f"Query result: {result.result}")
print(f"Improvements triggered: {len(result.metadata.get('improvement_tasks', []))}")
```

### 3. Configuration

```python
# config.py
SYSTEM_CONFIG = {
    # Data sources
    "databases": {
        "primary": "postgresql://user:pass@host:5432/db",
        "warehouse": "snowflake://account.region/database"
    },
    
    # Model settings
    "models": {
        "understanding": "gpt-4o",           # Fast, structured output
        "improvement": "o1-preview",         # Deep reasoning
        "code_generation": "gpt-4o"         # Code generation
    },
    
    # State management
    "state": {
        "backend": "postgresql",
        "connection": "postgresql://...",
        "capability_persistence": True
    },
    
    # Async execution
    "execution": {
        "backend": "celery",
        "broker": "redis://localhost:6379",
        "workers": ["dbt", "database", "ml"]
    }
}
```

### 4. Add Your Domain

```python
# Create domain-specific understanding agent
your_domain_agent = Agent(
    name="Your Domain Understanding Agent",
    instructions="""
    You are an expert in [YOUR DOMAIN].
    
    Analyze queries about [YOUR DOMAIN] and determine:
    1. What data sources are needed
    2. What calculations/metrics are required  
    3. Current system capabilities vs requirements
    4. Complexity based on available capabilities
    """,
    output_type=QueryUnderstanding
)

# Add domain-specific tools
@function_tool
async def your_domain_data_tool(query: str) -> str:
    """Execute domain-specific data operations"""
    # Your implementation here

# Register with system
system.register_agent_tool("your_domain_agent", your_domain_agent)
```

## Advanced Concepts

### Multi-System Orchestration

```python
# Create specialized systems for different aspects
core_data_system = DataIntelligenceWorkflow(name="core_data")
analytics_system = DataIntelligenceWorkflow(name="analytics")  
ml_system = DataIntelligenceWorkflow(name="machine_learning")

# Create meta-orchestrator that coordinates systems
meta_system = Agent(
    name="Meta Orchestrator",
    instructions="""
    You coordinate multiple specialized intelligence systems.
    
    Route queries to appropriate systems based on:
    1. Query type and complexity
    2. Required capabilities 
    3. System specializations
    4. Performance characteristics
    """,
    tools=[
        mcp_tool("core_data", "process_query"),
        mcp_tool("analytics", "analyze_patterns"), 
        mcp_tool("machine_learning", "predict_outcomes")
    ]
)
```

### Capability Marketplace

```python
# Publish capabilities to marketplace
class CapabilityMarketplace:
    async def publish_capability(self, capability: Capability):
        """Make capability available to other systems"""
        await self.registry.publish(CapabilityListing(
            name=capability.name,
            description=capability.description,
            mcp_endpoint=capability.mcp_endpoint,
            performance_metrics=capability.metrics,
            cost_model=capability.pricing
        ))
    
    async def discover_capabilities(self, requirements: List[str]) -> List[Capability]:
        """Find capabilities that match requirements"""
        return await self.registry.search(requirements)
```

### System Evolution Metrics

```python
# Track how the system evolves over time
class EvolutionTracker:
    def track_capability_growth(self):
        """Monitor capability acquisition over time"""
        
    def track_performance_improvement(self): 
        """Monitor query performance improvements"""
        
    def track_user_satisfaction(self):
        """Monitor user experience improvements"""
        
    def track_cost_efficiency(self):
        """Monitor cost per query trends"""
```

## Contributing

This framework is designed to be extensible. Key extension points:

- **Agents**: Add domain-specific understanding and execution agents
- **Tools**: Add new data sources, analysis capabilities, code generators  
- **Workflows**: Create specialized workflows for different use cases
- **State Backends**: Add new persistence layers for different scales
- **MCP Servers**: Expose new capabilities for system composition

## Architecture Principles

1. **Every query is a learning opportunity** - Build feedback loops everywhere
2. **Multi-modal reasoning separation** - Different agents for different thinking  
3. **Dynamic workflow generation** - Structure emerges from complexity
4. **Multi-temporal state management** - Different data has different lifecycles
5. **Composability through MCP** - Enable recursive system improvement
6. **Capability-driven evolution** - System grows based on actual needs
7. **Async improvement execution** - Don't block users while improving
8. **Performance-driven optimization** - Use real metrics to guide improvements

## License

MIT License - see LICENSE file for details.

---

**Start simple, evolve continuously, compose infinitely.**
