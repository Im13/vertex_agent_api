"""
Company Policy Agent with RAG (Retrieval-Augmented Generation)
Automatically searches across all company policy documents to answer questions.

This agent uses Vertex AI Search to:
1. Index all policy documents once
2. Automatically search relevant info when asked
3. Combine information from multiple documents
4. Cite sources in answers
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

# Get datastore ID from environment
# You'll need to create this in Google Cloud Console first
DATASTORE_ID = os.environ.get('COMPANY_POLICY_DATASTORE_ID', 'company-policies')

# Build full datastore path
full_datastore_id = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/locations/global/collections/default_collection/dataStores/{DATASTORE_ID}"

# Create the Vertex AI Search tool
policy_search_tool = VertexAiSearchTool(
    data_store_id=full_datastore_id
)

# Define the root agent
root_agent = LlmAgent(
    name="company_policy_agent",
    model="gemini-2.5-pro",
    tools=[policy_search_tool],
    instruction="""You are a Company Policy Assistant. Your role is to help employees understand company policies and procedures.

    When a user asks a question:
    1. ALWAYS use the search tool to find relevant information in company policy documents
    2. Base your answer ONLY on the information found in the documents
    3. CITE the source document and page number when possible
    4. If information is not found in the policies, clearly state that
    5. Be helpful and explain policies in clear, simple language

    Guidelines:
    - Use professional but friendly tone
    - Quote exact policy text when relevant
    - Explain implications or next steps if applicable
    - If policy is ambiguous, mention that and suggest contacting HR
    - Never make up or assume policies that aren't documented

    Example responses:
    - "According to the Employee Handbook (page 12), the annual leave policy states..."
    - "Based on the Remote Work Policy document, employees can work from home up to 3 days per week..."
    - "I couldn't find specific information about [topic] in the policy documents. I recommend contacting HR at hr@company.com for clarification."

    Remember: Always search the documents first before answering!
    """,
    description="Answers questions about company policies using Vertex AI Search across all policy documents."
)
