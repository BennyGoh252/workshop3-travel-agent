from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
import uuid

from state import State, Task, Message
from tools.attractions import search_attractions
from tools.weather import get_weather
from tools.hotels import book_hotel


def human_input_node(state: State) -> Dict[str, Any]:
    """
    Get travel request from user and initialize system state
    """
    # Get basic travel info
    print("\nWhere would you like to travel? (e.g., 'kyoto')")
    destination = input("Destination: ").strip().lower()
    
    print("\nWhen would you like to check in? (YYYY-MM-DD)")
    check_in = input("Check-in date: ").strip()
    
    print("\nWhen would you like to check out? (YYYY-MM-DD)")
    check_out = input("Check-out date: ").strip()
    
    print("\nHow many guests?")
    guests = int(input("Number of guests: ").strip())
    
    # Compute a sensible number of auto rounds from dates
    try:
        from datetime import datetime as _dt
        sd = _dt.strptime(check_in, "%Y-%m-%d")
        ed = _dt.strptime(check_out, "%Y-%m-%d")
        nights = max(1, (ed - sd).days)
    except Exception:
        nights = 3

    # Initialize clean state
    return {
        "message_board": [],
        "shared_state": {
            "tasks": [],
            "task_status": {},
            "results": {},
            "bookings": [],
            "itinerary": None
        },
        "agent_states": {
            "planner": {"memory": [], "task_history": [], "tool_logs": []},
            "researcher": {"memory": [], "task_history": [], "tool_logs": []},
            "booker": {"memory": [], "task_history": [], "tool_logs": []}
        },
        "current_agent": "planner",
        "request": {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "preferences": {}
        },
        "phase": "planning",
        # Automatic mode controls
        # volley_msg_left: how many agent turns to allow before forcing summary/stop
        "volley_msg_left": max(6, nights * 3),
        # next_speaker: optional hint for who should run next (planner/researcher/booker)
        "next_speaker": "planner",
        "next_agent": None,
        "error": None
    }


def check_completion(state: State) -> Literal["summarize", "continue"]:
    """
    Check if all tasks are completed and we can generate final itinerary
    """
    shared = state["shared_state"]
    
    # If we have an error, go to summary
    if state.get("error"):
        return "summarize"
        
    # If we're already summarizing, continue that
    if state["phase"] == "summary":
        return "summarize"
        
    # Check if all tasks are done
    all_completed = all(
        status["status"] == "completed"
        for status in shared["task_status"].values()
    )
    
    # If we have results and bookings, we can finish
    has_results = bool(shared["results"])
    has_booking = bool(shared["bookings"])
    
    if all_completed and has_results and has_booking:
        return "summarize"
        
    return "continue"


def planner_node(state: State) -> Dict[str, Any]:
    """
    Planner agent: Creates and assigns tasks, monitors progress
    """
    print("\n=== Planner Agent Thinking ===")
    print("Reviewing current state and tasks...")
    # Add visible thinking trace to message board so user can watch
    try:
        state["message_board"].append({
            "timestamp": datetime.now(),
            "agent": "planner",
            "content": "Planner: reviewing state and preparing tasks",
            "payload": None
        })
    except Exception:
        pass
    
    shared = state["shared_state"]
    board = state["message_board"]
    request = state["request"]
    
    # If no tasks yet, create initial tasks
    if not shared["tasks"]:
        print(f"No tasks found. Creating initial tasks for {request['destination']} trip...")
        # Thought/Action trace for visibility
        board.append({
            "timestamp": datetime.now(),
            "agent": "planner",
            "content": "Thought: I should create tasks for research and booking. Action: create tasks and assign to researcher and booker.",
            "payload": None
        })
        research_task: Task = {
            "id": str(uuid.uuid4()),
            "type": "research",
            "description": f"Research attractions and weather in {request['destination']}",
            "params": {
                "location": request["destination"],
                "start_date": request["check_in"],
                "end_date": request["check_out"]
            },
            "assigned_to": "researcher"
        }
        
        book_task: Task = {
            "id": str(uuid.uuid4()),
            "type": "book",
            "description": f"Book hotel in {request['destination']}",
            "params": {
                "location": request["destination"],
                "check_in": request["check_in"],
                "check_out": request["check_out"],
                "guests": request["guests"]
            },
            "assigned_to": "booker"
        }
        
        shared["tasks"] = [research_task, book_task]
        
        # Initialize task status
        for task in shared["tasks"]:
            shared["task_status"][task["id"]] = {
                "task_id": task["id"],
                "status": "pending",
                "result": None,
                "updated_at": datetime.now()
            }
            
        # Post assignments
        board.append({
            "timestamp": datetime.now(),
            "agent": "planner",
            "content": "Created and assigned initial tasks",
            "payload": {"tasks": shared["tasks"]}
        })
        
    # Review results and advance phases
    completed_tasks = [
        task for task in shared["tasks"]
        if shared["task_status"][task["id"]]["status"] == "completed"
    ]
    
    if len(completed_tasks) == len(shared["tasks"]):
        # All done, move to summary
        state["phase"] = "summary"
        board.append({
            "timestamp": datetime.now(),
            "agent": "planner",
            "content": "All tasks completed. Moving to summary phase.",
            "payload": None
        })
        
    # Route to appropriate next agent
    pending_tasks = [
        task for task in shared["tasks"]
        if shared["task_status"][task["id"]]["status"] == "pending"
    ]
    
    if pending_tasks:
        # Route to first agent with pending task
        state["next_agent"] = pending_tasks[0]["assigned_to"]
    
    # Return state updates
    return {
        "shared_state": shared,
        "message_board": board,
        "phase": state["phase"],
        "next_agent": state["next_agent"]
    }
    

