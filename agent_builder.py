
import os
from message import Message
import ollama
from groq import Groq
import openai
from dotenv import load_dotenv
from typing import Union, List


load_dotenv()

class Agent:
    def __init__(self, backend="groq", model_name="llama3-8b-8192", cache = None):
        self.model_name = model_name
        self.cache = cache
        self.backend = backend
        self.token_limit = 7500
        self.conversation_history = []
        self.role = "user"

        if backend == "groq":
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_TOKEN"))
        elif backend == "openai":
            openai.api_key = os.environ["OPENAI_API_KEY"]
            self.openai_client = openai.OpenAI()
        elif backend == "ollama":
            pass
        else:
            raise ValueError("Please provide a valid inference")

    def __str__(self) -> str:
        return f"Agent(model_name={self.model_name})"

    def get_completion(self, prompt, system_message="You are a helpful assistant."):

        print(prompt)
        if self.backend == "ollama":
            response = ollama.chat(
                model=self.model_name,#"llama3:8b",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        elif self.backend == "groq":
            chat_completion = self.groq_client.chat.completions.create(
                model=self.model_name,#"llama3-70b-8192",
                temperature=0,
                messages=prompt,
                response_format={"type": "json_object"}
            )
            return chat_completion.choices[0].message.content
        elif self.backend == "openai":
            completion = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=prompt,
                        response_format={ "type": "json_object" }
            )
            return completion.choices[0].message.content
        else:
            raise ValueError("Please provide a valid inference: 'ollama' or 'groq'")

    def add_system_message(self, message):
        self.conversation_history.append({"role": message.role, "content": message.content})
    
    def _generate(
        self, message: Union[Message, List[Message]]
    ):
        
        # Add user message(s) to history
        if isinstance(message, list):
            for m in message:
                self.conversation_history.append({
                    "role": m.role,
                    "content": m.content
                })
        elif message is None:
            pass
        else:
            self.conversation_history.append({
                "role": message.role,
                "content": message.content
            })

        # Get response from API
        print(self.conversation_history)
        response = self.get_completion(self.conversation_history)
        message = Message(self.role, response)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": self.role,
            "content": response
        })

        return message


    def generate(self, message: Message) -> Message:

        response = self._generate(message)

        return response
