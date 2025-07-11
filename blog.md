## **Deploy Your First Azure AI Agent Service on Azure App Service**

## **1. Introduction**
Azure AI Agent Service is a fully managed service designed to empower developers to securely build, deploy, and scale high-quality, extensible AI agents without needing to manage the underlying compute and storage resources[1](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview). These AI agents act as "smart" microservices that can answer questions, perform actions, or automate workflows by combining generative AI models with tools that allow them to interact with real-world data sources[1](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview).

Deploying Azure AI Agent Service on Azure App Service offers several benefits:
- **Scalability**: Azure App Service provides automatic scaling options to handle varying loads.
- **Security**: Built-in security features ensure that your AI agents are protected.
- **Ease of Deployment**: Simplified deployment processes allow developers to focus on building and improving their AI agents rather than managing infrastructure[1](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview).

---

## **2. Prerequisites**
Before you begin deploying Azure AI Agent Service on Azure App Service, ensure you have the following prerequisites in place:

1. **Azure Subscription**: You need an active Azure subscription. If you don't have one, you can create a free account on the Azure portal[2](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart).

2. **Azure AI Foundry Access**: Azure AI Foundry is the platform where you create and manage your AI agents. Ensure you have access to Azure AI Foundry and have the necessary permissions to create hubs and projects[2](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart).

3. **Basic Knowledge of Azure App Service**: Familiarity with Azure App Service is essential for configuring and deploying your AI agent. Understanding the basics of resource groups, app services, and hosting plans will be beneficial[2](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart).

4. **Development Environment**: Set up your development environment with the required tools and SDKs. This includes:
	- **Azure CLI**: For managing Azure resources from the command line.
	- **Azure AI Foundry SDK**: For creating and managing AI agents.
	- **Code Editor**: Such as Visual Studio Code, for writing and editing your deployment scripts.

---

## **3. Setting Up Azure AI Agent Service**

To harness the capabilities of Azure AI Agent Service, follow these steps to set up the environment:

**a. Create an Azure AI Hub and Project**

Begin by establishing an AI Hub and initiating a new project within Azure AI Foundry:

1. **Access Azure Portal:** Log in to the [Azure Portal](https://portal.azure.com/) using your Azure credentials.

2. **Create AI Hub:**
   - Navigate to the search bar and search for "AI Foundry"
   - Select "AI Foundry" and click "Create" and select "Hub".
   - Provide necessary details such as subscription, resource group, region, name and connect AI services.
   - Review and create the AI Hub.

3. **Create a Project:**
   - Within the newly created AI Hub, click "Launch Azure AI Foundry"
   - Under your new AI Hub, click "New project" and click "Create".

**b. Deploy an Azure OpenAI Model**

With the project in place, deploy a suitable AI model:

1. **Model Deployment:**
	- On the left-hand side of the project panel, select "Models + Endpoints" and click "Deploy model"
	- Select "Deploy base model" and choose "gpt-4o" and click "Confirm"
	- Leave the default settings and click "Deploy"

Detailed guidance is available in the [Quickstart documentation](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart).

---

## **4. Create and Configure the AI Agent**

After setting up the environment and deploying the model, proceed to create the AI agent:

- On the left-hand side of the project panel, select "Agents".
- Click "New agent" and the default agent will be created which already connected to your Azure OpenAI model.

1. **Define Instructions:**
   - Craft clear and concise instructions that guide the agent's interactions. For example:
     ```python
     instructions = "You are a helpful assistant capable of answering queries and performing tasks."
     ```

2. **Integrate Tools:**
   - Incorporate tools to enhance the agent's capabilities, such as:
     - **Code Interpreter:** Allows the agent to execute code for data analysis.
     - **OpenAPI Tools:** Enable the agent to interact with external APIs.
   - Enable Code Interpreter tool:
     - Still on the agent settings, in the "Actions" section, click "Add" and select "Code interpreter" and click "Save".
	 - On the same agent settings panel at the top, click "Try in playground".
	 - Do some quick test by entering "Hi" to the agent.

---

## **5. Develop a Chat Application**

Utilize the Azure AI Foundry SDK to instantiate and integrate up the agent.
In this tutorial we will be using **chainlit** - an open-source Python package to quickly build  Conversational AI application.

1. **Setup your local development environment:**
	- Follow the steps below from cloning the repository to running the chainlit application.
	- You can find the "Project connection string" inside your project "Overview" section in AI Foundry.
	- Still in AI Foundry, "Agent ID" can be found inside your "Agents" section.
		 ```bash
		1. git clone -b Deploy-AI-Agent-App-Service https://github.com/robrita/tech-blogs
		2. copy sample.env to .env and update
		3. python -m venv venv
		4. .\venv\Scripts\activate
		5. python -m pip install -r requirements.txt
		6. chainlit run app.py
		 ```

2. **Full code for reference:**
   ```python
	import os
	import chainlit as cl
	import logging
	from dotenv import load_dotenv
	from azure.ai.projects import AIProjectClient
	from azure.identity import DefaultAzureCredential
	from azure.ai.projects.models import (
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
	project_client = AIProjectClient.from_connection_string(
		conn_str=AIPROJECT_CONNECTION_STRING, credential=DefaultAzureCredential()
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
			run = project_client.agents.create_and_process_run(thread_id=thread_id, agent_id=AGENT_ID)
			print(f"Run finished with status: {run.status}")

			# Check if you got "Rate limit is exceeded.", then you want to increase the token limit
			if run.status == "failed":
				raise Exception(run.last_error)

			# Get all messages from the thread
			messages = project_client.agents.list_messages(thread_id)

			# Get the last message from the agent
			last_msg = messages.get_last_text_message_by_role(MessageRole.AGENT)
			if not last_msg:
				raise Exception("No response from the model.")

			msg.content = last_msg.text.value
			await msg.update()

		except Exception as e:
			await cl.Message(content=f"Error: {str(e)}").send()

	if __name__ == "__main__":
		# Chainlit will automatically run the application
		pass
	```

3. **Test Agent Functionality:**
Ensure the agent operates as intended.

---

## **6. Deploying on Azure App Service**
Deploying a Chainlit application on Azure App Service involves creating an App Service instance, configuring your application for deployment, and ensuring it runs correctly in the Azure environment. Here's a step-by-step guide:

1. **Create an Azure App Service Instance:**
	- **Log in to the Azure Portal**: Access the [Azure Portal](https://portal.azure.com/) and sign in with your Azure account.

	- **Create a New Web App**:
	  - Navigate to "App Services" and select "Create".
	  - Fill in the necessary details:
		- **Subscription**: Choose your Azure subscription.
		- **Resource Group**: Select an existing resource group or create a new one.
		- **Name**: Enter a unique name for your web app.
		- **Publish**: Choose "Code".
		- **Runtime Stack**: Select "Python 3.12" or higher.
		- **Region**: Choose the region closest to your users.

	- **Review and Create**: After filling in the details, click "Review + Create" and then "Create" to provision the App Service.

2. **Update Azure App Service Settings:**
	- **Environment Variables**: Add both "AIPROJECT_CONNECTION_STRING" and "AGENT_ID"

	- **Configuration**:
		- Set Startup Command to "startup.sh"
		- Turn "On" the "SCM Basic Auth Publishing Credentials" setting.
		- Tutn "On" the "Session affinity" setting.
		- Finally, click "Save".

	- **Identity**: Turn the status "On" under "System assigned" tab and click "Save".

3. **Assigned Role to your AI Foundry Project:**
	- In the Azure Portal, navigate to "AI Foundry" and select your Azure AI Project where the Agent was created.

	- Select "Access Control(IAM)" and click "Add" to add role assignment.

	- In the search bar, enter "AzureML Data Scientist" > "Next" > "Managed identity" > "Select members" > "App Service" > (Your app name) > "Review + Assign"

4. **Deploy Your Application to Azure App Service:**
	- **Deployment Methods**: Azure App Service supports various deployment methods, including GitHub Actions, Azure DevOps, and direct ZIP uploads. Choose the method that best fits your workflow.

	- **Using External Public Github**:
	  - In the Azure Portal, navigate to your App Service.
	  - Go to the "Deployment Center" and select the "External Git" deployment option.
	  - Enter "Repository" and "Branch".
	  - Keep "Public" and hit "Save".

	- **Check Your Deployment**:
	  - Still under "Deployment Center", click "Logs" tab to view the deployment status.
	  - Once success, head over to the "Overview" section of your App Service to test the "Default domain".

	- **Redeploy Your Application**:
	  - To redeploy your app, under "Deployment Center", click "Sync".

By following these steps, you can successfully deploy your Chainlit application on Azure App Service with first class Azure AI Agent Service integration, making it accessible to users globally.