def researcher_node(state: State) -> Dict[str, Any]:
    """
    Researcher agent: Searches attractions and gets weather forecasts
    """
    print("\n=== Researcher Agent Thinking ===")
    print("Looking for research tasks...")
    # Visible thinking trace for user
    try:
        state["message_board"].append({
            "timestamp": datetime.now(),
            "agent": "researcher",
            "content": "Researcher: scanning for pending research task",
            "payload": None
        })
    except Exception:
        pass
    
    shared = state["shared_state"]
    board = state["message_board"]
    
    # Find my pending task
    my_task = next(
        (task for task in shared["tasks"]
         if task["assigned_to"] == "researcher"
         and shared["task_status"][task["id"]]["status"] == "pending"),
        None
    )
    
    if not my_task:
        print("No pending research tasks found.")
        return {}
        
    try:
        print(f"\nStarting research task: {my_task['description']}")
        print("Marking task as in progress...")
        # Mark task in progress
        shared["task_status"][my_task["id"]]["status"] = "in_progress"

        # Post Thought/Action to message board
        board.append({
            "timestamp": datetime.now(),
            "agent": "researcher",
            "content": "Thought: Identify top attractions and check weather. Action: call places API then weather API.",
            "payload": {"task_id": my_task["id"]}
        })
        
        # Get attractions (Action)
        attractions = search_attractions(
            my_task["params"]["location"],
            radius_km=5,
            top_n=5
        )
        
        # Observation: attractions result
        board.append({
            "timestamp": datetime.now(),
            "agent": "researcher",
            "content": f"Observation: found {len(attractions)} attractions (top example: {attractions[0]['name'] if attractions else 'n/a'})",
            "payload": {"attractions_count": len(attractions)}
        })

        # Get weather if we have attractions (Action)
        weather = None
        if attractions:
            # Use first attraction's coordinates
            weather = get_weather(
                attractions[0]["lat"],
                attractions[0]["lon"],
                my_task["params"]["start_date"],
                my_task["params"]["end_date"]
            )

            board.append({
                "timestamp": datetime.now(),
                "agent": "researcher",
                "content": f"Observation: retrieved weather for {my_task['params']['start_date']} to {my_task['params']['end_date']}",
                "payload": {"days": len(weather.get("daily", [])) if weather else 0}
            })
            
        # Store results
        result = {
            "attractions": attractions,
            "weather": weather
        }
        
        shared["results"].update(result)
        
        # Mark task completed
        shared["task_status"][my_task["id"]].update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.now()
        })
        
        # Post update
        board.append({
            "timestamp": datetime.now(),
            "agent": "researcher",
            "content": f"Completed research for {my_task['params']['location']}",
            "payload": result
        })
        
    except Exception as e:
        # Handle failure
        shared["task_status"][my_task["id"]].update({
            "status": "failed",
            "result": {"error": str(e)},
            "updated_at": datetime.now()
        })
        
        state["error"] = str(e)
        
        board.append({
            "timestamp": datetime.now(),
            "agent": "researcher",
            "content": f"Failed to complete research: {e}",
            "payload": None
        })
        
    return {
        "shared_state": shared,
        "message_board": board,
        "error": state.get("error")
    }


