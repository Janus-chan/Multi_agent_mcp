import json

from  google.adk.agents.llm_agent import Agent
from  google.adk.tools.mcp_tool.mcp_toolset import MCPToolset,StdioServerParameters
from  google.adk.models.lite_llm import LiteLlm


from ocr_agent.prompt import OCR_PROMPT


def create_ocr_agent() -> Agent:
    return Agent(
        name="ocr_agent",
        model="gemini-2.0-flash",
        description="Agent that processes images and extracts content using OCR capabilities.",
        instruction=OCR_PROMPT,
        tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                    command="python",
                    args=["-m", "mcp_ocr"],
                    env={}
            )
        ),
    ],
    )

root_agent = create_ocr_agent()
