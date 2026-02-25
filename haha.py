import streamlit as st
import requests
import json
import re
import time

# ===== CONFIG PAGE =====
st.set_page_config(page_title="Shopee Link Converter", layout="centered")

# ===== CSS CLONE MUANGAY.INFO =====
st.markdown("""
<style>

.main-container {
    max-width: 850px;
    margin: auto;
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
}

.title {
    text-align:center;
    font-size:28px;
    font-weight:bold;
    margin-bottom:20px;
}

.label {
    font-weight:600;
    margin-bottom:5px;
}

textarea {
    font-size:14px !important;
}

.convert-btn button {
    width:100%;
    height:48px;
    font-size:18px;
    font-weight:bold;
    border-radius:8px;
}

.result-box {
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)


# ===== COOKIE PROCESS =====
def process_cookie_input(raw_input):

    if not raw_input:
        return ""

    try:

        cookie_data = json.loads(raw_input)

        if isinstance(cookie_data, dict) and "cookies" in cookie_data:

            cookies_list = cookie_data["cookies"]

        elif isinstance(cookie_data, list):

            cookies_list = cookie_data

        else:
            return raw_input


        formatted = []

        for c in cookies_list:

            if "name" in c and "value" in c:

                formatted.append(f"{c['name']}={c['value']}")

        return "; ".join(formatted)

    except:
        return raw_input



# ===== LOAD COOKIE =====
try:

    raw_cookie_secret = st.secrets["SHOPEE_COOKIE"]

    cookie_str = process_cookie_input(raw_cookie_secret)

except:

    st.error("Chưa cấu hình SHOPEE_COOKIE trong Secrets")

    st.stop()



# ===== API FUNCTION =====
def call_shopee_api(links_batch, sub_ids_dict):

    URL = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"

    headers = {

        "accept": "application/json",

        "content-type": "application/json",

        "cookie": cookie_str,

        "origin": "https://shopee.vn",

        "referer": "https://shopee.vn/",

        "user-agent": "Mozilla/5.0"

    }

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

            return resp.json()["data"]["batchCustomLink"]

        else:

            return []

    except:

        return []



# ===== MAIN UI =====
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<div class="title">Chuyển URL Shopee sang link Affiliate</div>', unsafe_allow_html=True)



# ===== SUBID =====
col1, col2 = st.columns(2)

with col1:
    sub1 = st.text_input("Sub ID", value="sharezalo")

with col2:
    sub2 = st.text_input("Sub ID1")


sub_ids = {}

if sub1:
    sub_ids["subId1"] = sub1

if sub2:
    sub_ids["subId2"] = sub2



# ===== TABS =====
tab1, tab2 = st.tabs(["📋 Danh sách link", "📝 Content"])



# ===== TAB 1 =====
with tab1:

    st.markdown('<div class="label">Nhập vào nội dung:</div>', unsafe_allow_html=True)

    raw_input = st.text_area("", height=220)


    if st.button("Chuyển đổi", use_container_width=True):

        if not raw_input.strip():

            st.warning("Vui lòng nhập link")

        else:

            input_links = [x.strip() for x in raw_input.split("\n") if x.strip()]

            total = len(input_links)

            st.info(f"Tìm thấy {total} link")


            final_links = []

            progress = st.progress(0)


            batch_size = 50


            for i in range(0, total, batch_size):

                chunk = input_links[i:i+batch_size]

                results = call_shopee_api(chunk, sub_ids)


                if results:

                    for r in results:

                        if r.get("shortLink"):

                            final_links.append(r["shortLink"])

                        else:

                            final_links.append("ERROR")

                else:

                    final_links.extend(["API_ERROR"] * len(chunk))


                progress.progress(min((i+batch_size)/total,1.0))

                time.sleep(0.1)


            result_text = "\n".join(final_links)


            st.markdown('<div class="result-box">', unsafe_allow_html=True)

            st.success("Nội dung chuyển đổi:")

            st.code(result_text, language="text")



# ===== TAB 2 =====
with tab2:

    st.markdown('<div class="label">Nhập content:</div>', unsafe_allow_html=True)

    content = st.text_area("", height=220)


    if st.button("Chuyển đổi content", use_container_width=True):

        if not content.strip():

            st.warning("Vui lòng nhập content")

        else:

            links = re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', content)

            unique = list(set(links))


            mapping = {}


            for i in range(0,len(unique),50):

                chunk = unique[i:i+50]

                results = call_shopee_api(chunk, sub_ids)


                if results:

                    for old,res in zip(chunk,results):

                        if res.get("shortLink"):

                            mapping[old] = res["shortLink"]



            final = content


            for old,new in mapping.items():

                final = final.replace(old,new)


            st.success("Content sau khi chuyển đổi:")

            st.code(final, language="markdown")



st.markdown('</div>', unsafe_allow_html=True)
