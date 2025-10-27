# How to Monitor a Research Run

## Method 1: Agent State Monitor (Airflow-style)

Monitor live agent state with an Airflow-style DAG view:

```bash
coscientist-monitor-agents research_20251026_182552
```

Or with full path:
```bash
coscientist-monitor-agents ~/.coscientist/research_20251026_182552
```

This shows:
- Which agents are running
- Current node being executed
- Agent status (pending, running, completed, error)
- Duration of each execution
- Any errors

Press `Ctrl+C` to stop monitoring.

---

## Method 2: Tail Agent Events (JSON Lines)

Watch agent events in real-time:

```bash
tail -f ~/.coscientist/research_20251026_182552/agent_events.jsonl
```

This shows every agent invocation as it happens in JSON format.

---

## Method 3: Progress Logs

Check high-level progress:

```bash
# Text-based logs
tail -f ~/.coscientist/research_20251026_182552/progress.txt

# Or structured JSON events
tail -f ~/.coscientist/research_20251026_182552/progress.json
```

---

## Method 4: Test Run Log

If running via `run_test.sh`:

```bash
# In the open-coscientist-agents directory
tail -f test_run.log
```

Shows all logging output including LLM calls.

---

## Current Run

Your current test is running in:
```
~/.coscientist/research_20251026_182552/
```

### Quick Start

Open a terminal and run:
```bash
coscientist-monitor-agents research_20251026_182552
```

You'll see live updates showing which agents are executing!

---

## Monitoring All Three Ways at Once

Terminal 1 (Agent State DAG):
```bash
coscientist-monitor-agents research_20251026_182552
```

Terminal 2 (Agent Events):
```bash
tail -f ~/.coscientist/research_20251026_182552/agent_events.jsonl
```

Terminal 3 (LLM Logs):
```bash
tail -f ~/projects/co-scientist/open-coscientist-agents/test_run.log
```

