import streamlit as st
import time, re

# ===== CSS giống HTML gốc =====
st.markdown("""
<style>

.container {
    max-width: 800px;
    margin: auto;
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.1);
}

.container h2 {
    text-align: center;
    margin-bottom: 20px;
}

.textarea-wrapper {
    position: relative;
}

textarea {
    width: 100%;
}

.outside-button {
    position: absolute;
    right: 10px;
    top: 10px;
    background: #ff5722;
    color: white;
    border: none;
    padding: 5px 12px;
    border-radius: 5px;
    cursor: pointer;
}

.convert-btn {
    width: 100%;
    height: 45px;
    font-size: 18px;
    margin-top: 15px;
}

.sub-id-container {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}

.result-area {
    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)


# ===== CONTAINER =====
st.markdown('<div class="container">', unsafe_allow_html=True)

st.markdown("<h2>Chuyển URL Shopee & Lazada sang link rút gọn</h2>", unsafe_allow_html=True)


# ===== INPUT CONTENT =====
st.write("Nhập vào nội dung:")

col_text, col_paste = st.columns([8,1])

with col_text:
    text_input = st.text_area(
        "",
        height=250,
        key="input_text"
    )

with col_paste:
    if st.button("Dán"):
        st.info("Streamlit không hỗ trợ paste clipboard trực tiếp trên web")


# ===== SUB ID =====
col1, col2 = st.columns(2)

with col1:
    sub_id = st.text_input("", value="sharezalo", placeholder="Sub ID")

with col2:
    sub_id1 = st.text_input("", placeholder="Sub ID1")


sub_ids = {
    "sub_id": sub_id,
    "sub_id1": sub_id1
}


# ===== BUTTON CONVERT =====
convert = st.button("Chuyển đổi", use_container_width=True)


# ===== RESULT AREA =====
if convert:

    if not text_input.strip():

        st.warning("Vui lòng nhập nội dung")

    else:

        # tìm link shopee
        found_links = re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', text_input)

        unique_links = list(set(found_links))

        if not unique_links:

            st.warning("Không tìm thấy link Shopee")

        else:

            st.info(f"Tìm thấy {len(unique_links)} link. Đang xử lý...")

            link_mapping = {}

            batch_size = 50

            progress_bar = st.progress(0)

            for i in range(0, len(unique_links), batch_size):

                chunk = unique_links[i : i + batch_size]

                results = call_shopee_api(chunk, sub_ids)

                if results and len(results) == len(chunk):

                    for original, res in zip(chunk, results):

                        if res.get('shortLink'):
                            link_mapping[original] = res['shortLink']


                progress_bar.progress(min((i+batch_size)/len(unique_links),1.0))

                time.sleep(0.1)


            final_text = text_input

            for old, new in link_mapping.items():
                final_text = final_text.replace(old, new)


            st.success("Nội dung chuyển đổi:")


            col_result, col_copy = st.columns([8,1])

            with col_result:
                st.text_area(
                    "",
                    value=final_text,
                    height=250,
                    key="result_text"
                )

            with col_copy:

                st.code(final_text, language="text")

                st.caption("Copy bằng nút góc phải")



# ===== FOOTER giống HTML =====
st.markdown("""
<br><br>
<ul>
<li><b>Dùng ID khác</b>: https://muangay.info/convert?shopeeid=17345060048&lazadaid=c.0w4XtoA</li>
<li><b>Tạo ShortURL Shopee</b>: /convert-shopee</li>
<li><b>Thống kê</b>: /listurl</li>
</ul>

<p style="text-align:right">Code by</p>

""", unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)
