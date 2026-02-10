import streamlit as st
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import json


def make_debug_snapshot(res):
    msgs = res.get("messages", [])
    snapshot = {
        "message_types": [type(m).__name__ for m in msgs],
        "ai_previews": [],
        "tool_outputs": [],
    }

    for i, m in enumerate(msgs):
        if isinstance(m, AIMessage):
            content = getattr(m, "content", "") or ""
            snapshot["ai_previews"].append({
                "i": i,
                "len": len(content),
                "preview": content[:400],
                "additional_kwargs": getattr(m, "additional_kwargs", {}) if not content else {},
            })
        elif isinstance(m, ToolMessage):
            snapshot["tool_outputs"].append({
                "i": i,
                "content": getattr(m, "content", ""),
            })

    return snapshot


class DisplayResultStreamlit:
    def __init__(self,usecase,graph,user_message):
        self.usecase= usecase
        self.graph = graph
        self.user_message = user_message

    def display_result_on_ui(self):
        usecase= self.usecase
        graph = self.graph
        user_message = self.user_message
        print(user_message)
        if usecase =="Basic Chatbot":
                for event in graph.stream({'messages':("user",user_message)}):
                    print(event.values())
                    for value in event.values():
                        print(value['messages'])
                        with st.chat_message("user"):
                            st.write(user_message)
                        with st.chat_message("assistant"):
                            st.write(value["messages"].content)

        elif usecase=="Chatbot with Web":
             # Prepare state and invoke the graph
            initial_state = {"messages": [user_message]}
            # initial_state = {"messages": [HumanMessage(content=user_message)]}
            res = graph.invoke(initial_state)
            for message in res['messages']:
                if type(message) == HumanMessage:
                    with st.chat_message("user"):
                        st.write(message.content)
                elif type(message)==ToolMessage:
                    with st.chat_message("assistant"):
                        st.write("Tool Call Start")
                        st.write(message.content)
                        st.write("Tool Call End")
                elif type(message)==AIMessage and message.content:
                    with st.chat_message("assistant"):
                        st.write(message.content)

        elif usecase == "AI News":
            frequency = self.user_message
            with st.spinner("Fetching and summarizing news... "): #⏳
                result = graph.invoke({"messages": frequency})
                try:
                    # Read the markdown file
                    AI_NEWS_PATH = f"./AINews/{frequency.lower()}_summary.md"
                    with open(AI_NEWS_PATH, "r") as file:
                        markdown_content = file.read()

                    # Display the markdown content in Streamlit
                    st.markdown(markdown_content, unsafe_allow_html=True)
                except FileNotFoundError:
                    st.error(f"News Not Generated or File not found: {AI_NEWS_PATH}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        
        #######
        ######
        elif usecase == "Brew Guide":
            query = user_message

            # Show user query once
            with st.chat_message("user"):
                st.write(query)

            # Run the graph once
            with st.spinner("Researching & generating brew guide..."):
                initial_state = {
                    "messages": [HumanMessage(content=query)],
                    "tool_calls_count": 0,
                    "revision_count": 0,
                    "needs_revision": False,
                }

                try:
                    res = graph.invoke(initial_state)
                    st.session_state["brew_last_res"] = res
                    st.session_state["brew_last_query"] = query
                    st.session_state["brew_debug"] = make_debug_snapshot(res)
                except Exception as e:
                    st.error(f"Brew Guide failed: {e}")
                    raise
            
            saved_res = st.session_state.get("brew_last_res")
            if not saved_res:
                st.info("No Brew Guide result yet. Submit a query first.")
                return
            
            # DEBUG EXPANDER goes HERE (after invoke, before rendering final output)
            #   show_debug = st.checkbox("Show DEBUG", value=False)
            show_debug = st.checkbox("Show DEBUG", value=False, key="brew_show_debug")

            if show_debug:
                dbg = st.session_state.get("brew_debug")

                with st.expander("DEBUG: Brew Guide execution", expanded=True):
                    if not dbg:
                        st.warning("No debug snapshot found yet. Submit a Brew Guide query first.")
                    else:
                        st.write("Last query:")
                        st.write(st.session_state.get("brew_last_query", ""))

                        st.write("Message types:")
                        st.write(dbg["message_types"])

                        st.write("AIMessage previews:")
                        for item in dbg["ai_previews"]:
                            st.write(f'{item["i"]}: len={item["len"]}')
                            if item["preview"]:
                                st.write(item["preview"])
                            else:
                                st.write("(EMPTY AIMessage content)")
                                st.write("additional_kwargs:")
                                st.write(item["additional_kwargs"])

                        st.write("Tool outputs:")
                        for t in dbg["tool_outputs"]:
                            st.write(f'ToolMessage[{t["i"]}]')
                            st.write(t["content"])

            # Show final output only (last message)
            # final_msg = res["messages"][-1]
            # final_text = getattr(final_msg, "content", str(final_msg))
           
            ####
            # for m in reversed(res["messages"]):
            #     if isinstance(m, AIMessage) and getattr(m, "content", ""):
            #         final_text = m.content
            #         break
            
            # -------------------------
            # Pick best final answer
            # -------------------------

            # -------------------------
            # Pick best final answer
            # -------------------------
            final_text = ""

            def _clean(s: str) -> str:
                return (s or "").strip()

            # 1) Prefer a real Brew Guide (markdown OR plain text heading)
            for m in reversed(saved_res["messages"]):
                if isinstance(m, AIMessage):
                    content = _clean(getattr(m, "content", ""))
                    if (
                        "# Brew Guide" in content
                        or content.startswith("Brew Guide")
                        or "\nBrew Guide\n" in content
                    ):
                        final_text = content
                        break

            # 2) Fallback: pick the "best looking" long answer, excluding obvious meta text
            if not final_text:
                candidates = []
                #for m in res["messages"]:
                for m in saved_res["messages"]:
                    if isinstance(m, AIMessage):
                        content = _clean(getattr(m, "content", ""))
                        if not content:
                            continue
                        # exclude common meta replies
                        bad_starts = ("i hope", "here is", "based on", "sure,", "of course")
                        if content.lower().startswith(bad_starts):
                            continue
                        candidates.append(content)

                if candidates:
                    final_text = max(candidates, key=len)

            # 3) Final fallback: longest AIMessage content (even if meta)
            if not final_text:
                longest = ""
                #for m in res["messages"]:
                for m in saved_res["messages"]:
                    if isinstance(m, AIMessage):
                        content = _clean(getattr(m, "content", ""))
                        if len(content) > len(longest):
                            longest = content
                final_text = longest

            if not final_text:
                final_text = "No final Brew Guide produced. See DEBUG."

            # Normalize heading so Streamlit renders nicely
            if final_text.startswith("Brew Guide") and "# Brew Guide" not in final_text:
                final_text = "# " + final_text

            # with st.chat_message("assistant"):
            #     st.markdown(final_text)
                        
            
            
            with st.chat_message("assistant"):
                st.markdown(final_text)

            # Optional: show tool logs in an expander (keep if you want)
            with st.expander("Show research steps (optional)"):
                for m in saved_res["messages"]:
                    if type(m) == ToolMessage:
                        st.write(m.content)
        
        ###### 
        # elif usecase == "Brew Guide":
        #     query = user_message

        #     # Show user query once
        #     with st.chat_message("user"):
        #         st.write(query)

        #     # Spinner is optional but recommended (tool calls + loops can take time)
        #     with st.spinner("Researching & generating brew guide... ☕"):
        #         initial_state = {
        #             "messages": [HumanMessage(content=query)],
        #             "tool_calls_count": 0,
        #             "revision_count": 0,
        #             "needs_revision": False,
        #         }

        #         try:
        #             res = graph.invoke(initial_state)
        #         except Exception as e:
        #             st.error(f"Brew Guide failed: {e}")
        #             raise
            
            
        #     # =========================
        #     # DEBUG: inspect graph output
        #     # =========================
        #     with st.spinner("Researching & generating brew guide... "):#☕

        #         initial_state = {
        #             "messages": [HumanMessage(content=query)],
        #             "tool_calls_count": 0,
        #             "revision_count": 0,
        #             "needs_revision": False,
        #         }

        #         try:
        #             res = graph.invoke(initial_state)
        #         except Exception as e:
        #             st.error(f"Brew Guide failed: {e}")
        #             raise

        #     # Show final output only (last message)
        #     final_msg = res["messages"][-1]
        #     final_text = getattr(final_msg, "content", str(final_msg))
            
            
        #     # Show final output only (last message)
        #     final_msg = res["messages"][-1]
        #     final_text = getattr(final_msg, "content", str(final_msg))

        #     with st.chat_message("assistant"):
        #         st.markdown(final_text)

        #     # Optional: show tool logs in an expander
        #     with st.expander("Show research steps (optional)"):
        #         for m in res["messages"]:
        #             if type(m) == ToolMessage:
        #                 st.write(m.content)