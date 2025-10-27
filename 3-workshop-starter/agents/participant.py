from tools import singapore_time, singapore_weather, singapore_news
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils import debug
import re


# Persona configurations
PERSONAS = {
    "planner": {
        "name": "Planner",
        "backstory": "Breaks a trip into discrete tasks and assigns which parts need research/bookings.",
        "personality": "Organized, pragmatic, detail-oriented",
        "speech_style": "Clear, concise, directive",
        "tools": []
    },
    "researcher": {
        "name": "Researcher",
        "backstory": "Gathers up-to-date information about destinations, attractions, and logistics.",
        "personality": "Curious, thorough, evidence-driven",
        "speech_style": "Informative, concise",
        "tools": ["news", "weather"]
    },
    "booker": {
        "name": "Booker",
        "backstory": "Checks availability and handles reservations for hotels and transport.",
        "personality": "Practical, fast, reliability-focused",
        "speech_style": "Direct, transactional",
        "tools": ["time", "weather"]
    },
    "summarize": {
        "name": "Summarizer",
        "backstory": "Aggregates findings and produces the final trip plan and concise summary.",
        "personality": "Concise, high-level, objective",
        "speech_style": "Summary-style, bullet-friendly",
        "tools": []
    }
}


def execute_tool(tool_name):
    """
    Execute a specific tool and return its output.
    Returns Tool output as string
    """
    tool_name = tool_name.lower().strip()

    if tool_name == "time":
        return singapore_time()
    elif tool_name == "weather":
        return singapore_weather()
    elif tool_name == "news":
        return singapore_news()
    else:
        return f"Unknown tool: {tool_name}"


# def participant(persona_id, state) -> dict:
#     """
#     Generate speech for a persona using ReAct workflow with real tool calling.

#     Args:
#         persona_id: One of "ah_seng", "mei_qi", "bala", "dr_tan"
#         state: Current conversation state

#     Returns:
#         Dict with message updates for state
#     """
#     if persona_id not in PERSONAS:
#         return {"messages": [{"role": "assistant", "content": f"Unknown persona: {persona_id}"}]}

#     persona = PERSONAS[persona_id]
#     debug(f"\n=== {persona['name']} is thinking... ===")

#     # Get recent conversation for context
#     messages = state.get("messages", [])
#     conversation_text = ""
#     for msg in messages: 
#         conversation_text += f"{msg.get('content', '')}\n"

#     # System prompt for ReAct
#     system_prompt = f"""You are {persona['name']}, {persona['age']} years old.
# Background: {persona['backstory']}
# Personality: {persona['personality']}
# Speech style: {persona['speech_style']}

# You are at a Singapore kopitiam having a casual conversation.

# You run in a loop of Thought, Action, Observation.
# At the end of the loop you output a Message.

# Use Thought to describe your thoughts about the conversation.
# Use Action to run one of the actions available to you.
# Observation will be the result of running those actions.

# Your available actions are:

# time:
# Returns current time in Singapore

# weather:
# Returns current weather in Singapore

# news:
# Returns latest Singapore news

# ------

# Example session:

# Thought: I should check what time it is to frame my response
# Action: time

# You will be called again with:
# Observation: Time in Singapore now: [Actual time returned after you call the tool, THIS IS NOT THE RIGHT TIME, call Action: time to get the actual time]

# You must never try to guess the time or weather or news. Rely on the Observation that you will be called later on for the answers. You MUST NOT answer with those.

# You then continue thinking or output:
# Message: [Your response in character]

# IMPORTANT:
# - You can use multiple actions by continuing the loop
# - You must not be providing Observation in your response. Observation is a result from tool, not for you to respond.
# - Once you have enough information, output Message: followed by your response
# - Keep your Message concise (1-2 sentences) and in character
# """

#     # Internal loop for ReAct
#     max_iterations = 5  # Prevent infinite loops
#     internal_context = f"Recent conversation:\n{conversation_text}\n\nContinue the conversation as {persona['name']}.\n"

#     for iteration in range(max_iterations):
#         user_prompt = internal_context
#         debug(f"Iteration {iteration + 1}/{max_iterations}")

#         try:
#             llm = ChatOpenAI(model="gpt-5-mini", temperature=1)
#             response = llm.invoke([
#                 SystemMessage(content=system_prompt),
#                 HumanMessage(content=user_prompt)
#             ])
#             content = response.content.strip()
#             debug(f"LLM Response:\n{content}\n")

#             # Check if the response contains Message:
#             if "Message:" in content:
#                 # Extract the message
#                 message_match = re.search(r'Message:\s*(.*)', content, re.DOTALL)
#                 if message_match:
#                     final_message = message_match.group(1).strip()
#                     debug(f"Final Message: {final_message}")
#                     debug(f"=== End of {persona['name']}'s thought process ===\n")

#                     # Return the message to state
#                     return {
#                         "messages": [{
#                             "role": "assistant",
#                             "name": persona['name'],
#                             "content": f"\n{persona['name']}: {final_message}\n\n"
#                         }]
#                     }

