import os
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

    # Create a thread for the agent
    if not cl.user_session.get("thread_id"):
        thread = await project_client.agents.create_thread_and_process_run(
            agent_id=AGENT_ID,
            thread=AgentThreadCreationOptions(
                messages=[ThreadMessageOptions(role="user", content="Hi! Tell me your favorite programming joke.")]
            ),
        )

        cl.user_session.set("thread_id", thread.id)
        print(f"New Thread ID: {thread.id}")

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

        await project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content,
        )
        
        # Run the agent to process tne message in the thread
        run = await project_client.agents.create_thread_and_process_run(thread_id=thread_id, agent_id=AGENT_ID)
        print(f"Run finished with status: {run.status}")

        # Check if you got "Rate limit is exceeded.", then you want to increase the token limit
        if run.status == "failed":
            raise Exception(run.last_error)

        # Get all messages from the thread
        messages = project_client.agents.messages.list(thread_id=run.thread_id,
            order=ListSortOrder.ASCENDING,)

        # Get the last message from the agent
        last_msg = await project_client.agents.messages.get_last_message_text_by_role(thread_id=run.thread_id,role=MessageRole.AGENT)
        if not last_msg:
            raise Exception("No response from the model.")

        msg.content = last_msg.text.value
        await msg.update()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

if __name__ == "__main__":
    # Chainlit will automatically run the application
    pass