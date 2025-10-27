from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils import debug
from agents.participant import travel_participant


def coordinator(state):
    """
    Select next speaker based on conversation context.
    Manages volley control and updates state accordingly.

    Updates state with:
    - next_speaker: Selected agent ID or "human"
    - volley_msg_left: Decremented counter

    Returns: Updated state
    """

    debug(state)
    volley_left = state.get("volley_msg_left", 0)
    debug(f"Volley messages left: {volley_left}", "COORDINATOR")

    if volley_left <= 0:
        debug("No volleys left, returning to human", "COORDINATOR")
        return {
            "next_speaker": "human",
            "volley_msg_left": 0
        }

    messages = state.get("messages", [])

    conversation_text = ""
    for msg in messages:
        # Messages are now always dicts
        conversation_text += f"{msg.get('content', '')}\n"

    system_prompt = """You are managing a lively conversation at a Singapore kopitiam.

    Available speakers:
    - ah_seng: Uncle Ah Seng, 68yo kopi uncle, speaks Singlish, knows about drinks and weather
    - mei_qi: Young 21yo content creator, social media savvy, knows latest news and trends
    - bala: Ex-statistician turned football tipster, dry humor, analytical
    - dr_tan: Retired 72yo philosophy professor, thoughtful and deep thinker

    Based on the conversation flow, select who should speak next to keep the conversation lively and natural.
    Consider:
    - Who hasn't spoken recently
    - Who has relevant expertise for the current topic
    - Most importantly, who would add interesting perspective
    - Natural kopitiam banter flow
    - mei_qi should speak more about social media and trends, and she gets a lot of news, so she's naturally excited.

    Respond with ONLY the speaker ID (ah_seng, mei_qi, bala, or dr_tan).
    """

    user_prompt = f"""Recent conversation:
{conversation_text}

Who should speak next to keep this kopitiam conversation lively?"""

    debug("Analyzing conversation context...", "COORDINATOR")

    # Call LLM
    try:
        llm = ChatOpenAI(model="gpt-5-nano", temperature=1)

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Extract speaker from response
        if isinstance(response.content, list):
            selected_speaker = " ".join(str(item) for item in response.content).strip().lower()
        else:
            selected_speaker = str(response.content).strip().lower()
        debug(f"LLM selected: {selected_speaker}", "COORDINATOR")

        # Validate speaker
        valid_speakers = ["ah_seng", "mei_qi", "bala", "dr_tan"]
        if selected_speaker not in valid_speakers:
            # Fallback to round-robin if invalid
            import random
            selected_speaker = random.choice(valid_speakers)
            debug(f"Invalid speaker, fallback to: {selected_speaker}", "COORDINATOR")

    except Exception as e:
        # Fallback selection if LLM fails
        import random
        valid_speakers = ["ah_seng", "mei_qi", "bala", "dr_tan"]
        selected_speaker = random.choice(valid_speakers)
        debug(f"LLM error, random selection: {selected_speaker}", "COORDINATOR")

    debug(f"Final selection: {selected_speaker} (volley {volley_left} -> {volley_left - 1})", "COORDINATOR")

    # Return only the updates (LangGraph will merge with existing state)
    return {
        "next_speaker": selected_speaker,
        "volley_msg_left": volley_left - 1
    }


def travel_coordinator(state: dict) -> dict:
        """
        Simple coordinator for the travel planning workflow.

        Behavior:
        - If there are tasks in state["shared_state"]["tasks"], pick the first pending
            task and set `next_agent` to the agent assigned to it.
        - If no tasks exist yet (immediately after user input), instruct the Planner
            to start.
        - Post a short message to the shared `message_board` so the user can see the
            coordinator is initiating the agent discussion.
        """
        print("\n=== Coordinator: orchestrating travel agents ===")

        shared = state.get("shared_state") or {}
        board = state.get("message_board", [])

        tasks = shared.get("tasks") if shared else None

        # Default to planner when nothing else is scheduled
        next_agent = "planner"

        if tasks:
                # Find first pending task
                pending = [t for t in tasks if (state.get("shared_state", {}).get("task_status", {}).get(t["id"], {}).get("status") == "pending")]
                if pending:
                        next_agent = pending[0].get("assigned_to", "planner")

        # Announce to message board so user can see coordinator action
        board.append({
                "timestamp": __import__("datetime").datetime.now(),
                "agent": "coordinator",
                "content": f"Coordinator requests {next_agent} to begin their tasks.",
                "payload": {"next_agent": next_agent}
        })

        print(f"Coordinator selected next agent: {next_agent}")

        # Also ask the agent to post an initial 'thinking' message so the user can
        # see both the coordinator instruction and the agent's initial trace.
        try:
            agent_updates = travel_participant(next_agent, {"message_board": board})
            # travel_participant returns {"message_board": board}
            if agent_updates and "message_board" in agent_updates:
                board = agent_updates["message_board"]
        except Exception as e:
            debug(f"Error calling travel_participant: {e}", "COORDINATOR")

        return {"next_agent": next_agent, "message_board": board}
