from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from typing import Optional
import os
import json

class LLMProvider:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.llm = self._initialize_local_model()

    def _initialize_local_model(self):
        return ChatOllama(model=self.model_name, temperature=0.7)

    def switch_to_cloud(self, provider: str, api_key: str):
        if provider.lower() == "openai":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0.7)
        elif provider.lower() == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(google_api_key=api_key, model="gemini-pro", temperature=0.7)
        else:
            raise ValueError(f"Provider {provider} not supported.")
        self.model_name = getattr(self.llm, 'model_name', self.model_name)

    async def get_completion(self, system_prompt: str, user_prompt: str, require_json: bool = False):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        if require_json:
            parser = JsonOutputParser()
            format_instructions = parser.get_format_instructions()
            messages[0].content += f"\n\n{format_instructions}"
            chain = self.llm | parser
            return await chain.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)
            return response.content