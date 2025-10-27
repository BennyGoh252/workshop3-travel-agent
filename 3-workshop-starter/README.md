# travel agent

This is a simple project to learn LangGraph.

## Set up

# Travel Planner (travel agents)

This repository is a small workshop project that demonstrates a multi-agent
travel planning workflow built on top of a LangGraph-style state graph. The
system coordinates three agents (Planner, Researcher, Booker) using a shared
message board and a coordinator. The console shows concise "thinking" traces
from agents as they run.

## Quick start

1. Create and activate the project's virtual environment (if you use the
	 included venv, run the python binary directly):

```sh
# if using the repo venv
.venv/bin/python --version
.venv/bin/python main.py

# or activate and run
source .venv/bin/activate
python main.py
```

2. (Optional) If you use the project's `uv` helper as documented earlier:

```sh
uv sync
uv run python main.py
```

## What the program does

- Prompts for a destination, check-in/check-out dates and number of guests.
- Automatically coordinates Planner → Researcher → Booker agents.
- Prints concise agent "thoughts" and observations (no timestamps by default)
	so you can follow their internal reasoning.
- Automatically summarizes the trip once tasks complete or when the
	configured volley limit is reached.

## Automated run behaviour

- The program runs fully automated (no Enter prompts) after you provide the
	trip details. It uses `volley_msg_left` (derived from trip length) to limit
	how many agent turns are executed before forcing a summary. You can tweak
	the initial value in `nodes.human_input_node`.

## Starter checklist

1. Sketch Graph
2. Go through dependencies (`pyproject.toml` / `requirements.txt`)
3. Define State (`state.py`)
4. Define Tools (`tools/`)
5. Define Agents (`agents/`)
6. Define Nodes (`nodes.py`)
7. Define Graph (`main.py`)

## Support

If anything doesn't behave as expected (e.g., missing API keys, exceptions
from external services), check the console output for the agent observation
messages and open an issue with the stack trace and the inputs you used.
