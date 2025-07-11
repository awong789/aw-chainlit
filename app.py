import os
import chainlit as cl
import logging
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import (
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

# Create an instance of the AIProjectClient using DefaultAzureCredential
project_client = AIProjectClient(
    endpoint=AIPROJECT_CONNECTION_STRING, credential=DefaultAzureCredential()
)


# Chainlit setup
@cl.on_chat_start
async def on_chat_start():
    # Create a thread for the agent
    if not cl.user_session.get("thread_id"):
        thread = project_client.agents.create_thread()

        cl.user_session.set("thread_id", thread.id)
        print(f"New Thread ID: {thread.id}")

@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    
    try:
        # Show thinking message to user
        msg = await cl.Message("thinking...", author="agent").send()

        project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=message.content,
        )
        
        # Run the agent to process tne message in the thread
        run = project_client.agents.create_thread_and_process_run(thread_id=thread_id, agent_id=AGENT_ID)
        print(f"Run finished with status: {run.status}")

        # Check if you got "Rate limit is exceeded.", then you want to increase the token limit
        if run.status == "failed":
            raise Exception(run.last_error)

        # Get all messages from the thread
        messages = project_client.agents.messages.list(thread_id=run.thread_id,
            order=ListSortOrder.ASCENDING,)

        # Get the last message from the agent
        last_msg = messages.get_last_message_text_by_role(thread_id=run.thread_id,role=MessageRole.AGENT)
        if not last_msg:
            raise Exception("No response from the model.")

        msg.content = last_msg.text.value
        await msg.update()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()

if __name__ == "__main__":
    # Chainlit will automatically run the application
    pass