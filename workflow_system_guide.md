# Advanced Agent Workflow System - Getting Started Guide

## Overview

We've built a sophisticated foundation for creating arbitrarily complex, reusable, and composable agent workflows. Here are the **key primitives** you need to master:

## 🔑 Core Primitives (In Order of Importance)

### 1. **State Management** - The Foundation

```python
from workflow_primitives import StateManager, StateScope, MemoryStateBackend

# Create state backend
state_backend = MemoryStateBackend()
state_manager = StateManager(state_backend)

# Use different state scopes
await state_manager.set("user_preference", value, scope=StateScope.PERSISTENT)
await state_manager.set("temp_data", value, scope=StateScope.WORKFLOW)  
await state_manager.set("shared_cache", value, scope=StateScope.GLOBAL)

# Checkpointing for long workflows
await state_manager.save_checkpoint("planning_done", plan_data)
if await state_manager.has_checkpoint("planning_done"):
    plan = await state_manager.load_checkpoint("planning_done")
```

**Why Critical:** Everything else depends on state management. Without proper state handling, you can't build persistent, resumable, or collaborative workflows.

### 2. **Workflow Engine** - The Orchestrator

```python
from workflow_primitives import WorkflowEngine, BaseWorkflow, WorkflowContext

class CustomWorkflow(BaseWorkflow):
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        # Your workflow logic here
        # Can access context.state_manager for persistence
        # Can access context.workflow_id, session_id, etc.
        pass

# Register and execute
engine = WorkflowEngine(state_backend)
engine.register_workflow(CustomWorkflow())

result = await engine.execute_workflow("custom_workflow", "input data")
```

**Why Critical:** This abstracts workflow execution, provides context, and handles metadata/persistence automatically.

### 3. **Tool Registry** - The Composability Engine

```python
from workflow_primitives import ToolRegistry

registry = ToolRegistry(workflow_engine)

# Register agents as reusable tools
registry.register_agent_as_tool("researcher", research_agent, "Expert research")
registry.register_agent_as_tool("analyst", analysis_agent, "Expert analysis")

# Create composite agents that use other agents as tools
super_agent = registry.create_composite_agent(
    name="Research Director",
    instructions="Use your research and analysis team to complete complex projects",
    tool_names=["researcher", "analyst"]
)

# Register entire workflows as tools for other agents
registry.register_workflow_as_tool("deep_research", "Run comprehensive research workflow")
```

**Why Critical:** This enables the "agents as tools" pattern and workflow composability that makes the system truly scalable.

### 4. **MCP Integration** - The Interoperability Layer

```python
# Expose your entire workflow system as MCP tools
mcp_server = create_workflow_mcp_server(workflow_engine, tool_registry)

# Now ANY system can use your workflows via MCP
# Each workflow becomes a simple tool call
```

**Why Critical:** This makes your complex workflows available as simple tools to other systems, creating a "workflow marketplace."

### 5. **Event System** - Loose Coupling

```python
from workflow_primitives import EventBus, WorkflowEvent

event_bus = EventBus()

# Subscribe to workflow events
async def handle_completion(event: WorkflowEvent):
    print(f"Workflow {event.workflow_id} completed!")

event_bus.subscribe("workflow.completed", handle_completion)

# Publish events from workflows
await event_bus.publish(WorkflowEvent(
    type="workflow.completed",
    workflow_id=context.workflow_id,
    data={"result": final_output}
))
```

**Why Critical:** Enables loose coupling between workflow components and reactive programming patterns.

## 🚀 Quick Start - Build Your First System

```python
from workflow_primitives import WorkflowSystemBuilder
from agents import Agent

# 1. Create your agents
planner = Agent(name="Planner", instructions="Create detailed plans")
executor = Agent(name="Executor", instructions="Execute tasks efficiently")

# 2. Build the system using the builder pattern
system = (WorkflowSystemBuilder()
          .register_agent_workflow("planning", planner, "Planning workflow")
          .register_agent_workflow("execution", executor, "Execution workflow")  
          .register_agent_tool("planner", planner, "Planning expertise"))

workflow_engine, tool_registry, event_bus = system.build()

# 3. Create composite workflows
director = tool_registry.create_composite_agent(
    name="Project Director",
    instructions="Orchestrate planning and execution using your tools",
    tool_names=["planner"]
)

system.register_agent_workflow("project_management", director, "Full project management")

# 4. Execute workflows
result = await workflow_engine.execute_workflow(
    "project_management", 
    "Build a customer support system",
    session_id="my_session"
)

# 5. Expose as MCP server
mcp_server = system.create_mcp_server()
```

## 📋 Essential Patterns to Master

### Pattern 1: **Stateful Workflows with Checkpointing**

