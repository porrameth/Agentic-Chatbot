### End to end project agentic chatbots
# Agentic Chatbots – LangGraph Multi-Agent System

A modular, graph-based LLM system built with **LangGraph**, demonstrating tool-augmented reasoning, state-driven routing, and multi-stage agent orchestration.

This repository contains:

1. Original learning examples from a LangGraph Udemy course  
2. A fully original multi-stage agent: **Brew Guide Agent**

---

## Original Udemy Scaffold

The original course project included:

### LLM Provider
- Groq

### Use Cases
1. Basic Chatbot  
2. Chatbot with Web (Tavily Search)  
3. AI News Summarizer  

These examples demonstrated:

- Basic LangGraph construction  
- Tool integration  
- Streamlit UI integration  
- Conditional routing  
- Single-pass response generation  

These modules are preserved for learning reference.

---

## My Extensions

### 1. OpenAI Support

Extended the system to support:

- OpenAI models  
- Configurable provider selection  
- Unified LLM interface for Groq and OpenAI  

---

### 2. Brew Guide Agent (Original Implementation)

The Brew Guide Agent is a fully original multi-stage agent designed independently from the Udemy scaffold.

This agent demonstrates:

- Structured research planning  
- Tool-augmented reasoning  
- Parameter extraction  
- Iterative drafting  
- Self-review loop  
- Deterministic state-based routing  
- Configurable loop control  

It is implemented as a separate graph module and does not reuse Udemy use case logic.

---

# Brew Guide Agent – System Overview

## Example Inputs

- `Flair 58 light roast brew guide`
- `Cafelat Robot light roast feasibility`

---

## Architecture

```mermaid
flowchart TD
    START([START])
    END([END])

    research_agent["research_agent<br/>(LLM plans research + optional tool call)"]
    tools["tools<br/>(Tavily search)"]
    extract["extract<br/>(structured parameter extraction)"]
    draft["draft<br/>(guide generation)"]
    review["review<br/>(quality + safety check)"]
    finalize["finalize<br/>(deterministic final output)"]

    START --> research_agent

    research_agent -->|tool call & count < max_tool_calls| tools
    tools --> research_agent

    research_agent -->|no tool call or limit reached| extract
    extract --> draft
    draft --> review

    review -->|needs revision & rev < max_revisions| draft
    review -->|approved or limit reached| finalize

    finalize --> END
```
    ---


## Design Principles (Brew Guide Agent)

### 1. Explicit Graph Orchestration

The agent is implemented using LangGraph with clearly defined nodes:

- `research_agent`
- `extract`
- `draft`
- `review`
- `finalize`

Routing is state-driven and deterministic.

---

### 2. State-Driven Conditional Routing

Router functions inspect state values:

- `tool_calls_count`
- `revision_count`
- `needs_revision`

This ensures:

- Bounded loops  
- Controlled iteration  
- Predictable execution behavior  

---

### 3. Loop Control Safeguards

Two configurable parameters control iteration limits:

```python
max_tool_calls
max_revisions
These prevent:
	•	Infinite tool loops
	•	Infinite revision loops
	•	Unbounded cost










Required API Keys:
- Groq or OpenAI
- Tavily

Use Case: Brew Guide Agent 

Example input for the Brew Guide use case: 
	•	“Flair 58 light roast brew guide”
	•	“Cafelat Robot light roast feasibility”


Architecture:
```mermaid

flowchart TD
    START([START])
    END([END])

    research_agent["research_agent<br/>(LLM plans research<br/>+ may call tools)"]
    tools["tools<br/>(Tavily search)"]
    extract["extract<br/>(extract brew parameters)"]
    draft["draft<br/>(write brew guide)"]
    review["review<br/>(judge quality)"]
    finalize["finalize<br/>(final rewrite)"]

    START --> research_agent

    research_agent -->|tool call<br/>& count < 2| tools
    tools --> research_agent

    research_agent -->|no tool call<br/>or max reached| extract
    extract --> draft
    draft --> review

    review -->|needs revision<br/>& rev < 2| draft
    review -->|ok or max reached| finalize

    finalize --> END
