import os
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

SECONDARY_DATASTORE_ID = os.environ.get('COMPANY_POLICY_DATASTORE_ID')
project = os.environ['GOOGLE_CLOUD_PROJECT']
secondary_datastore_path = f"projects/{project}/locations/global/collections/default_collection/dataStores/{SECONDARY_DATASTORE_ID}"

secondary_search_tool = VertexAiSearchTool(data_store_id=secondary_datastore_path)

secondary_agent = LlmAgent(
    name="secondary_policy_agent",
    model="gemini-2.5-pro",
    tools=[secondary_search_tool],
    instruction="""Search tài liệu chính sách và trả lời ngay.
    Nếu KHÔNG tìm thấy, nói rõ "Không tìm thấy thông tin này trong tài liệu chính sách".
    """
)