Use for long-running workflows that might fail and need to resume:

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
    # Stage 1: Planning (resumable)
    if not await context.state_manager.has_checkpoint("plan"):
        plan = await self.create_plan(input_data)
        await context.state_manager.save_checkpoint("plan", plan)
    else:
        plan = await context.state_manager.load_checkpoint("plan")
    
    # Stage 2: Execution (resumable)
    if not await context.state_manager.has_checkpoint("execution"):
        result = await self.execute_plan(plan)
        await context.state_manager.save_checkpoint("execution", result)
    else:
        result = await context.state_manager.load_checkpoint("execution")
    
    return WorkflowResult(...)
```

### Pattern 2: **Parallel Execution with Error Handling**

Use when you need speed and can handle partial failures:

```python
import asyncio

# Run multiple agents in parallel
tasks = [
    Runner.run(agent1, prompt1, context=context.create_agent_context()),
    Runner.run(agent2, prompt2, context=context.create_agent_context()),
    Runner.run(agent3, prompt3, context=context.create_agent_context())
]

results = await asyncio.gather(*tasks, return_exceptions=True)

# Handle partial failures gracefully
successful_results = [r for r in results if not isinstance(r, Exception)]
```

### Pattern 3: **Agent-to-Agent Communication via Shared State**

Use when agents need to collaborate and share information:

```python
@function_tool
async def store_finding(finding: str, context: RunContextWrapper) -> str:
    workflow_context = context.context.get('workflow_context')
    findings = await workflow_context.state_manager.get('shared_findings', scope=StateScope.SESSION) or []
    findings.append(finding)
    await workflow_context.state_manager.set('shared_findings', findings, scope=StateScope.SESSION)
    return f"Stored: {finding}"

@function_tool  
async def get_findings(context: RunContextWrapper) -> str:
    workflow_context = context.context.get('workflow_context')
    findings = await workflow_context.state_manager.get('shared_findings', scope=StateScope.SESSION) or []
    return f"Current findings: {findings}"

# Give both tools to agents that need to collaborate
collaborative_agent = Agent(
    name="Collaborator",
    instructions="Use shared tools to collaborate with other agents",
    tools=[store_finding, get_findings]
)
```

### Pattern 4: **Chain of Thought with Structured Output**

Use when you need explicit reasoning traces:

```python
@dataclass
class ReasoningStep:
    thought: str
    action: str
    observation: str
    confidence: float

@dataclass  
class ChainOfThought:
    steps: List[ReasoningStep]
    final_answer: str
    overall_confidence: float

reasoning_agent = Agent(
    name="Reasoner",
    instructions="""
    Think step by step. For each step provide:
    1. Your thought process
    2. The action you're taking  
    3. What you observed
    4. Your confidence level
    """,
    output_type=ChainOfThought
)
```

## 🎯 Next Steps

1. **Start Simple**: Begin with the quick start example above
2. **Add State**: Implement checkpointing for your workflows  
3. **Make it Parallel**: Add parallel execution where appropriate
4. **Enable Collaboration**: Add shared state tools for agent communication
5. **Go Composite**: Create meta-agents that orchestrate other agents
6. **Expose via MCP**: Make your workflows available to other systems
7. **Scale Up**: Build increasingly complex multi-stage workflows

## 🔧 Production Considerations

### For Production Use:

1. **Replace MemoryStateBackend** with Redis/PostgreSQL backend
2. **Add Error Recovery**: Implement retry policies and circuit breakers  
3. **Add Observability**: Comprehensive logging and metrics
4. **Implement Rate Limiting**: Control API usage and costs
5. **Add Authentication**: Secure your MCP endpoints
6. **Scale Horizontally**: Use message queues for workflow distribution

### Example Production State Backend:

```python
class RedisStateBackend(StateBackend):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: StateKey) -> Optional[Any]:
        data = await self.redis.get(str(key))
        return json.loads(data) if data else None
    
    async def set(self, key: StateKey, value: Any, ttl: Optional[int] = None) -> None:
        data = json.dumps(value)
        if ttl:
            await self.redis.setex(str(key), ttl, data)
        else:
            await self.redis.set(str(key), data)
```

## 💡 Key Insights

- **State First**: Always design your state management strategy before building workflows
- **Compose Everything**: Make every workflow exposable as a tool for other workflows  
- **Design for Failure**: Use checkpointing, parallel execution with error handling
- **Think in Layers**: Core agents → Workflows → Meta-orchestrators → MCP exposure
- **Start Small**: Begin with simple workflows and gradually increase complexity

This system can handle arbitrarily complex workflows while maintaining clean abstractions and composability. The key is progressive enhancement - start simple and add complexity incrementally.