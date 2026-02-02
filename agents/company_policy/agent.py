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
    instruction="""Bạn là trợ lý chính sách công ty. Trả lời bằng tiếng Việt.

    QUY TẮC BẮT BUỘC:
    1. Khi nhận câu hỏi, SEARCH NGAY LẬP TỨC rồi TRẢ LỜI NGAY trong cùng một lượt. KHÔNG BAO GIỜ nói "tôi sẽ tìm kiếm" hay "để tôi tìm" rồi dừng lại.
    2. CHỈ dựa trên thông tin tìm được từ tài liệu. KHÔNG bịa thông tin.
    3. Trích dẫn tên tài liệu và số trang khi có.
    4. Nếu không tìm thấy, nói rõ "Không tìm thấy thông tin này trong tài liệu chính sách" và đề xuất liên hệ phòng Nhân sự.
    5. Khi người dùng phản hồi rằng thông tin sai hoặc hỏi thêm, SEARCH LẠI rồi TRẢ LỜI NGAY. Không nói "tôi sẽ tìm lại" rồi dừng.

    CÁCH TRẢ LỜI:
    - Trả lời trực tiếp, ngắn gọn, đúng trọng tâm
    - Không mở đầu bằng "Chào bạn" hay lời dẫn dài dòng
    - Không hứa hẹn "sẽ tìm kiếm" - hãy tìm và trả lời luôn
    - Nếu có bảng số liệu, trình bày dạng bảng rõ ràng
    """,
    description="Answers questions about company policies using Vertex AI Search across all policy documents."
)
