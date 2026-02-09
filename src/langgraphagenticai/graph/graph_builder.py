from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from langgraph.graph import START,END
from src.langgraphagenticai.nodes.basic_chatbot_node import BasicChatbotNode
from src.langgraphagenticai.tools.search_tool import get_tools, create_tool_node
from langgraph.prebuilt import tools_condition,ToolNode
from src.langgraphagenticai.nodes.chatbot_with_Tool_node import ChatbotWithToolNode
from src.langgraphagenticai.nodes.ai_news_node import AINewsNode

from langchain_core.messages import SystemMessage


class GraphBuilder:
    def __init__(self,model):
        self.llm=model
        self.graph_builder=StateGraph(State)

    def basic_chatbot_build_graph(self):
        """
        Builds a basic chatbot graph using LangGraph.
        This method initializes a chatbot node using the `BasicChatbotNode` class 
        and integrates it into the graph. The chatbot node is set as both the 
        entry and exit point of the graph.
        """

        self.basic_chatbot_node=BasicChatbotNode(self.llm)

        self.graph_builder.add_node("chatbot",self.basic_chatbot_node.process)
        self.graph_builder.add_edge(START,"chatbot")
        self.graph_builder.add_edge("chatbot",END)


    def chatbot_with_tools_build_graph(self):
        """
        Builds an advanced chatbot graph with tool integration.
        This method creates a chatbot graph that includes both a chatbot node 
        and a tool node. It defines tools, initializes the chatbot with tool 
        capabilities, and sets up conditional and direct edges between nodes. 
        The chatbot node is set as the entry point.
        """
        ## Define the tool and tool node
        tools=get_tools()
        tool_node=create_tool_node(tools)

        ## Define the LLM
        llm=self.llm

        ## Define the chatbot node

        obj_chatbot_with_node=ChatbotWithToolNode(llm)
        chatbot_node=obj_chatbot_with_node.create_chatbot(tools)
        ## Add nodes
        self.graph_builder.add_node("chatbot",chatbot_node)
        self.graph_builder.add_node("tools",tool_node)
        # Define conditional and direct edges
        self.graph_builder.add_edge(START,"chatbot")
        self.graph_builder.add_conditional_edges("chatbot",tools_condition)
        self.graph_builder.add_edge("tools","chatbot")
    
    
    def ai_news_builder_graph(self):

        ai_news_node=AINewsNode(self.llm)

        ## added the nodes

        self.graph_builder.add_node("fetch_news",ai_news_node.fetch_news)
        self.graph_builder.add_node("summarize_news",ai_news_node.summarize_news)
        self.graph_builder.add_node("save_result",ai_news_node.save_result)

        #added the edges

        self.graph_builder.set_entry_point("fetch_news")
        self.graph_builder.add_edge("fetch_news","summarize_news")
        self.graph_builder.add_edge("summarize_news","save_result")
        self.graph_builder.add_edge("save_result", END)

    



