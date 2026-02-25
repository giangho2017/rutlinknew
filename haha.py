import streamlit as st
import time, re

# ===== CSS GIAO DIỆN GIỐNG HTML MẪU =====
st.markdown("""
<style>
.main-container {
    max-width: 900px;
    margin: auto;
    background: #ffffff;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}

.title {
    text-align:center;
    font-size:28px;
    font-weight:700;
    margin-bottom:20px;
}

.textarea-label {
    font-weight:600;
    margin-bottom:5px;
}

.subid-container {
    display:flex;
    gap:10px;
    margin-top:10px;
    margin-bottom:10px;
}

.convert-btn {
    width:100%;
    height:50px;
    font-size:18px;
    font-weight:600;
    border-radius:8px;
}

.result-box {
    margin-top:20px;
}
</style>
""", unsafe_allow_html=True)


# ===== CONTAINER =====
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<div class="title">🔗 Chuyển URL Shopee & Lazada sang link Affiliate</div>', unsafe_allow_html=True)

# ===== INPUT SUBID =====
col1, col2 = st.columns(2)

with col1:
    sub_id = st.text_input("Sub ID", value="sharezalo")

with col2:
    sub_id1 = st.text_input("Sub ID1")

sub_ids = {
    "sub_id": sub_id,
    "sub_id1": sub_id1
}


# ===== TABS =====
tab1, tab2 = st.tabs(["📋 Chuyển đổi danh sách Link", "📝 Chuyển đổi bài viết (Content)"])


# ================= TAB 1 =================
with tab1:

    st.markdown("**Nhập danh sách link:**")

    raw_input = st.text_area(
        "",
        height=250,
        placeholder="https://shopee.vn/sp1...\nhttps://shopee.vn/sp2..."
    )

    if st.button("🚀 Chuyển đổi", use_container_width=True):

        if not raw_input.strip():

            st.warning("Vui lòng nhập link!")

        else:

            input_links = [line.strip() for line in raw_input.split('\n') if line.strip()]
            total_links = len(input_links)

            st.info(f"Tìm thấy {total_links} link. Đang xử lý...")

            final_short_links = []

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
                            final_short_links.append(f"ERROR_{res.get('failCode')}")

                else:
                    final_short_links.extend(["API_ERROR"] * len(chunk))


                progress_bar.progress(min((i + batch_size) / total_links, 1.0))

                time.sleep(0.1)


            result_text = "\n".join(final_short_links)

            st.success("✅ Hoàn tất!")

            st.code(result_text, language="text")



# ================= TAB 2 =================
with tab2:

    st.markdown("**Dán nội dung bài viết:**")

    content_input = st.text_area(
        "",
        height=250,
        placeholder="Siêu sale tại https://s.shopee.vn/xyz ..."
    )

    if st.button("🔄 Chuyển đổi", use_container_width=True):

        if not content_input.strip():

            st.warning("Vui lòng nhập nội dung!")

        else:

            found_links = re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', content_input)

            unique_links = list(set(found_links))


            if not unique_links:

                st.warning("Không tìm thấy link Shopee!")

            else:

                st.info(f"Tìm thấy {len(unique_links)} link. Đang xử lý...")


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

                    final_content = final_content.replace(old_link, new_link)

                    count_success += 1



                st.success(f"✅ Đã thay {count_success}/{len(unique_links)} link")

                st.code(final_content, language="markdown")


st.markdown('</div>', unsafe_allow_html=True)
