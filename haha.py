import streamlit as st
import requests
import json
import re
import time

# ===== CẤU HÌNH GIAO DIỆN =====
st.set_page_config(page_title="Shopee Advanced Tool", layout="wide")
st.title("Chuyển Đổi Link Shopee ")

# ===== HÀM XỬ LÝ COOKIE THÔNG MINH =====
def process_cookie_input(raw_input):
    """
    Hàm này tự động phát hiện xem đầu vào là JSON hay chuỗi thường
    và convert về dạng chuẩn: key=value; key2=value2
    """
    if not raw_input:
        return ""
        
    try:
        # 1. Thử parse xem có phải là JSON không
        cookie_data = json.loads(raw_input)
        
        # Trường hợp 1: JSON dạng object có chứa key "cookies" (như mẫu bạn gửi)
        if isinstance(cookie_data, dict) and "cookies" in cookie_data:
            cookies_list = cookie_data["cookies"]
        # Trường hợp 2: JSON là một list ngay từ đầu
        elif isinstance(cookie_data, list):
            cookies_list = cookie_data
        else:
            # JSON hợp lệ nhưng không đúng cấu trúc mong muốn -> coi như chuỗi thường hoặc lỗi
            return raw_input

        # Convert list object thành chuỗi key=value;
        formatted_cookies = []
        for c in cookies_list:
            # Lấy name và value, bỏ qua nếu thiếu
            if "name" in c and "value" in c:
                formatted_cookies.append(f"{c['name']}={c['value']}")
        
        return "; ".join(formatted_cookies)

    except json.JSONDecodeError:
        # 2. Nếu lỗi JSON -> Đây là chuỗi cookie thô (key=value;...)
        # Trả về nguyên bản
        return raw_input

# ===== LOAD VÀ XỬ LÝ COOKIE =====
try:
    raw_cookie_secret = st.secrets["SHOPEE_COOKIE"]
    # Gọi hàm xử lý để convert JSON sang chuỗi chuẩn (nếu cần)
    cookie_str = process_cookie_input(raw_cookie_secret)
except Exception:
    st.error("Chưa cấu hình 'SHOPEE_COOKIE' trong Secrets!")
    st.stop()

# Kiểm tra nhanh xem cookie có hợp lệ không
if not cookie_str or "=" not in cookie_str:
    st.warning("Cảnh báo: Format Cookie có vẻ không đúng. Hãy kiểm tra lại Secrets.")

# ===== KHU VỰC CẤU HÌNH SUB_ID (DÙNG CHUNG) =====
with st.expander("Cấu hình SubID (Tùy chọn)", expanded=False):
    cols = st.columns(5)
    sub_ids = {}
    for i, col in enumerate(cols):
        val = col.text_input(f"SubID {i+1}", key=f"sub_{i+1}")
        if val.strip():
            sub_ids[f"subId{i+1}"] = val.strip()

# ===== HÀM GỌI API (XỬ LÝ CHUNK 50 LINK) =====
def call_shopee_api(links_batch, sub_ids_dict):
    """
    Hàm này nhận vào list tối đa 50 links và trả về danh sách kết quả tương ứng.
    """
    URL = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br", 
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,fr-FR;q=0.7,fr;q=0.6",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "cookie": cookie_str, # Đã được xử lý chuẩn format
        "origin": "https://shopee.vn",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://shopee.vn/",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }

    # Xây dựng linkParams
    link_params = []
    for link in links_batch:
        item = {"originalLink": link}
        if sub_ids_dict:
            item["advancedLinkParams"] = sub_ids_dict
        link_params.append(item)

    payload = {
        "operationName": "batchGetCustomLink",
        "query": """
        query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) {
          batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) {
            shortLink
            longLink
            failCode
          }
        }
        """,
        "variables": {
            "linkParams": link_params,
            "sourceCaller": "CUSTOM_LINK_CALLER"
        }
    }

    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('data', {}).get('batchCustomLink', [])
        else:
            # Silent fail hoặc log nhẹ
            return []
    except Exception as e:
        return []

