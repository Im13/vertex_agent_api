import os
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

SECONDARY_DATASTORE_ID = os.environ.get('COMPANY_POLICY_DATASTORE_ID')
project = os.environ['GOOGLE_CLOUD_PROJECT']
secondary_datastore_path = f"projects/{project}/locations/global/collections/default_collection/dataStores/{SECONDARY_DATASTORE_ID}"

secondary_search_tool = VertexAiSearchTool(data_store_id=secondary_datastore_path)

secondary_agent = LlmAgent(
    name="secondary_policy_agent",
    model="gemini-2.5-flash",
    tools=[secondary_search_tool],
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
    - Nếu có bảng số liệu, trình bày dạng bảng rõ ràng.
    
    Nếu KHÔNG tìm thấy, nói rõ "Không tìm thấy thông tin này trong tài liệu chính sách".
    """
)
