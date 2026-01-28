"""
Procurement Agent - Tìm kiếm và so sánh nhà cung cấp
Sử dụng Google Search để tìm nhà cung cấp, so sánh giá và trả về danh sách top 5.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search

# Define the procurement agent
root_agent = LlmAgent(
    name="procurement_agent",
    model="gemini-2.5-pro",
    tools=[google_search],
    instruction="""Bạn là trợ lý mua hàng. Nhiệm vụ: tìm kiếm nhà cung cấp bằng Google Search.

    QUY TẮC BẮT BUỘC:
    1. PHẢI sử dụng Google Search ngay khi nhận yêu cầu
    2. CHỈ trả về thông tin từ kết quả tìm kiếm thực tế
    3. KHÔNG ĐƯỢC tự bịa ra link, giá, hoặc tên nhà cung cấp
    4. Nếu không tìm thấy thông tin, nói rõ "Không tìm thấy"

    CÁCH TÌM KIẾM:
    - Search: "Mua [tên sản phẩm]"
    - Thu thập: tên shop, giá, URL từ kết quả search

    FORMAT TRẢ VỀ:

    ## Kết quả tìm kiếm: [Tên sản phẩm]

    | 1 | [Tên] | [Giá] | [URL thật từ search] |

    ### Đề xuất:
    - Giá tốt nhất: [Tên shop]

    LƯU Ý: Chỉ liệt kê nhà cung cấp có trong kết quả search. Link phải là URL gốc, không format markdown.
    """,
    description="Tìm kiếm và so sánh nhà cung cấp từ Google Search."
)
