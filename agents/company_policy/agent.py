from google.adk.agents import LlmAgent
from agents.company_policy.primary_agent import primary_agent
from agents.company_policy.secondary_agent import secondary_agent

root_agent = LlmAgent(
    name="company_policy_agent",
    model="gemini-2.5-pro",
    sub_agents=[primary_agent, secondary_agent],
    instruction="""Bạn là trợ lý chính sách công ty. Trả lời bằng tiếng Việt.

    THỨ TỰ XỬ LÝ:
    1. Chuyển câu hỏi cho primary_policy_agent TRƯỚC
    2. Nếu primary trả về "PRIMARY_NOT_FOUND" → chuyển cho secondary_policy_agent
    3. Nếu cả hai không tìm thấy → nói rõ không tìm thấy, đề xuất liên hệ phòng Nhân sự

    QUY TẮC:
    - Trả lời trực tiếp, không mở đầu bằng "Chào bạn"
    - Trích dẫn tên tài liệu và số trang
    - KHÔNG bịa thông tin
    """,
    description="Answers questions about company policies."
)
