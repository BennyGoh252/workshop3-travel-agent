from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class Task(TypedDict):
    """Individual task assigned by planner"""
    id: str
    type: str  # "research" or "book"
    description: str
    params: Dict[str, Any]
    assigned_to: str


class TaskStatus(TypedDict):
    """Status tracking for tasks"""
    task_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    result: Optional[Dict[str, Any]]
    updated_at: datetime


class Message(TypedDict):
    """Message board entry"""
    timestamp: datetime
    agent: str
    content: str
    payload: Optional[Dict[str, Any]]


class AgentState(TypedDict):
    """Per-agent private state"""
    memory: List[str]  # Agent's memory/context
    task_history: List[str]  # Previously completed tasks
    tool_logs: List[Dict[str, Any]]  # Tool usage logs


class SharedState(TypedDict):
    """Shared state between all agents"""
    tasks: List[Task]
    task_status: Dict[str, TaskStatus]  # task_id -> status
    results: Dict[str, Any]  # Collected results
    bookings: List[Dict[str, Any]]  # Hotel bookings
    itinerary: Optional[Dict[str, Any]]  # Final generated itinerary


class TravelRequest(TypedDict):
    """User's travel request details"""
    destination: str
    check_in: str  # ISO date
    check_out: str  # ISO date
    guests: int
    preferences: Optional[Dict[str, Any]]


class State(TypedDict):
    """
    Overall state of the travel planning system.
    
    Contains:
    - message_board: Shared communication channel
    - shared_state: Shared data and results
    - agent_states: Per-agent private state
    - current_agent: Currently active agent
    - request: Original travel request
    """
    message_board: List[Message]
    shared_state: SharedState
    agent_states: Dict[str, AgentState]
    current_agent: str  # "planner", "researcher", or "booker"
    request: TravelRequest
    
    # Optional fields for flow control
    phase: str  # "planning", "research", "booking", "summary"
    next_agent: Optional[str]
    error: Optional[str]