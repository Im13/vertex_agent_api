import os
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

PRIMARY_DATASTORE_ID = os.environ.get('COMPANY_POLICY_PRIMARY_DATASTORE_ID')
project = os.environ['GOOGLE_CLOUD_PROJECT']
primary_datastore_path = f"projects/{project}/locations/global/collections/default_collection/dataStores/{PRIMARY_DATASTORE_ID}"

primary_search_tool = VertexAiSearchTool(data_store_id=primary_datastore_path)

primary_agent = LlmAgent(
    name="primary_policy_agent",
    model="gemini-2.5-pro",
    tools=[primary_search_tool],
    instruction="""Search tài liệu chính sách chính và trả lời ngay.
    Nếu KHÔNG tìm thấy, trả lời chính xác: "PRIMARY_NOT_FOUND"
    """
)