# ===== GIAO DIỆN TABS =====
tab1, tab2 = st.tabs(["📋 Chuyển đổi danh sách Link", "📝 Chuyển đổi bài viết (Content)"])
with tab1:

    # ===== CSS giống 100% container HTML =====
    st.markdown("""
    <style>

    .container-box {
        max-width: 800px;
        margin: auto;
        background: #ffffff;
        padding: 25px;
        border-radius: 8px;
        border: 1px solid #ddd;
    }

    .container-box h2 {
        text-align: center;
        margin-bottom: 20px;
    }

    .processed-text p {
        margin-bottom: 5px;
        font-weight: 500;
    }

    .textarea-wrapper {
        position: relative;
    }

    textarea {
        width: 100% !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        padding: 10px !important;
        font-size: 14px !important;
    }

    .outside-button {
        position: absolute;
        right: 10px;
        top: 10px;
        background: #f1f1f1;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 4px 10px;
        cursor: pointer;
    }

    .sub-id-container {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .sub-id-container input {
        flex: 1;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    div.stButton > button {
        width: 100%;
        background-color: #007bff;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 4px;
        font-size: 15px;
        font-weight: bold;
    }

    div.stButton > button:hover {
        background-color: #0056b3;
    }

    .footer {
        margin-top: 30px;
        font-size: 14px;
    }

    </style>
    """, unsafe_allow_html=True)


    # ===== Container =====
    st.markdown('<div class="container-box">', unsafe_allow_html=True)

    st.markdown("<h2>Chuyển URL Shopee & Lazada sang link rút gọn</h2>", unsafe_allow_html=True)


    # ===== Input =====
    st.markdown('<div class="processed-text"><p>Nhập vào nội dung:</p></div>', unsafe_allow_html=True)

    raw_input = st.text_area(
        label="input_main",
        height=200,
        key="input_main"
    )


    # ===== Sub ID =====
    col1, col2 = st.columns(2)

    with col1:
        sub_id = st.text_input("Sub ID", value="sharezalo", key="sub_id")

    with col2:
        sub_id1 = st.text_input("Sub ID1", key="sub_id1")


    # ===== Button =====
    if st.button("Chuyển đổi", key="convert_main"):

        if not raw_input.strip():

            st.warning("Vui lòng nhập nội dung")

        else:

            input_links = [
                line.strip()
                for line in raw_input.split("\n")
                if line.strip()
            ]

            total_links = len(input_links)

            progress_bar = st.progress(0)

            final_short_links = []

            batch_size = 50

            sub_ids = {
                "sub_id": sub_id,
                "sub_id1": sub_id1
            }


            # ===== GIỮ NGUYÊN API LOGIC =====
            for i in range(0, total_links, batch_size):

                chunk = input_links[i:i+batch_size]

                results = call_shopee_api(chunk, sub_ids)

                if results:

                    for res in results:

                        if res.get("shortLink"):
                            final_short_links.append(res["shortLink"])
                        else:
                            final_short_links.append(
                                f"ERROR_FAIL_CODE_{res.get('failCode')}"
                            )

                else:

                    final_short_links.extend(
                        ["API_ERROR"] * len(chunk)
                    )


                progress_bar.progress(
                    min((i+batch_size)/total_links, 1.0)
                )

                time.sleep(0.1)


            result_text = "\n".join(final_short_links)


            # ===== Result =====
            st.markdown("<p><b>Nội dung chuyển đổi:</b></p>", unsafe_allow_html=True)

            st.text_area(
                label="result_box",
                value=result_text,
                height=200,
                key="result_box"
            )


            st.success("Hoàn tất!")


    # ===== Footer =====
    st.markdown("""
    <ul style="margin-top: 50px;">
        <li><b>Dùng ID khác</b>: https://muangay.info/convert?shopeeid=<span style="color:red;">17345060048</span>&lazadaid=<span style="color:red;">c.0w4XtoA</span></li>
        <li><b>Tạo ShortURL Shopee</b>: Tạo ở đây</li>
        <li><b>Thống kê</b>: Xem ở đây</li>
    </ul>

    <p style="text-align:right;">
        Code by Nguyễn Hùng
    </p>
    """, unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)

            
# ================= TAB 2: CHUYỂN ĐỔI CONTENT =================
with tab2:
    st.write("Dán toàn bộ bài viết quảng cáo vào đây. Tool sẽ tự tìm link `s.shopee.vn` và thay thế bằng link Affiliate của bạn.")
    content_input = st.text_area("Input Content", height=200, placeholder="Siêu sale tại https://s.shopee.vn/xyz ...")

    if st.button("🔄 Chuyển Đổi Link", key="btn_tab2"):
        if not content_input.strip():
            st.warning("Vui lòng nhập nội dung!")
        else:
            # Regex bắt link https://s.shopee.vn/xxxxx
            found_links = re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', content_input)
            unique_links = list(set(found_links))
            
            if not unique_links:
                st.warning("Không tìm thấy link s.shopee.vn nào trong bài viết!")
            else:
                st.info(f"Tìm thấy {len(unique_links)} link rút gọn. Đang xử lý...")
                
                link_mapping = {}
                batch_size = 50
                
                for i in range(0, len(unique_links), batch_size):
                    chunk = unique_links[i : i + batch_size]
                    results = call_shopee_api(chunk, sub_ids)
                    
                    if results and len(results) == len(chunk):
                        for original, res in zip(chunk, results):
                            if res.get('shortLink'):
                                link_mapping[original] = res['shortLink']
                    
                final_content = content_input
                count_success = 0
                for old_link, new_link in link_mapping.items():
                    if new_link:
                        final_content = final_content.replace(old_link, new_link)
                        count_success += 1
                
                st.success(f"Đã thay thế thành công {count_success}/{len(unique_links)} link! Bấm vào nút Copy ở góc phải bên dưới 👇")
                
                # --- Thay đổi: Dùng st.code để có nút copy ---
                st.code(final_content, language="markdown")




