import json

from  google.adk.agents.llm_agent import Agent
from  google.adk.tools.mcp_tool.mcp_toolset import MCPToolset,StdioServerParameters
from  google.adk.models.lite_llm import LiteLlm


from ocr_agent.prompt import OCR_PROMPT


def create_ocr_agent() -> Agent:
    return Agent(
        name="web_search_agent",
        model="gemini-2.0-flash",
        description="Agent that answers user queries by performing web searches.",
        instruction=OCR_PROMPT,
        tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "firecrawl-mcp"],
                    env={
                        "FIRECRAWL_API_KEY": "fc-9c8bbdeff8d248dbaec414064b0b7a9d"
                    }
                
            )
        ),
    ],
    )

root_agent = create_ocr_agent()