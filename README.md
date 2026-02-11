### End to end project agentic chatbots

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
