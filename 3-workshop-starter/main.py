from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from state import State
from nodes import (
    human_input_node,
    check_completion,
    planner_node,
    researcher_node,
    booker_node,
    summarizer_node
)
from agents.coordinator import travel_coordinator


load_dotenv(override=True)  # Override, so it would use your local .env file


def build_graph():
    """
    Build the LangGraph workflow.
    """
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("human", human_input_node)
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("booker", booker_node)
    builder.add_node("summarize", summarizer_node)
    
    # From START, go to human input
    builder.set_entry_point("human")

    # Add nodes and routing: human -> coordinator -> agents
    builder.add_node("coordinator", travel_coordinator)

    # human input hands off to coordinator which selects next agent
    builder.add_edge("human", "coordinator")
    builder.add_edge("coordinator", "planner")
    
    # From agents, check completion status
    builder.add_conditional_edges(
        "planner",
        check_completion,
        {
            "continue": "researcher",
            "summarize": "summarize"
        }
    )
    
    builder.add_conditional_edges(
        "researcher",
        check_completion,
        {
            "continue": "booker",
            "summarize": "summarize"
        }
    )
    
    builder.add_conditional_edges(
        "booker",
        check_completion,
        {
            "continue": "planner",
            "summarize": "summarize"
        }
    )
    
    # From summary to END
    builder.add_edge("summarize", END)
    
    return builder.compile()


def main():
    print("===TRAVEL PLANNER ===")
    print("Let me help plan your perfect trip to anywhere!")
    print("I'll research attractions, check the weather, and book your hotel.")
    print("\nWorkflow:")
    print("1. Get your travel preferences")
    print("2. Research attractions and check weather")
    print("3. Find and book suitable hotel")
    print("4. Create detailed trip summary\n")
    print("Initializing travel planning system...")

    graph = build_graph()
    print("\nWorkflow Graph:")
    print(graph.get_graph().draw_ascii())
    print("\nStarting interactive planning process...\n")

    # Initialize state using the human input node (collects destination/dates)
    state = human_input_node(None)

    # Keep track of how many message_board entries we've displayed to the user
    last_board_index = 0

    try:
        # Automated loop: run until completion or volley exhausted
        while True:
            # Print any new message board entries for user visibility
            board = state.get("message_board", [])
            if len(board) > last_board_index:
                for entry in board[last_board_index:]:
                    # Print only agent and content — timestamps are stored but not shown
                    agent = entry.get("agent")
                    content = entry.get("content")
                    print(f"{agent}: {content}")
                last_board_index = len(board)

            # Check if system should finalize
            route = check_completion(state)
            if route == "summarize":
                summarizer_node(state)
                break

            # If volley_msg_left exhausted, finalize
            volley_left = state.get("volley_msg_left", 0)
            if volley_left <= 0:
                print("\nVolley exhausted — generating summary...\n")
                summarizer_node(state)
                break

            # Run coordinator to select next agent and post its thinking trace
            updates = travel_coordinator(state)
            # Merge updates into state
            for k, v in updates.items():
                if k == "message_board":
                    state.setdefault("message_board", [])
                    state["message_board"] = v
                else:
                    state[k] = v

            # Determine which agent to run next
            next_agent = state.get("next_agent") or state.get("next_speaker")
            if not next_agent:
                print("No agent selected. Stopping.")
                break

            # Call the appropriate agent node
            if next_agent == "planner":
                node_updates = planner_node(state)
            elif next_agent == "researcher":
                node_updates = researcher_node(state)
            elif next_agent == "booker":
                node_updates = booker_node(state)
            else:
                print(f"Unknown agent: {next_agent}")
                break

            # Merge node updates
            if node_updates:
                if "message_board" in node_updates:
                    state.setdefault("message_board", [])
                    state["message_board"] = node_updates["message_board"]
                if "shared_state" in node_updates:
                    state["shared_state"] = node_updates["shared_state"]
                if "phase" in node_updates:
                    state["phase"] = node_updates["phase"]
                if "next_agent" in node_updates:
                    state["next_agent"] = node_updates["next_agent"]
                if "error" in node_updates:
                    state["error"] = node_updates["error"]

            # Decrement volley counter and possibly continue
            state["volley_msg_left"] = state.get("volley_msg_left", 0) - 1

            # small heartbeat so console doesn't flood (optional)
            # time.sleep(0.1)

            # Loop continues until auto completion

    except KeyboardInterrupt:
        print("\n\nPlanning interrupted by keyboard. Generating summary...\n")
        summarizer_node(state)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Planning ended unexpectedly. Please try again.")


if __name__ == "__main__":
    main()
