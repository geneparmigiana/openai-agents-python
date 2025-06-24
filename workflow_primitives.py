"""
Core Primitives for Advanced Agent Workflow System

This module defines the foundational abstractions and implementations
that everything else will build upon.
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, AsyncIterator
from contextlib import asynccontextmanager

import agents
from agents import Agent, Runner, function_tool, RunContextWrapper


# =============================================================================
# 1. STATE MANAGEMENT PRIMITIVES (Most Critical)
# =============================================================================

class StateScope(Enum):
    """Defines the scope/lifetime of state"""
    SESSION = "session"      # Lives for one session/conversation
    WORKFLOW = "workflow"    # Lives for one workflow execution  
    PERSISTENT = "persistent" # Lives across sessions
    GLOBAL = "global"       # Shared across all workflows


@dataclass
class StateKey:
    """Typed key for state access"""
    scope: StateScope
    namespace: str
    key: str
    
    def __str__(self) -> str:
        return f"{self.scope.value}:{self.namespace}:{self.key}"


class StateBackend(ABC):
    """Abstract interface for state persistence"""
    
    @abstractmethod
    async def get(self, key: StateKey) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: StateKey, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: StateKey) -> None:
        pass
    
    @abstractmethod
    async def list_keys(self, scope: StateScope, namespace: str = "*") -> List[StateKey]:
        pass


class MemoryStateBackend(StateBackend):
    """In-memory state backend for development/testing"""
    
    def __init__(self):
        self._storage: Dict[str, Any] = {}
    
    async def get(self, key: StateKey) -> Optional[Any]:
        return self._storage.get(str(key))
    
    async def set(self, key: StateKey, value: Any, ttl: Optional[int] = None) -> None:
        self._storage[str(key)] = value
    
    async def delete(self, key: StateKey) -> None:
        self._storage.pop(str(key), None)
    
    async def list_keys(self, scope: StateScope, namespace: str = "*") -> List[StateKey]:
        keys = []
        prefix = f"{scope.value}:{namespace}:" if namespace != "*" else f"{scope.value}:"
        for key_str in self._storage.keys():
            if key_str.startswith(prefix):
                parts = key_str.split(":", 2)
                keys.append(StateKey(scope, parts[1], parts[2]))
        return keys


class StateManager:
    """High-level state management interface"""
    
    def __init__(self, backend: StateBackend, default_namespace: str = "default"):
        self.backend = backend
        self.default_namespace = default_namespace
    
    async def get(self, key: str, scope: StateScope = StateScope.WORKFLOW, 
                 namespace: Optional[str] = None) -> Optional[Any]:
        state_key = StateKey(scope, namespace or self.default_namespace, key)
        return await self.backend.get(state_key)
    
    async def set(self, key: str, value: Any, scope: StateScope = StateScope.WORKFLOW,
                 namespace: Optional[str] = None, ttl: Optional[int] = None) -> None:
        state_key = StateKey(scope, namespace or self.default_namespace, key)
        await self.backend.set(state_key, value, ttl)
    
    async def has_checkpoint(self, checkpoint_name: str) -> bool:
        value = await self.get(f"checkpoint:{checkpoint_name}")
        return value is not None
    
    async def save_checkpoint(self, checkpoint_name: str, data: Any) -> None:
        await self.set(f"checkpoint:{checkpoint_name}", data)
    
    async def load_checkpoint(self, checkpoint_name: str) -> Optional[Any]:
        return await self.get(f"checkpoint:{checkpoint_name}")


# =============================================================================
# 2. WORKFLOW DEFINITION PRIMITIVES
# =============================================================================

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowContext:
    """Context passed to all workflow operations"""
    workflow_id: str
    session_id: str
    user_id: Optional[str]
    state_manager: StateManager
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def create_agent_context(self) -> Dict[str, Any]:
        """Create context for agent execution"""
        return {
            'workflow_context': self,
            'state_manager': self.state_manager,
            'metadata': self.metadata
        }


@dataclass 
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    
    def is_success(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED


class BaseWorkflow(ABC):
    """Base class for all workflows"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute the workflow"""
        pass
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for input validation"""
        return {"type": "object"}  # Override in subclasses
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return JSON schema for output validation"""
        return {"type": "object"}  # Override in subclasses


# =============================================================================
# 3. AGENT WORKFLOW IMPLEMENTATION
# =============================================================================

class AgentWorkflow(BaseWorkflow):
    """Workflow that uses OpenAI Agents"""
    
    def __init__(self, name: str, agent: Agent, description: str = ""):
        super().__init__(name, description)
        self.agent = agent
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute workflow using the configured agent"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create agent context
            agent_context = context.create_agent_context()
            
            # Run the agent
            result = await Runner.run(
                self.agent, 
                str(input_data),
                context=agent_context
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.COMPLETED,
                result=result.final_output,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )


