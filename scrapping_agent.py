from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from bs4 import BeautifulSoup
import requests
from typing import Optional, Type, Any
from pydantic import BaseModel, Field
import re
from urllib.parse import urljoin


class URLNavigatorInput(BaseModel):
    url: str = Field(description="URL to navigate to")

class WebPageScraperTool(BaseTool):
    name: str = "web_page_scraper"
    description: str = "Useful for getting the content of a web page. Input should be a URL."
    args_schema: Type[BaseModel] = URLNavigatorInput
    
    def _run(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            return f"Error fetching webpage: {str(e)}"

    def _arun(self, url: str) -> Any:
        raise NotImplementedError("Async not implemented")

class LinkExtractorTool(BaseTool):
    name: str = "link_extractor"
    description: str = "Useful for extracting links from a webpage. Input should be a URL."
    args_schema: Type[BaseModel] = URLNavigatorInput
    
    def _run(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(url, href)
                link_text = link.get_text().strip()
                if link_text:  # Only include links with text
                    links.append(f"{link_text}: {absolute_url}")
            
            return "\n".join(links)
        except Exception as e:
            return f"Error extracting links: {str(e)}"

    def _arun(self, url: str) -> Any:
        raise NotImplementedError("Async not implemented")
    


def create_thesis_opportunities_agent(openai_api_key: str):
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4o",
        openai_api_key=openai_api_key,
        
    )
    
    tools = [
        Tool(
            name="web_page_scraper",
            func=WebPageScraperTool()._run,
            description="Useful for getting the content of a web page. Input should be a URL."
        ),
        Tool(
            name="link_extractor",
            func=LinkExtractorTool()._run,
            description="Useful for extracting links from a webpage. Input should be a URL."
        )
    ]
    
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,        
    )
    
    return agent