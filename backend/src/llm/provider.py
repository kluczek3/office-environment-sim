from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional
import os

import json
from langchain_core.output_parsers import JsonOutputParser

class LLMProvider:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        # Defaulting to local ChatOllama as per requirements
        self.llm = self._initialize_local_model()

    def _initialize_local_model(self):
        """Initializes the ChatOllama model."""
        return ChatOllama(model=self.model_name, temperature=0.7)

    def switch_to_cloud(self, provider: str, api_key: str):
        """Method to swap to cloud models (e.g., openai, gemini) if needed."""
        if provider.lower() == "openai":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(api_key=api_key, model="gpt-4-turbo", temperature=0.7)
        elif provider.lower() == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-pro", temperature=0.7)
        else:
            raise ValueError(f"Provider {provider} not supported.")
        self.model_name = getattr(self.llm, 'model_name', self.model_name)

    async def get_completion(self, system_prompt: str, user_prompt: str, require_json: bool = False):
        """Standardized generation method. If require_json is true, uses JsonOutputParser."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        if require_json:
            # Append JSON formatting instructions if needed
            parser = JsonOutputParser()
            format_instructions = parser.get_format_instructions()
            messages[0].content += f"\n\n{format_instructions}"
            
            chain = self.llm | parser
            response = await chain.ainvoke(messages)
            return response
        else:
            response = await self.llm.ainvoke(messages)
            return response.content
