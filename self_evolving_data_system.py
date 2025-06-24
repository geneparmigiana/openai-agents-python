"""
Self-Evolving Data Intelligence System

This demonstrates how to build a system that:
1. Answers immediate data queries when possible
2. Identifies system limitations and gaps
3. Automatically creates workflows to improve capabilities
4. Evolves to handle increasingly complex queries

The system learns from every interaction and becomes more capable over time.
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum

import sys
sys.path.append('src')

from agents import Agent, function_tool, RunContextWrapper
from workflow_primitives import (
    WorkflowSystemBuilder, BaseWorkflow, WorkflowContext, 
    WorkflowResult, WorkflowStatus, StateScope, MemoryStateBackend
)


# =============================================================================
# 1. CORE DATA STRUCTURES
# =============================================================================

class QueryComplexity(Enum):
    SIMPLE = "simple"           # Direct SQL query
    MODERATE = "moderate"       # Multiple queries, joins
    COMPLEX = "complex"         # Requires new metrics/transformations
    IMPOSSIBLE = "impossible"   # Missing fundamental data


class WorkType(Enum):
    IMMEDIATE = "immediate"     # Can answer now
    ASYNC_IMPROVEMENT = "async_improvement"  # Background work to improve system
    BLOCKED = "blocked"         # Cannot answer, missing capabilities


@dataclass
class QueryUnderstanding:
    """Structured understanding of user query"""
    original_query: str
    intent: str
    entities: List[str]          # ["buildings", "DOB violations"]
    metrics: List[str]           # ["count", "threshold > 5"]
    time_scope: Optional[str]    # "last year", "all time"
    complexity: QueryComplexity
    required_data_sources: List[str]
    existing_capabilities: List[str]
    missing_capabilities: List[str]
    confidence: float


@dataclass
class DataCapability:
    """Represents a data capability the system has"""
    name: str
    description: str
    data_sources: List[str]
    metrics_available: List[str]
    last_updated: str
    performance_tier: str  # "fast", "medium", "slow"
    sql_pattern: Optional[str] = None


@dataclass
class ImprovementTask:
    """Represents work needed to improve the system"""
    task_id: str
    description: str
    work_type: WorkType
    priority: int  # 1-10
    estimated_effort: str  # "hours", "days", "weeks"
    dependencies: List[str]
    creates_capabilities: List[str]
    triggered_by_query: str
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed


@dataclass
class QueryResult:
    """Result of processing a query"""
    query_id: str
    original_query: str
    understanding: QueryUnderstanding
    immediate_answer: Optional[str] = None
    explanation: Optional[str] = None
    improvement_tasks: List[ImprovementTask] = field(default_factory=list)
    future_capability_timeline: Optional[str] = None
    confidence: float = 0.0


# =============================================================================
# 2. UNDERSTANDING AGENT - QUERY ANALYSIS & ROUTING
# =============================================================================

understanding_agent = Agent(
    name="Query Understanding Agent",
    instructions="""
    You are a query understanding specialist for a data intelligence system.
    
    Your job is to analyze user business queries and determine:
    
    1. INTENT: What is the user actually asking for?
    2. ENTITIES: What business objects are involved? (buildings, violations, permits, etc.)
    3. METRICS: What measurements are needed? (count, sum, average, threshold analysis)
    4. COMPLEXITY: How difficult is this to answer?
       - SIMPLE: Direct lookup/query
       - MODERATE: Multiple queries, some joins
       - COMPLEX: Requires new metrics, transformations, or analysis
       - IMPOSSIBLE: Missing fundamental data
    
    5. CAPABILITIES: What do we need to answer this?
       - Check against known data sources and capabilities
       - Identify gaps in current system
    
    6. ROUTING: Which agent(s) should handle this?
       - data_execution_agent: For immediate queries
       - process_improvement_agent: For complex cases needing system improvements
       - Both: When we can partially answer and also improve
    
    Always consider:
    - Can we answer this immediately with existing capabilities?
    - If not, what would we need to build to answer it?
    - How would answering this make the system better for future queries?
    """,
    output_type=QueryUnderstanding
)


# =============================================================================
# 3. DATA EXECUTION AGENT - IMMEDIATE QUERY HANDLING
# =============================================================================

@function_tool
async def sql_execution_tool(
    query: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Execute SQL query against data warehouse"""
    # In real implementation, this would connect to your data warehouse
    # For demo, we'll simulate execution
    
    workflow_context = context.context.get('workflow_context')
    if workflow_context:
        # Log query execution for learning
        await workflow_context.state_manager.set(
            f"executed_query:{hash(query)}", 
            {"query": query, "timestamp": "now", "performance": "simulated"},
            scope=StateScope.SESSION
        )
    
    # Simulate query execution
    if "DOB violations" in query.lower():
        return json.dumps({
            "result": [{"building_count": 1247}],
            "execution_time_ms": 2500,
            "complexity": "moderate",
            "tables_scanned": ["buildings", "violations", "dob_records"],
            "performance_issues": ["missing index on violation_count", "complex joins across 3 tables"]
        })
    else:
        return json.dumps({
            "result": "Query executed successfully",
            "execution_time_ms": 150,
            "complexity": "simple"
        })