def booker_node(state: State) -> Dict[str, Any]:
    """
    Booker agent: Makes hotel reservations
    """
    print("\n=== Booker Agent Thinking ===")
    print("Checking for booking tasks...")
    # Visible thinking trace for user
    try:
        state["message_board"].append({
            "timestamp": datetime.now(),
            "agent": "booker",
            "content": "Booker: looking for booking opportunities",
            "payload": None
        })
    except Exception:
        pass
    
    shared = state["shared_state"]
    board = state["message_board"]
    
    # Find my pending task
    my_task = next(
        (task for task in shared["tasks"]
         if task["assigned_to"] == "booker"
         and shared["task_status"][task["id"]]["status"] == "pending"),
        None
    )
    
    if not my_task:
        print("No pending booking tasks found.")
        return {}
        
    try:
        print(f"\nStarting booking task: {my_task['description']}")
        print("Marking task as in progress...")
        # Mark task in progress
        shared["task_status"][my_task["id"]]["status"] = "in_progress"
        
        # Thought/Action trace
        board.append({
            "timestamp": datetime.now(),
            "agent": "booker",
            "content": "Thought: find best available hotels for the dates and guests. Action: call hotel search API.",
            "payload": {"task_id": my_task["id"]}
        })

        print("Searching for available hotels...")
        # Make booking
        booking = book_hotel(
            location=my_task["params"]["location"],
            check_in=my_task["params"]["check_in"],
            check_out=my_task["params"]["check_out"],
            guests=my_task["params"]["guests"]
        )
        
        # Store booking
        shared["bookings"].append(booking)

        # Observation: booking result
        board.append({
            "timestamp": datetime.now(),
            "agent": "booker",
            "content": f"Observation: selected hotel {booking['hotel']['name']} with total {booking.get('total_price')}",
            "payload": {"booking": booking}
        })
        
        # Mark task completed
        shared["task_status"][my_task["id"]].update({
            "status": "completed",
            "result": {"booking": booking},
            "updated_at": datetime.now()
        })
        
        # Post update
        board.append({
            "timestamp": datetime.now(),
            "agent": "booker",
            "content": f"Booked {booking['hotel']['name']} for {booking['nights']} nights",
            "payload": {"booking": booking}
        })
        
    except Exception as e:
        # Handle failure
        shared["task_status"][my_task["id"]].update({
            "status": "failed",
            "result": {"error": str(e)},
            "updated_at": datetime.now()
        })
        
        state["error"] = str(e)
        
        board.append({
            "timestamp": datetime.now(),
            "agent": "booker",
            "content": f"Failed to complete booking: {e}",
            "payload": None
        })
        
    return {
        "shared_state": shared,
        "message_board": board,
        "error": state.get("error")
    }


def summarizer_node(state: State) -> Dict[str, Any]:
    """
    Generate final trip summary and itinerary
    """
    shared = state["shared_state"]
    board = state["message_board"]
    request = state["request"]
    
    print("\n=== TRIP SUMMARY ===\n")
    
    if state.get("error"):
        print(f"Error occurred: {state['error']}")
        print("\nUnable to complete trip planning. Please try again.")
        return {}
        
    # Get results
    attractions = shared["results"].get("attractions", [])
    weather = shared["results"].get("weather", {})
    booking = shared["bookings"][0] if shared["bookings"] else None
    
    if not (attractions and weather and booking):
        print("Missing required information. Please try again.")
        return {}
        
    # Print summary
    print(f"Trip to {request['destination'].title()}")
    print(f"Dates: {request['check_in']} to {request['check_out']}")
    print(f"Guests: {request['guests']}\n")
    
    print("Hotel:")
    print(f"- {booking['hotel']['name']}")
    print(f"- Confirmation: {booking['confirmation_code']}")
    print(f"- Total: ${booking['total_price']} {booking['currency']}")
    print(f"- {booking['cancellation_policy']}\n")
    
    print("Top Attractions:")
    for i, poi in enumerate(attractions, 1):
        print(f"{i}. {poi['name']}")
        print(f"   {poi['description']}")
        print(f"   Visit duration: {poi['visit_duration']} hours")
        print()
        
    print("Weather Forecast:")
    for day in weather["daily"]:
        print(f"- {day['date']}: {day['weather_code'].replace('_', ' ').title()}")
        print(f"  High: {day['temperature_max']}°C, Low: {day['temperature_min']}°C")
        print(f"  Rain chance: {int(day['precipitation_probability'] * 100)}%\n")
        
    print("\nHave a great trip!")
    
    return {}
