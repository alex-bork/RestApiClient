import streamlit as st 
import requests as rq
import json
from modules import *
import os


st.subheader("HR | REST API Tester")


if "auth_active" not in st.session_state:
    init_auth_form()

if "request_headers" not in st.session_state:
    st.session_state.request_headers = {}

if "requests_session" not in st.session_state:
    st.session_state.requests_session = rq.Session()


with st.sidebar:
    init_sidebar_auth()
    init_sidebar_responses()

init_request_method_url()
"######"
init_request_headers()
"######"
init_request_body()


col1, col2, col3 = st.columns([3, 4, 4], vertical_alignment="top")
with col1:
    send_request = st.button("Send request", type="primary", icon=":material/send:")
with col2:
    with st.expander('Save request'):
        download_filename = st.text_input("Supply file name and push Enter")
        if len(download_filename) > 0:
            st.write(f"{download_filename}.hrrest")
        st.download_button(
            f"Download",
            type="primary",
            data=json.dumps(
                {
                    "request_method": st.session_state.request_method,
                    "request_url": st.session_state.request_url,
                    "request_headers": st.session_state.request_headers,
                    "request_body": st.session_state.request_body,
                }
            ),
            file_name=(
                f"{download_filename}.hrrest"
                if download_filename
                else f"{st.session_state.request_url}.hrrest"
            ),
            disabled=True if len(download_filename) == 0 else False,
            icon=":material/download:"
        )
with col3:
    with st.expander("Load request"):
        file =  st.file_uploader("Click or drop file here", type="hrrest")
        st.button("Upload", 
                  type="primary", 
                  on_click=set_request_data, 
                  args=[file], 
                  icon=":material/upload:", 
                  disabled=True if not file else False)

if send_request:
    request_method = st.session_state.request_method
    request_url = st.session_state.request_url
    request_body = st.session_state.request_body

    try:
        if str(st.session_state.request_url[0:4]).upper() != "HTTP":
            st.error("Missing web protocol in url.")
            st.stop()

        request_headers = {
            header: st.session_state.request_headers[header]["value"]
            for header in st.session_state.request_headers
        }

        use_auth(st.session_state.requests_session, request_headers)

        if request_method == "GET":
            response = st.session_state.requests_session.get(
                request_url, 
                headers=request_headers, 
                verify=False
            )
        elif request_method == "POST":
            response = st.session_state.requests_session.post(
                request_url,
                headers=request_headers,
                data=request_body,
                verify=False,
            )
        else:
            st.error("Unknown method.")
            st.stop()

        if response.status_code:
            response_code = response.status_code
            response_headers = dict(response.headers)
            response_content = response.text

            st.session_state.response = {
                "url": request_url,
                "method": request_method,
                "code": response_code,
                "headers": response_headers,
                "content": response_content,
            }

            st.divider()
            col1, col2, col3 = st.columns([3,7,3])
            col1.subheader("Response")
            if str(response_code)[0] == "2":
                col3.button("Pin to sidebar", on_click=save_response_to_sidebar, icon=":material/arrow_back:")
            st.markdown(f"##### Status Code:")
            col1, col2 = st.columns([5,5])
            if str(response_code)[0] == "2":
                col1.success(response_code)
            else:
                col1.error(f"{response_code} {response.reason}")
            st.markdown("##### Headers:")
            st.write(response_headers)
            if response_content:
                st.markdown("##### Content")
                st.write(response_content)

    except Exception as ex:
        st.error(ex)
