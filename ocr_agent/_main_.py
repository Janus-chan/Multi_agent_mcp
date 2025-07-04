import logging
import os

# Add parent directory to Python path for imports
from pathlib import Path

parent_dir = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(parent_dir))

import click
import uvicorn

# A2A server imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

# ADK imports
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
try:
    # Try absolute imports first (when run from parent directory)
    from ocr_agent.agent_executor import OcrExecutor
    from ocr_agent.agent import create_ocr_agent
except ImportError:
    # Fall back to relative imports (when run from ocr_agent directory)
    from agent_executor import OcrExecutor
    from agent import create_ocr_agent

# Basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--host",
    "host",
    default=os.getenv("A2A_OCR_HOST", "localhost"),
    show_default=True,
    help="Host for the OCR agent server."
)
@click.option(
    "--port",
    "port",
    default=int(os.getenv("A2A_OCR_PORT", 8003)),  # Default port for OCR agent
    show_default=True,
    type=int,
    help="Port for the OCR agent server."
)

def main(host: str, port: int) -> None:

    # No specific API key validation needed for OCR MCP tool
    logger.info("Initializing OCR Agent with MCP OCR tool integration")

    ocr_skill = AgentSkill(
        id="image_ocr_processing",
        name="Process images with OCR",
        description="Takes an array of images and extracts text content using OCR, providing detailed analysis and updated metadata.",
        tags=["ocr", "image", "text-extraction", "analysis"],
        examples=[
            "Process these document images for text extraction",
            "Analyze and extract content from multiple screenshots",
            "OCR processing for batch image analysis"
        ],
    )

    agent_card = AgentCard(
        name="OCR Image Processing Agent",
        description="Processes arrays of images using OCR capabilities to extract text and provide detailed analysis.",
        url=f"http://{host}:{port}/",  # URL is dynamically set here
        version="1.0.0",
        defaultInputModes=["text", "image"],  # Agent takes text and image inputs
        defaultOutputModes=["text"],  # Agent outputs structured text results
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),  # OCR is batch processing
        skills=[ocr_skill]
    )

    agent = create_ocr_agent()

    runner = Runner(
    agent=agent,
    app_name=agent_card.name,
    artifact_service=InMemoryArtifactService(),
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
    )

    agent_executor = OcrExecutor(
        agent=agent,
        agent_card=agent_card,
        runner=runner,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # Build the app with custom endpoint paths
    app = a2a_app.build(
        agent_card_url="/.well-known/agent.json",
        rpc_url="/a2a/ocr_agent",
        extended_agent_card_url="/agent/authenticatedExtendedCard"
    )

    logger.info(f"Starting OCR Agent server on http://{host}:{port}")
    logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")
    logger.info(f"A2A RPC Endpoint: http://{host}:{port}/a2a/ocr_agent")
    logger.info(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
    if agent_card.skills:
        for skill in agent_card.skills:
            logger.info(f" Skill: {skill.name} (ID: {skill.id}, Tags: {skill.tags})")

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
        main()