# If you already import State/START/END/tools utilities at top, keep yours.
# from src.langgraphagenticai.state.state import State
# from langgraph.graph import START, END
# from src.langgraphagenticai.tools.tools import get_tools
# from src.langgraphagenticai.tools.tool_node import create_tool_node

    def brew_guide_agent_build_graph(self):
        """
        Brew Guide Agent graph with two loops:
        1) research_agent <-> tools (max 2 tool calls)
        2) draft <-> review (max 2 revisions)

        Flow:
        START -> research_agent -(conditional)-> tools -> research_agent ... -> extract -> draft -> review -(conditional)-> draft/finalize -> END
        """

        tools = get_tools()
        tool_node = create_tool_node(tools)

        llm = self.llm
        llm_with_tools = llm.bind_tools(tools)

        
   
        
        # -----------------------------
        # Helpers: routing decisions
        # -----------------------------
        def _has_tool_call(state: "State") -> bool:
            """Return True if the last assistant message includes a tool call request."""
            msgs = state.get("messages", [])
            if not msgs:
                return False
            last = msgs[-1]

            # Works for LangChain AIMessage with tool_calls
            tool_calls = getattr(last, "tool_calls", None)
            if tool_calls:
                return True

            # Some versions store it in additional_kwargs
            additional_kwargs = getattr(last, "additional_kwargs", {}) or {}
            if additional_kwargs.get("tool_calls"):
                return True

            return False

        def _route_after_research_agent(state: "State") -> str:
            """
            If the agent is requesting a tool call and we haven't exceeded max calls,
            go to tools. Otherwise move on to extract.
            """
            tool_calls_count = state.get("tool_calls_count", 0)

            if _has_tool_call(state) and tool_calls_count < 2:
                return "tools"
            return "extract"

        def _route_after_review(state: "State") -> str:
            """
            If review says needs_revision and under max revisions, go back to draft.
            Else finalize.
            """
            needs_revision = state.get("needs_revision", False)
            revision_count = state.get("revision_count", 0)

            if needs_revision and revision_count < 2:
                return "draft"
            return "finalize"

        # -----------------------------
        # Node: research_agent
        # -----------------------------
        def research_agent_node(state: "State"):
            """
            Agent step: decide search queries and (usually) call Tavily via tools.
            We strongly instruct it to use Tavily first, but allow it to stop after 1-2 calls.
            """
            messages = state.get("messages", [])
            tool_calls_count = state.get("tool_calls_count", 0)

            system = SystemMessage(content=
                "You are BrewGuideAgent.\n"
                "Goal: produce an accurate, practical brew guide.\n"
                "Step right now: RESEARCH ONLY.\n\n"
                "Rules:\n"
                f"- You may call the Tavily search tool up to 2 times. So far used: {tool_calls_count}.\n"
                "- Use Tavily to find credible guidance relevant to the user's query.\n"
                "- If you already have enough information from prior tool results in this conversation, DO NOT call tools again.\n"
                "- Do NOT write the brew guide yet. Only research and gather sources."
            )

            messages2 = [system] + messages
            resp = llm_with_tools.invoke(messages2)

            # If this response requested tool calls, increment counter (we will route to tools)
            new_tool_calls_count = tool_calls_count + (1 if _has_tool_call({"messages": [resp]}) else 0)

            return {
                "messages": [resp],
                "tool_calls_count": new_tool_calls_count
            }

        # -----------------------------
        # Node: extract
        # -----------------------------
        def extract_node(state: "State"):
            """
            Extract structured brew parameters from the research/tool outputs.
            """
            messages = state.get("messages", [])

            system = SystemMessage(content=
                "Extract brewing parameters and key guidance from the tool outputs in the conversation.\n"
                "Output ONLY markdown with these headings:\n"
                "## Assumptions\n"
                "## Starting recipe\n"
                "## Preheat\n"
                "## Preinfusion\n"
                "## Pressure/profile\n"
                "## Time targets\n"
                "## Dial-in rules\n"
                "## Notes/caveats\n"
                "Be precise. If something is uncertain, say it's a starting point."
            )

            resp = llm.invoke([system] + messages)
            return {"messages": [resp]}

        # -----------------------------
        # Node: draft
        # -----------------------------
        def draft_node(state: "State"):
            """
            Write the first brew guide draft (structured and actionable).
            """
            messages = state.get("messages", [])

            system = SystemMessage(content=
                "Write a beginner-friendly, step-by-step brew guide in MARKDOWN.\n"
                "Use the extracted parameters in the conversation.\n\n"
                "Required format:\n"
                "# Brew Guide\n"
                "## Quick recipe (dose / yield / temp)\n"
                "## Step-by-step workflow\n"
                "## Pressure / profile\n"
                "## Dial-in cheatsheet (sour / bitter / slow flow / channeling)\n"
                "## Safety notes\n"
                "## Sources (bulleted list of URLs if present in tool output)\n"
                "Keep it practical, not long."
            )

            resp = llm.invoke([system] + messages)
            return {"messages": [resp]}

        # -----------------------------
        # Node: review
        # -----------------------------
        def review_node(state: "State"):
            """
            Review the draft and decide if revision is needed.
            Sets needs_revision + increments revision_count.
            """
            messages = state.get("messages", [])
            revision_count = state.get("revision_count", 0)

            system = SystemMessage(content=
                "Review the latest brew guide draft in the conversation.\n"
                "Check for:\n"
                "- missing crucial steps (especially preheat / preinfusion for light roasts)\n"
                "- contradictions\n"
                "- unclear instructions\n"
                "- unsafe advice\n\n"
                "Return:\n"
                "1) A short markdown checklist of issues (if any)\n"
                "2) A final line EXACTLY: NEEDS_REVISION: yes/no"
            )

            resp = llm.invoke([system] + messages)
            text = (getattr(resp, "content", "") or "").lower()
            needs_revision = ("needs_revision: yes" in text)

            return {
                "messages": [resp],
                "needs_revision": needs_revision,
                "revision_count": revision_count + 1
            }

        # -----------------------------
        # Node: finalize
        # -----------------------------
        def finalize_node(state: "State"):
            """
            Produce the final brew guide, applying review feedback.
            """
            messages = state.get("messages", [])

            system = SystemMessage(content=
                "Rewrite the brew guide applying any review checklist feedback in the conversation.\n"
                "Output ONLY the final MARKDOWN brew guide. No extra commentary."
            )

            resp = llm.invoke([system] + messages)
            return {"messages": [resp]}

              # -----------------------------
        # Register nodes
        # -----------------------------
        self.graph_builder.add_node("research_agent", research_agent_node)
        self.graph_builder.add_node("tools", tool_node)
        self.graph_builder.add_node("extract", extract_node)
        self.graph_builder.add_node("draft", draft_node)
        self.graph_builder.add_node("review", review_node)
        self.graph_builder.add_node("finalize", finalize_node)

        # -----------------------------
        # Edges
        # -----------------------------
        self.graph_builder.add_edge(START, "research_agent")

        # Research loop (max 2 tool calls)
        #self.graph_builder.add_conditional_edges("research_agent", _route_after_research_agent)
        self.graph_builder.add_conditional_edges(
        "research_agent",
        _route_after_research_agent,
        {"tools": "tools", "extract": "extract"}
        )

        self.graph_builder.add_edge("tools", "research_agent")

        # Main pipeline after research
        self.graph_builder.add_edge("extract", "draft")
        self.graph_builder.add_edge("draft", "review")

        # Review loop (max 2 revisions)
        #self.graph_builder.add_conditional_edges("review", _route_after_review)
        self.graph_builder.add_conditional_edges(
         "review",
        _route_after_review,
         {"draft": "draft", "finalize": "finalize"}
            )
        # Final step
        self.graph_builder.add_edge("finalize", END)
        
    def setup_graph(self, usecase: str):
        """
        Sets up the graph for the selected use case.
        """
        if usecase == "Basic Chatbot":
            self.basic_chatbot_build_graph()
        elif usecase == "Chatbot with Web":
            self.chatbot_with_tools_build_graph()
        elif usecase == "AI News":
            self.ai_news_builder_graph()    
        elif usecase == "Brew Guide":
            self.brew_guide_agent_build_graph()
        return self.graph_builder.compile()
