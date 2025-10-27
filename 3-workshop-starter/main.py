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

    Updated flow:
      START -> human -> coordinator -> planner -> coordinator -> (researcher/booker) -> coordinator -> planner -> summarize -> END
    """
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("human", human_input_node)
    builder.add_node("coordinator", travel_coordinator)
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("booker", booker_node)
    builder.add_node("summarize", summarizer_node)

    # Connect START to human (optional) and set the entry to the human node so the rendered graph
    # shows all reachable nodes without treating START as an end node.
    builder.add_edge(START, "human")
    builder.set_entry_point("human")  # <-- use the human node name here, not START

    # human -> coordinator
    builder.add_edge("human", "coordinator")

    # Coordinator orchestrates flow:
    # coordinator -> planner
    builder.add_edge("coordinator", "planner")
    # planner -> coordinator (planner returns the parts/tasks to be done)
    builder.add_edge("planner", "coordinator")

    # coordinator -> researcher/booker (assign respective parts)
    builder.add_edge("coordinator", "researcher")
    builder.add_edge("coordinator", "booker")

    # researcher/booker -> coordinator (return results/findings)
    builder.add_edge("researcher", "coordinator")
    builder.add_edge("booker", "coordinator")

    # Coordinator may loop back to planner to assemble plan, then summarize -> END
    builder.add_edge("coordinator", "summarize")
    builder.add_edge("summarize", END)

    return builder.compile()


def main():
    print("===TRAVEL PLANNER ===")
    print("Let me help plan your perfect trip to anywhere!")
    print("I'll research attractions, check the weather, and book your hotel.")
    print("\nWorkflow:")
    print("1. Get your travel preferences")
    print("2. Coordinator asks planner to break down tasks")
    print("3. Planner returns parts to coordinator")
    print("4. Coordinator assigns parts to researcher/booker")
    print("5. Researcher/Booker return findings to coordinator")
    print("6. Coordinator asks planner to assemble final plan and summarize\n")
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

            # Run coordinator to select next agent and post its thinking trace.
            # Coordinator is the central router in the updated flow.
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
            elif next_agent == "coordinator":
                # coordinator may be scheduled as next_agent by planner/researcher/booker;
                # call travel_coordinator to process returned parts/results.
                node_updates = travel_coordinator(state)
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
