### End to end project agentic chatbots
## Agentic Chatbots – LangGraph Multi-Agent System

A modular, graph-based LLM system built with LangGraph, demonstrating tool-augmented reasoning, state-driven routing, and multi-stage agent orchestration.

This repository contains:
	1.	Original learning examples from a LangGraph Udemy course
	2.	A fully original multi-stage agent: Brew Guide Agent

⸻

Original Udemy Scaffold

The original course project included:

LLM Provider
	•	Groq

Use Cases
	1.	Basic Chatbot
	2.	Chatbot with Web (Tavily search)
	3.	AI News Summarizer

These examples demonstrated:
	•	Basic LangGraph construction
	•	Tool integration
	•	Streamlit UI integration
	•	Conditional routing
	•	Single-pass response generation

These modules are preserved for learning reference.

My Extensions

1️⃣ OpenAI Support

Extended the system to support:
	•	OpenAI models
	•	Configurable provider selection
	•	Unified LLM interface for Groq and OpenAI

⸻

2️⃣ Brew Guide Agent (Original Implementation)

The Brew Guide Agent is a fully original multi-stage agent designed independently from the Udemy scaffold.

This agent demonstrates:
	•	Structured research planning
	•	Tool-augmented reasoning
	•	Parameter extraction
	•	Iterative drafting
	•	Self-review loop
	•	Deterministic state-based routing
	•	Configurable loop control

It is implemented as a separate graph module and does not reuse Udemy use case logic.

⸻

Brew Guide Agent – System Overview

Example Inputs
	•	Flair 58 light roast brew guide
	•	Cafelat Robot light roast feasibility

Architecture
flowchart TD
    START([START])
    END([END])

    research_agent["research_agent<br/>(LLM plans research<br/>+ optional tool call)"]
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


    Design Principles (Brew Guide Agent)

1. Explicit Graph Orchestration

The agent is implemented using LangGraph with clearly defined nodes:
	•	research_agent
	•	extract
	•	draft
	•	review
	•	finalize

Routing is state-driven and deterministic.

⸻

2. State-Driven Conditional Routing

Router functions inspect state values:
	•	tool_calls_count
	•	revision_count
	•	needs_revision

This ensures:
	•	Bounded loops
	•	Controlled iteration
	•	Predictable execution behavior

3. Loop Control Safeguards

Two configurable parameters:
max_tool_calls
max_revisions
These prevent:
	•	Infinite tool loops
	•	Infinite revision loops
	•	Unbounded cost
4. Structured Intermediate Representation

The agent enforces a structured extraction step before drafting.

Flow:
	1.	Research
	2.	Extract structured parameters
	3.	Draft using enforced headings
	4.	Review against checklist
	5.	Finalize

This reduces hallucination risk and improves output consistency.

ech Stack
	•	LangGraph
	•	LangChain
	•	OpenAI / Groq
	•	Tavily Search API
	•	Streamlit

⸻

Required API Keys
	•	OpenAI or Groq
	•	Tavily

⸻

Purpose of This Repository

This repository demonstrates:
	•	Evolution from tutorial-based systems
	•	Independent multi-stage agent design
	•	Practical tool-augmented LLM workflows
	•	State-based control logic
	•	Production-oriented architectural thinking

The Brew Guide Agent represents a deliberate step beyond simple chatbots toward structured, iterative AI systems.












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
