import os
import streamlit as st
from langchain_openai import ChatOpenAI


class OpenAILLM:
    def __init__(self, user_controls_input):
        self.user_controls_input = user_controls_input

    def get_llm_model(self):
        try:
            openai_api_key = self.user_controls_input.get("OPENAI_API_KEY", "")
            selected_openai_model = self.user_controls_input.get(
                "selected_openai_model",
                "gpt-4o-mini"  # safe default
            )

            # Validation
            if openai_api_key == "" and os.environ.get("OPENAI_API_KEY", "") == "":
                st.error("Please enter the OpenAI API Key")
                return None

            llm = ChatOpenAI(
                api_key=openai_api_key,
                model=selected_openai_model,
                #temperature=0.1
            )

        except Exception as e:
            raise ValueError(f"Error occurred with exception: {e}")

        return llm