#             # Check if the response contains Action:
#             if "Action:" in content:
#                 # Extract the action
#                 action_match = re.search(r'Action:\s*(\w+)', content)
#                 if action_match:
#                     tool_name = action_match.group(1)
#                     debug(f"Executing tool: {tool_name}")

#                     # Execute the tool
#                     observation = execute_tool(tool_name)
#                     debug(f"Observation: {observation}")
#                     debug("")  # Empty line for readability

#                     # Add observation to internal context
#                     internal_context += f"\n{content}\n\nObservation: {observation}\n"
#                     continue

#             # If we get here without action or message, add to context and continue
#             internal_context += f"\n{content}\n"

#         except Exception as e:
#             # Fallback response if LLM fails
#             return {
#                 "messages": [{
#                     "role": "assistant",
#                     "name": persona['name'],
#                     "content": f"{persona['name']}: Sorry ah, my mind a bit blur now..."
#                 }]
#             }

#     # If we exhausted iterations without getting a Message, provide default
#     return {
#         "messages": [{
#             "role": "assistant",
#             "name": persona['name'],
#             "content": f"{persona['name']}: Well, that's interesting lah..."
#         }]
#     }


# --- Travel agent configuration -------------------------------------------------
# Simple agent configs for the travel planner system. These agents are lightweight
# and designed to work with the nodes in `nodes.py`. The actual behaviour for each
# agent is implemented in the corresponding node function (planner_node,
# researcher_node, booker_node). This config only exposes metadata for wiring.

TRAVEL_AGENTS = {
    "planner": {
        "name": "Planner",
        "role": "Creates tasks, assigns work and monitors progress",
        "tools": []
    },
    "researcher": {
        "name": "Researcher",
        "role": "Searches attractions and gathers weather information",
        "tools": ["places", "weather"]
    },
    "booker": {
        "name": "Booker",
        "role": "Finds and books hotels",
        "tools": ["hotels"]
    }
}

def travel_participant(persona_id, state):
    """
    Orchestrator-facing participant. Does NOT call a separate `participant` helper.
    - Runs a single LLM turn for the given persona using the workspace PERSONAS.
    - Returns either {"messages": [...]} or {"action": "<tool>", "tool_query": "...", "raw": "...", "persona": persona_id}
    - The coordinator/orchestrator is responsible for executing actions and reinvoking this function
      with Observation added to state.
    """
    if persona_id not in PERSONAS:
        return {"messages": [{"role": "assistant", "content": f"Unknown persona: {persona_id}"}]}

    persona = PERSONAS[persona_id]
    debug(f"\n=== {persona['name']} is thinking... ===")

    # Build recent conversation context (prefer message_board then messages)
    messages = state.get("message_board") or state.get("messages") or []
    conversation_text = ""
    for msg in messages:
        # msg may be dict with agent/content or raw string
        if isinstance(msg, dict):
            conversation_text += f"{msg.get('agent','user')}: {msg.get('content','')}\n"
        else:
            conversation_text += f"{str(msg)}\n"

    system_prompt = f"""You are the {persona['name']} process in a travel planning system.
Background: {persona['backstory']}
Personality: {persona['personality']}
Speech style: {persona['speech_style']}

You operate in a Thought -> Action -> Observation loop. At the end of the loop output either:
- Message: <short 1-2 sentence reply>
OR
- Action: <tool>[: optional query]

Available tools the orchestrator can run: time, weather, news, attractions, etc.
If you emit Action, the orchestrator will run the tool and call you again with:
Observation: <tool output>

Do NOT fabricate tool outputs. Keep messages concise and on-task.
"""

    user_prompt = f"Recent conversation:\n{conversation_text}\n\nAs the {persona['name']}, respond with Thought/Action/Message as appropriate."

    try:
        llm = ChatOpenAI(model="gpt-5-mini", temperature=0.7)
        resp = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        content = resp.content.strip()
        debug(f"LLM Response for {persona_id}:\n{content}\n")

        # Prefer explicit Message:
        if "Message:" in content:
            m = re.search(r'Message:\s*(.*)', content, re.DOTALL)
            if m:
                final_message = m.group(1).strip()
                return {"messages": [{
                    "role": "assistant",
                    "name": persona['name'],
                    "content": final_message
                }]}

        # Or Action:
        if "Action:" in content:
            a = re.search(r'Action:\s*([^\n\r]+)', content)
            if a:
                action_text = a.group(1).strip()
                parts = action_text.split(":", 1)
                tool_name = parts[0].strip().lower()
                tool_query = parts[1].strip() if len(parts) > 1 else None
                return {
                    "action": tool_name,
                    "tool_query": tool_query,
                    "raw": content,
                    "persona": persona_id
                }

        # Fallback: return entire content as a message
        return {"messages": [{
            "role": "assistant",
            "name": persona['name'],
            "content": content
        }]}

    except Exception as e:
        debug(f"travel_participant error for {persona_id}: {e}")
        return {"messages": [{
            "role": "assistant",
            "name": persona['name'],
            "content": f"{persona['name']}: encountered an error"
        }]}