# =============================================================================
# 4. WORKFLOW ORCHESTRATION ENGINE
# =============================================================================

class WorkflowEngine:
    """Core engine for executing workflows"""
    
    def __init__(self, state_backend: StateBackend):
        self.state_manager = StateManager(state_backend)
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
    
    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """Register a workflow for execution"""
        self.workflows[workflow.name] = workflow
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        input_data: Any,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a workflow by name"""
        
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        workflow_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            session_id=session_id,
            user_id=user_id,
            state_manager=self.state_manager,
            metadata=metadata or {}
        )
        
        # Store workflow execution info
        await self.state_manager.set(
            f"workflow:{workflow_id}:info",
            {
                "name": workflow_name,
                "session_id": session_id,
                "user_id": user_id,
                "started_at": datetime.now().isoformat(),
                "status": WorkflowStatus.RUNNING.value
            },
            scope=StateScope.PERSISTENT
        )
        
        try:
            result = await workflow.execute(input_data, context)
            
            # Update workflow status
            await self.state_manager.set(
                f"workflow:{workflow_id}:result", 
                result.__dict__,
                scope=StateScope.PERSISTENT
            )
            
            return result
            
        except Exception as e:
            error_result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )
            
            await self.state_manager.set(
                f"workflow:{workflow_id}:result",
                error_result.__dict__,
                scope=StateScope.PERSISTENT
            )
            
            raise


# =============================================================================
# 5. TOOL REGISTRY FOR COMPOSABILITY  
# =============================================================================

class ToolRegistry:
    """Registry for managing reusable tools and agent-tools"""
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.workflow_engine = workflow_engine
        self.tools: Dict[str, Any] = {}
        self.agent_tools: Dict[str, Any] = {}
    
    def register_function_tool(self, name: str, tool_func: Callable) -> None:
        """Register a function as a tool"""
        self.tools[name] = tool_func
    
    def register_agent_as_tool(
        self, 
        name: str, 
        agent: Agent, 
        description: str,
        output_extractor: Optional[Callable] = None
    ) -> None:
        """Register an agent as a reusable tool"""
        self.agent_tools[name] = agent.as_tool(name, description, output_extractor)
    
    def register_workflow_as_tool(self, workflow_name: str, description: str) -> None:
        """Register a workflow as a tool"""
        
        @function_tool
        async def workflow_tool(
            input_data: str,
            context: RunContextWrapper[Dict[str, Any]]
        ) -> str:
            """Execute workflow as a tool"""
            workflow_context = context.context.get('workflow_context')
            result = await self.workflow_engine.execute_workflow(
                workflow_name,
                input_data,
                session_id=workflow_context.session_id if workflow_context else None
            )
            
            if result.is_success():
                return str(result.result)
            else:
                return f"Workflow failed: {result.error}"
        
        # Set the description on the tool's docstring
        workflow_tool.__doc__ = description
        
        self.tools[workflow_name] = workflow_tool
    
    def get_tools_for_agent(self, tool_names: List[str]) -> List[Any]:
        """Get tools for agent creation"""
        tools = []
        for name in tool_names:
            if name in self.tools:
                tools.append(self.tools[name])
            elif name in self.agent_tools:
                tools.append(self.agent_tools[name])
        return tools
    
    def create_composite_agent(
        self, 
        name: str, 
        instructions: str,
        tool_names: List[str]
    ) -> Agent:
        """Create an agent with specified tools"""
        tools = self.get_tools_for_agent(tool_names)
        return Agent(
            name=name,
            instructions=instructions,
            tools=tools
        )


# =============================================================================
# 6. EVENT SYSTEM FOR LOOSE COUPLING
# =============================================================================

@dataclass
class WorkflowEvent:
    """Event in the workflow system"""
    type: str
    workflow_id: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


EventHandler = Callable[[WorkflowEvent], None]


class EventBus:
    """Simple event bus for workflow coordination"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to events of a given type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def publish(self, event: WorkflowEvent) -> None:
        """Publish an event to all subscribers"""
        if event.type in self.handlers:
            for handler in self.handlers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")


# =============================================================================
# 7. MCP INTEGRATION LAYER
# =============================================================================