@function_tool
async def data_lookup_tool(
    entity: str,
    lookup_type: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Look up data schema, available metrics, etc."""
    
    # Simulate data capability lookup
    if entity.lower() == "buildings":
        return json.dumps({
            "available_metrics": ["count", "total_area", "year_built", "violation_count"],
            "data_sources": ["buildings_table", "building_permits", "violations_log"],
            "performance": "fast for basic metrics, slow for violation analysis",
            "limitations": "violation_count not pre-calculated, requires expensive joins"
        })
    elif "violation" in entity.lower():
        return json.dumps({
            "available_metrics": ["violation_type", "violation_date", "severity", "resolution_status"],
            "data_sources": ["dob_violations", "violation_history"],
            "performance": "slow for aggregations, missing proper indexes",
            "limitations": "no pre-calculated violation counts per building"
        })
    else:
        return json.dumps({
            "available_metrics": [],
            "message": f"No data capabilities found for entity: {entity}"
        })


@function_tool
async def performance_assessment_tool(
    query_result: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Assess query performance and identify improvement opportunities"""
    
    result_data = json.loads(query_result)
    execution_time = result_data.get("execution_time_ms", 0)
    performance_issues = result_data.get("performance_issues", [])
    
    assessment = {
        "performance_tier": "slow" if execution_time > 2000 else "medium" if execution_time > 500 else "fast",
        "improvement_opportunities": performance_issues,
        "recommended_actions": []
    }
    
    if execution_time > 2000:
        assessment["recommended_actions"].extend([
            "Create pre-calculated metrics",
            "Add database indexes", 
            "Consider data pipeline optimization"
        ])
    
    if "missing index" in str(performance_issues):
        assessment["recommended_actions"].append("Add database indexes for violation_count")
    
    if "complex joins" in str(performance_issues):
        assessment["recommended_actions"].append("Create denormalized table with building violation metrics")
    
    return json.dumps(assessment)


data_execution_agent = Agent(
    name="Data Execution Agent",
    instructions="""
    You are a data execution specialist. Your job is to:
    
    1. Execute immediate data queries using available tools
    2. Assess the performance and complexity of queries
    3. Identify when queries are too slow/complex for production use
    4. Determine what improvements would make queries faster/better
    
    Available tools:
    - sql_execution_tool: Execute SQL queries
    - data_lookup_tool: Check available data and capabilities
    - performance_assessment_tool: Analyze query performance
    
    For each query:
    1. Check if we have the required data sources
    2. Execute the query if possible
    3. Assess performance and identify issues
    4. Recommend improvements if the query is too slow/complex
    
    Be honest about limitations and performance issues.
    """,
    tools=[sql_execution_tool, data_lookup_tool, performance_assessment_tool]
)


# =============================================================================
# 4. PROCESS IMPROVEMENT AGENT - SYSTEM EVOLUTION
# =============================================================================

@function_tool
async def create_improvement_task(
    description: str,
    work_type: str,
    priority: int,
    estimated_effort: str,
    creates_capabilities: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Create a new improvement task for the system"""
    
    workflow_context = context.context.get('workflow_context')
    if not workflow_context:
        return "Error: No workflow context available"
    
    task = ImprovementTask(
        task_id=f"task_{hash(description) % 10000}",
        description=description,
        work_type=WorkType(work_type),
        priority=priority,
        estimated_effort=estimated_effort,
        dependencies=[],
        creates_capabilities=creates_capabilities.split(","),
        triggered_by_query=workflow_context.workflow_id
    )
    
    # Store task for tracking
    await workflow_context.state_manager.set(
        f"improvement_task:{task.task_id}",
        task.__dict__,
        scope=StateScope.PERSISTENT
    )
    
    # Add to task queue
    task_queue = await workflow_context.state_manager.get("improvement_task_queue", scope=StateScope.PERSISTENT) or []
    task_queue.append(task.task_id)
    await workflow_context.state_manager.set("improvement_task_queue", task_queue, scope=StateScope.PERSISTENT)
    
    return f"Created improvement task: {task.task_id} - {description}"


@function_tool
async def assess_system_capabilities(
    required_capabilities: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Assess current system capabilities vs requirements"""
    
    workflow_context = context.context.get('workflow_context')
    if not workflow_context:
        return "Error: No workflow context available"
    
    # Get current capabilities
    current_capabilities = await workflow_context.state_manager.get("system_capabilities", scope=StateScope.PERSISTENT) or []
    
    required = required_capabilities.split(",")
    existing = [cap for cap in required if cap.strip() in current_capabilities]
    missing = [cap for cap in required if cap.strip() not in current_capabilities]
    
    return json.dumps({
        "required_capabilities": required,
        "existing_capabilities": existing,
        "missing_capabilities": missing,
        "coverage_ratio": len(existing) / len(required) if required else 1.0
    })


process_improvement_agent = Agent(
    name="Process Improvement Agent",
    instructions="""
    You are a process improvement specialist for the data intelligence system.
    
    Your job is to:
    1. Analyze when queries are too complex/slow for current capabilities
    2. Design improvement tasks that will make the system better
    3. Prioritize improvements based on impact and effort
    4. Create concrete work items for other agents to execute
    
    Available tools:
    - create_improvement_task: Create new improvement work
    - assess_system_capabilities: Check what we can/can't do
    
    When a query is too complex:
    1. Identify the root cause (missing metrics, poor performance, etc.)
    2. Design improvement tasks that would solve the problem
    3. Consider both immediate fixes and longer-term improvements
    4. Prioritize based on user impact and system benefit
    
    Types of improvements you might create:
    - Database optimization (indexes, denormalization)
    - New metrics and pre-calculations (dbt models)
    - Data pipeline improvements
    - New data source integrations
    
    Think strategically: how can we make the system answer this class of questions easily in the future?
    """,
    tools=[create_improvement_task, assess_system_capabilities]
)


# =============================================================================
# 5. DBT AGENT - ASYNC DATA MODELING
# =============================================================================

@function_tool
async def generate_dbt_model(
    model_name: str,
    description: str,
    required_metrics: str,
    source_tables: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Generate DBT model code for new metrics"""
    
    # Simulate DBT model generation
    dbt_code = f"""
-- models/{model_name}.sql
-- {description}

{{ config(materialized='table') }}

with source_data as (
    select 
        building_id,
        count(violation_id) as violation_count,
        max(violation_date) as last_violation_date,
        sum(case when severity = 'major' then 1 else 0 end) as major_violations
    from {{ ref('dob_violations') }}
    group by building_id
),

building_metrics as (
    select 
        b.building_id,
        b.address,
        b.year_built,
        coalesce(s.violation_count, 0) as total_violations,
        s.last_violation_date,
        s.major_violations,
        case 
            when s.violation_count > 5 then 'high_violations'
            when s.violation_count > 2 then 'medium_violations'
            else 'low_violations'
        end as violation_tier
    from {{ ref('buildings') }} b
    left join source_data s on b.building_id = s.building_id
)

select * from building_metrics
"""
    
    # Store the generated model
    workflow_context = context.context.get('workflow_context')
    if workflow_context:
        await workflow_context.state_manager.set(
            f"dbt_model:{model_name}",
            {"code": dbt_code, "status": "generated", "description": description},
            scope=StateScope.PERSISTENT
        )
    
    return f"Generated DBT model: {model_name}\n\nCode:\n{dbt_code}"


@function_tool
async def schedule_dbt_deployment(
    model_name: str,
    priority: str,
    context: RunContextWrapper[Dict[str, Any]]
) -> str:
    """Schedule DBT model for deployment"""
    
    workflow_context = context.context.get('workflow_context')
    if not workflow_context:
        return "Error: No workflow context available"
    
    deployment = {
        "model_name": model_name,
        "priority": priority,
        "scheduled_time": "next_deployment_window",
        "status": "scheduled"
    }
    
    await workflow_context.state_manager.set(
        f"dbt_deployment:{model_name}",
        deployment,
        scope=StateScope.PERSISTENT
    )
    
    return f"Scheduled DBT model {model_name} for deployment (priority: {priority})"


dbt_agent = Agent(
    name="DBT Agent",
    instructions="""
    You are a DBT specialist responsible for creating new data models and metrics.
    
    Your job is to:
    1. Generate DBT model code based on improvement requirements
    2. Create pre-calculated metrics that make queries faster
    3. Schedule deployments of new models
    4. Design data transformations that improve system capabilities
    
    Available tools:
    - generate_dbt_model: Create new DBT model code
    - schedule_dbt_deployment: Schedule model deployment
    
    When creating models:
    1. Focus on pre-calculating expensive operations
    2. Create denormalized tables for common query patterns
    3. Add proper indexing and partitioning strategies
    4. Consider both current needs and future extensibility
    
    For the building violations example:
    - Create a model that pre-calculates violation counts per building
    - Include violation tiers (high/medium/low) for easy filtering
    - Add time-based metrics (violations per year, recent violations)
    - Make queries that were slow become fast
    """,
    tools=[generate_dbt_model, schedule_dbt_deployment]
)


# =============================================================================
# 6. ORCHESTRATION WORKFLOW - PUTTING IT ALL TOGETHER
# =============================================================================

class DataIntelligenceWorkflow(BaseWorkflow):
    """Main workflow that orchestrates the entire data intelligence system"""
    
    def __init__(self):
        super().__init__(
            name="data_intelligence",
            description="Self-evolving data intelligence system"
        )
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Execute the complete data intelligence workflow"""
        
        try:
            from agents import Runner
            
            user_query = str(input_data)
            query_id = f"query_{hash(user_query) % 10000}"
            
            # Stage 1: Understand the query
            understanding_result = await Runner.run(
                understanding_agent,
                f"Analyze this business query: {user_query}",
                context=context.create_agent_context()
            )
            
            understanding = understanding_result.final_output
            await context.state_manager.save_checkpoint("understanding", understanding.__dict__)
            
            # Stage 2: Attempt immediate execution (if possible)
            immediate_answer = None
            performance_issues = []
            
            if understanding.complexity in [QueryComplexity.SIMPLE, QueryComplexity.MODERATE]:
                execution_result = await Runner.run(
                    data_execution_agent,
                    f"Execute query based on understanding: {understanding.__dict__}",
                    context=context.create_agent_context()
                )
                immediate_answer = execution_result.final_output
                
                # Check if execution revealed performance issues
                if "slow" in immediate_answer.lower() or "complex" in immediate_answer.lower():
                    understanding.complexity = QueryComplexity.COMPLEX
            
            # Stage 3: Process improvement (if needed)
            improvement_tasks = []
            
            if understanding.complexity in [QueryComplexity.COMPLEX, QueryComplexity.IMPOSSIBLE]:
                improvement_result = await Runner.run(
                    process_improvement_agent,
                    f"""
                    Query: {user_query}
                    Understanding: {understanding.__dict__}
                    Execution Result: {immediate_answer}
                    
                    Create improvement tasks to make this query faster/possible in the future.
                    """,
                    context=context.create_agent_context()
                )
                
                # Parse improvement tasks from result
                # In real implementation, would extract structured data
                improvement_tasks.append(ImprovementTask(
                    task_id="dbt_building_violations",
                    description="Create pre-calculated building violation metrics",
                    work_type=WorkType.ASYNC_IMPROVEMENT,
                    priority=8,
                    estimated_effort="2-3 days",
                    dependencies=[],
                    creates_capabilities=["fast_building_violation_queries"],
                    triggered_by_query=user_query
                ))
            
            # Stage 4: Async work generation (if needed)
            if improvement_tasks and any(task.work_type == WorkType.ASYNC_IMPROVEMENT for task in improvement_tasks):
                dbt_result = await Runner.run(
                    dbt_agent,
                    f"""
                    Create DBT model for building violation metrics.
                    Requirements: {understanding.metrics}
                    Source tables: buildings, dob_violations
                    Make queries like '{user_query}' fast and easy.
                    """,
                    context=context.create_agent_context()
                )
                
                # Update improvement task with DBT work
                for task in improvement_tasks:
                    task.assigned_agent = "dbt_agent"
                    task.status = "in_progress"
            
            # Stage 5: Compile final result
            result = QueryResult(
                query_id=query_id,
                original_query=user_query,
                understanding=understanding,
                immediate_answer=immediate_answer,
                improvement_tasks=improvement_tasks,
                future_capability_timeline="2-3 days for building violation metrics",
                confidence=0.8 if immediate_answer else 0.3
            )
            
            # Store result for learning
            await context.state_manager.set(
                f"query_result:{query_id}",
                result.__dict__,
                scope=StateScope.PERSISTENT
            )
            
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.COMPLETED,
                result=result.__dict__,
                metadata={
                    "query_complexity": understanding.complexity.value,
                    "immediate_answer_available": immediate_answer is not None,
                    "improvement_tasks_created": len(improvement_tasks),
                    "async_work_triggered": any(task.work_type == WorkType.ASYNC_IMPROVEMENT for task in improvement_tasks)
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )


# =============================================================================
# 7. SYSTEM LEARNING AND EVOLUTION
# =============================================================================

class SystemEvolutionWorkflow(BaseWorkflow):
    """Workflow that manages system evolution and learning"""
    
    def __init__(self):
        super().__init__(
            name="system_evolution",
            description="Manages system learning and capability evolution"
        )
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> WorkflowResult:
        """Analyze patterns and evolve system capabilities"""
        
        try:
            # Analyze query patterns
            query_patterns = await self._analyze_query_patterns(context)
            
            # Identify capability gaps
            capability_gaps = await self._identify_capability_gaps(context)
            
            # Prioritize improvements
            improvement_priorities = await self._prioritize_improvements(context)
            
            # Update system capabilities
            await self._update_system_capabilities(context)
            
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.COMPLETED,
                result={
                    "query_patterns": query_patterns,
                    "capability_gaps": capability_gaps,
                    "improvement_priorities": improvement_priorities
                }
            )
            
        except Exception as e:
            return WorkflowResult(
                workflow_id=context.workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )
    
    async def _analyze_query_patterns(self, context: WorkflowContext) -> Dict[str, Any]:
        """Analyze patterns in user queries to identify common needs"""
        # Implementation would analyze historical queries
        return {"common_entities": ["buildings", "violations"], "common_metrics": ["count", "threshold"]}
    
    async def _identify_capability_gaps(self, context: WorkflowContext) -> List[str]:
        """Identify gaps between what users need and what system can provide"""
        return ["building_violation_metrics", "fast_aggregation_queries"]
    
    async def _prioritize_improvements(self, context: WorkflowContext) -> List[Dict[str, Any]]:
        """Prioritize improvement tasks based on impact and effort"""
        return [{"task": "building_violation_metrics", "priority": 9, "impact": "high"}]
    
    async def _update_system_capabilities(self, context: WorkflowContext) -> None:
        """Update the system's understanding of its own capabilities"""
        await context.state_manager.set(
            "last_capability_update",
            "system_evolution_completed",
            scope=StateScope.PERSISTENT
        )


# =============================================================================
# 8. DEMONSTRATION
# =============================================================================

async def demonstrate_data_intelligence_system():
    """Demonstrate the complete self-evolving data intelligence system"""
    
    print("🏢 Self-Evolving Data Intelligence System Demo\n")
    
    # Build the system
    system = (WorkflowSystemBuilder()
              .with_state_backend(MemoryStateBackend())
              .register_workflow(DataIntelligenceWorkflow())
              .register_workflow(SystemEvolutionWorkflow())
              .register_agent_tool("understanding_agent", understanding_agent, "Query understanding and routing")
              .register_agent_tool("data_execution_agent", data_execution_agent, "Immediate data query execution")
              .register_agent_tool("process_improvement_agent", process_improvement_agent, "System improvement planning")
              .register_agent_tool("dbt_agent", dbt_agent, "Data modeling and transformation"))
    
    workflow_engine, tool_registry, event_bus = system.build()
    
    # Demo queries of increasing complexity
    test_queries = [
        "How many buildings have had more than 5 DOB violations?",
        "What's the average number of violations per building by neighborhood?",
        "Which buildings are at highest risk for future violations based on historical patterns?",
        "Create a dashboard showing building violation trends over time with predictive analytics"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Processing Query {i}: {query}")
        
        result = await workflow_engine.execute_workflow(
            "data_intelligence",
            query,
            session_id=f"demo_session_{i}"
        )
        
        if result.is_success():
            query_result = result.result or {}
            print(f"✅ Query processed successfully")
            print(f"📊 Complexity: {query_result.get('understanding', {}).get('complexity', 'unknown')}")
            print(f"🔄 Immediate answer: {'Yes' if query_result.get('immediate_answer') else 'No'}")
            print(f"🛠️  Improvement tasks: {query_result.get('improvement_tasks_created', 0)}")
            print(f"⚡ Async work triggered: {'Yes' if query_result.get('async_work_triggered') else 'No'}")
        else:
            print(f"❌ Query failed: {result.error}")
        
        print()
    
    # Demo system evolution
    print("🧠 Running System Evolution Analysis...")
    evolution_result = await workflow_engine.execute_workflow(
        "system_evolution",
        "analyze_and_evolve",
        session_id="evolution_session"
    )
    print(f"✅ System evolution completed: {evolution_result.is_success()}\n")
    
    # Create MCP server for the entire system
    print("🌐 Creating MCP Server...")
    mcp_server = system.create_mcp_server()
    if mcp_server:
        print("✅ MCP server created!")
        print("📡 Available services:")
        print("   - data_intelligence: Complete data query processing")
        print("   - system_evolution: System learning and improvement")
        print("\n🌟 External systems can now access this data intelligence via MCP!")
    
    print("\n🎉 Self-Evolving Data Intelligence System demo completed!")
    
    return workflow_engine, tool_registry, event_bus


if __name__ == "__main__":
    asyncio.run(demonstrate_data_intelligence_system())