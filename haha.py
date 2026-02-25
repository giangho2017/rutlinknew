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

# ================= TAB 1: DANH SÁCH LINK =================
with tab1:
    st.write("Nhập danh sách link Shopee (mỗi link 1 dòng):")
    raw_input = st.text_area("Input Links", height=200, placeholder="https://shopee.vn/sp1...\nhttps://shopee.vn/sp2...")
    
    if st.button("🚀 Chuyển Đổi Link", key="btn_tab1"):
        if not raw_input.strip():
            st.warning("Vui lòng nhập link!")
        else:
            input_links = [line.strip() for line in raw_input.split('\n') if line.strip()]
            total_links = len(input_links)
            st.info(f"Đã tìm thấy {total_links} links. Đang xử lý...")

            final_short_links = []
            
            # Chia nhỏ thành từng chunk 50 link
            batch_size = 50
            progress_bar = st.progress(0)
            
            for i in range(0, total_links, batch_size):
                chunk = input_links[i : i + batch_size]
                results = call_shopee_api(chunk, sub_ids)
                
                if results:
                    for res in results:
                        if res.get('shortLink'):
                            final_short_links.append(res['shortLink'])
                        else:
                            final_short_links.append(f"ERROR_FAIL_CODE_{res.get('failCode')}")
                else:
                    final_short_links.extend(["API_ERROR"] * len(chunk))
                
                progress_bar.progress(min((i + batch_size) / total_links, 1.0))
                time.sleep(0.1)

            st.success("Hoàn tất! Bấm vào nút Copy ở góc phải bên dưới 👇")
            result_text = "\n".join(final_short_links)
            
            # --- Thay đổi: Dùng st.code để có nút copy ---
            st.code(result_text, language="text")

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



