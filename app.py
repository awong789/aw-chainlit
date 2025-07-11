import os
import asyncio
import chainlit as cl
import logging
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import (
    AgentThreadCreationOptions,
    ThreadMessageOptions,
    MessageTextContent,
    ListSortOrder,
    MessageRole,
)

    # Load environment variables
load_dotenv()

# Disable verbose connection logs
logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
logger.setLevel(logging.WARNING)

AIPROJECT_CONNECTION_STRING = os.getenv("AIPROJECT_CONNECTION_STRING")
AGENT_ID = os.getenv("AGENT_ID")

if not AIPROJECT_CONNECTION_STRING:
    raise ValueError("AIPROJECT_CONNECTION_STRING environment variable is required")
if not AGENT_ID:
    raise ValueError("AGENT_ID environment variable is required")

# Create an instance of the AIProjectClient using AsyncDefaultAzureCredential
project_client = AIProjectClient(
    endpoint=AIPROJECT_CONNECTION_STRING, credential=DefaultAzureCredential()
)


# Chainlit setup
@cl.on_chat_start
async def on_chat_start():
    if not AGENT_ID:
        raise ValueError("AGENT_ID environment variable is required")

    print(f"agent Id: {AGENT_ID}")
    # Create a thread for the agent
    if not cl.user_session.get("thread_id"):
        # thread = project_client.agents.create_thread_and_process_run(
        #     agent_id=AGENT_ID,
        #     thread=AgentThreadCreationOptions(
        #         messages=[ThreadMessageOptions(role="user", content="Hi! Tell me your favorite programming joke.")]
        #     ),
        # )
        run = await project_client.agents.create_thread_and_run(
            agent_id=AGENT_ID,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content="Hi! Tell me your favorite programming joke.")]
            ))
        
        # Poll the run as long as run status is queued or in progress
        while run.status in {"queued", "in_progress", "requires_action"}:
            await asyncio.sleep(1)
            run = await project_client.agents.runs.get(thread_id=run.thread_id, run_id=run.id)

            print(f"Run status: {run.status}")

        if run.status == "failed":
            print(f"Run error: {run.last_error}")

        cl.user_session.set("thread_id", run.thread_id)
        print(f"New Thread ID: {run.thread_id}")   

@cl.on_message
async def on_message(message: cl.Message): 
    thread_id = cl.user_session.get("thread_id")
    if not AGENT_ID:
        raise ValueError("AGENT_ID environment variable is required")

    if not thread_id:
        await cl.Message(content="Error: No active thread. Please restart the chat.").send()
        return
    
    try:
        # Show thinking message to user
        msg = await cl.Message("thinking...", author="agent").send()

        # 1. Add user's message to the thread
        await project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content,
        )

        # 2. Trigger the agent to process the new message
        run = await project_client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=AGENT_ID,
        )


        # Get all messages from the thread
        messages = project_client.agents.messages.list(
            thread_id=thread_id,
            order=ListSortOrder.ASCENDING
        )

        # Get the last message from the agent
        last_msg = await project_client.agents.messages.get_last_message_text_by_role(thread_id=thread_id, role=MessageRole.AGENT)
        # last_msg = await project_client.agents.messages.get_last_message_text_by_role(thread_id=run.thread_id,role=MessageRole.AGENT)
        if not last_msg:
            raise Exception("No response from the model.")

        # async for msg in messages:
        #     last_part = msg.content[-1]
        #     if isinstance(last_part, MessageTextContent):
        #         print(f"{msg.role}: {last_part.text.value}")
        #         msg.content = last_part.text.value

        print(f"agent: {last_msg.text.value}")
        msg.content = last_msg.text.value
        await msg.update()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

if __name__ == "__main__":
    # Chainlit will automatically run the application
    pass