def create_workflow_mcp_server(workflow_engine: WorkflowEngine, tool_registry: ToolRegistry):
    """Create an MCP server that exposes workflows as tools"""
    
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP not available - install with: pip install mcp")
        return None
    
    mcp = FastMCP("Workflow Engine Server")
    
    # Expose each workflow as an MCP tool
    for workflow_name, workflow in workflow_engine.workflows.items():
        
        def create_workflow_endpoint(wf_name: str, wf: BaseWorkflow):
            @mcp.tool()
            async def workflow_endpoint(input_data: str, session_id: Optional[str] = None) -> str:
                f"""Execute {wf_name}: {wf.description}"""
                try:
                    result = await workflow_engine.execute_workflow(
                        wf_name, 
                        input_data, 
                        session_id=session_id
                    )
                    
                    if result.is_success():
                        return json.dumps({
                            "success": True,
                            "result": result.result,
                            "workflow_id": result.workflow_id
                        })
                    else:
                        return json.dumps({
                            "success": False,
                            "error": result.error,
                            "workflow_id": result.workflow_id
                        })
                        
                except Exception as e:
                    return json.dumps({
                        "success": False,
                        "error": str(e)
                    })
            
            # Set function doc dynamically
            workflow_endpoint.__doc__ = f"Execute {wf_name}: {wf.description}"
            
            return workflow_endpoint
        
        # Create and register the endpoint
        endpoint = create_workflow_endpoint(workflow_name, workflow)
        
    return mcp


# =============================================================================
# 8. PUTTING IT ALL TOGETHER - SYSTEM BUILDER
# =============================================================================

class WorkflowSystemBuilder:
    """Builder for creating a complete workflow system"""
    
    def __init__(self):
        self.state_backend = MemoryStateBackend()
        self.workflow_engine = WorkflowEngine(self.state_backend)
        self.tool_registry = ToolRegistry(self.workflow_engine)
        self.event_bus = EventBus()
    
    def with_state_backend(self, backend: StateBackend) -> 'WorkflowSystemBuilder':
        """Use a custom state backend"""
        self.state_backend = backend
        self.workflow_engine = WorkflowEngine(backend)
        self.tool_registry = ToolRegistry(self.workflow_engine)
        return self
    
    def register_workflow(self, workflow: BaseWorkflow) -> 'WorkflowSystemBuilder':
        """Register a workflow"""
        self.workflow_engine.register_workflow(workflow)
        return self
    
    def register_agent_workflow(
        self, 
        name: str, 
        agent: Agent, 
        description: str = ""
    ) -> 'WorkflowSystemBuilder':
        """Register an agent as a workflow"""
        workflow = AgentWorkflow(name, agent, description)
        self.workflow_engine.register_workflow(workflow)
        return self
    
    def register_agent_tool(
        self, 
        name: str, 
        agent: Agent, 
        description: str
    ) -> 'WorkflowSystemBuilder':
        """Register an agent as a reusable tool"""
        self.tool_registry.register_agent_as_tool(name, agent, description)
        return self
    
    def create_mcp_server(self):
        """Create MCP server for the workflow system"""
        return create_workflow_mcp_server(self.workflow_engine, self.tool_registry)
    
    def build(self) -> tuple[WorkflowEngine, ToolRegistry, EventBus]:
        """Build and return the complete system"""
        return self.workflow_engine, self.tool_registry, self.event_bus


# =============================================================================
# 9. EXAMPLE USAGE
# =============================================================================

async def example_usage():
    """Example of how to use the workflow system"""
    
    # 1. Create some basic agents
    planner_agent = Agent(
        name="Planner",
        instructions="Create detailed plans for achieving goals. Break down complex tasks into steps."
    )
    
    executor_agent = Agent(
        name="Executor", 
        instructions="Execute specific tasks efficiently. Focus on getting things done."
    )
    
    # 2. Build the workflow system
    system = (WorkflowSystemBuilder()
              .register_agent_workflow("planning", planner_agent, "Create execution plans")
              .register_agent_workflow("execution", executor_agent, "Execute tasks")
              .register_agent_tool("planner", planner_agent, "Plan complex tasks"))
    
    workflow_engine, tool_registry, event_bus = system.build()
    
    # 3. Create a composite agent that can use other agents as tools
    composite_agent = tool_registry.create_composite_agent(
        name="Project Manager",
        instructions="You manage projects by using planning and execution tools.",
        tool_names=["planner"]
    )
    
    # 4. Register composite workflow
    system.register_agent_workflow("project_management", composite_agent, "Manage complex projects")
    
    # 5. Execute workflows
    result = await workflow_engine.execute_workflow(
        "planning",
        "Plan a system for managing customer support tickets",
        session_id="demo_session"
    )
    
    print(f"Planning result: {result.result}")
    
    # 6. Create MCP server (optional)
    mcp_server = system.create_mcp_server()
    if mcp_server:
        print("MCP server created - workflows available as tools!")
    
    return workflow_engine, tool_registry, event_bus


if __name__ == "__main__":
    asyncio.run(example_usage())