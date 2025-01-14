import base64
from requests_ntlm import HttpNtlmAuth
import streamlit as st
import json


most_common_headers = [
    {"Accept": "application/json"},
    {"Authorization": ""},
    {"Content-Type": "application/json"},
    {"X-CSRF-Token": "fetch"},
]


def init_auth_form() -> None:
    st.session_state.auth_active = {
        "user": "",
        "password": "",
        "domain": "",
        "method": "",
    }


def change_request_header_value(name) -> None:
    new_value = st.session_state[f"request_header_value_{name}"]
    st.session_state.request_headers[name]["value"] = new_value


def keep_request_header(name) -> None:
    new_value = st.session_state[f"request_header_keep_{name}"]
    st.session_state.request_headers[name]["keep"] = new_value


def delete_header(name) -> None:
    del st.session_state.request_headers[name]


def add_header_to_request(header: str, value: str) -> None:
    if header not in st.session_state.request_headers or (header in st.session_state.request_headers and not st.session_state.request_headers[header]["keep"]):
        st.session_state.request_headers[header] = {"value": value, "keep": False}


def add_headers_from_dia() -> None:
    if st.session_state.dia_header_name:
        add_header_to_request(
            st.session_state.dia_header_name, st.session_state.dia_header_value
        )
    headers = [
        header
        for header in st.session_state
        if "dia_header_name_" in header and st.session_state[header]
    ]
    headers.sort()
    for header in headers:
        name = header.split("_")[-1]
        value = st.session_state[f"dia_header_value_{name}"]
        add_header_to_request(name, value)


@st.dialog("Add Headers")
def add_header_dia() -> None:
    st.markdown("**New Header**")
    col1, col2 = st.columns([1, 1])
    col1.text_input("Header", key=f"dia_header_name")
    col2.text_input("Value", key=f"dia_header_value")
    st.write("##")
    st.markdown("**Most Used**")
    for index, header in enumerate(most_common_headers):
        key = next(iter(header))
        col1, col2 = st.columns([1, 1], vertical_alignment="center")
        with col1:
            st.checkbox(key, key=f"dia_header_name_{key}")
        with col2:
            st.text_input("", header[key], key=f"dia_header_value_{key}", label_visibility="collapsed")
    st.markdown("##")
    if st.button(
        "Add", 
        type="primary", 
        on_click=add_headers_from_dia,
        icon=":material/add:"
    ):
        st.rerun()


def use_auth(session, headers) -> None:
    user = st.session_state.auth_active["user"]
    password = st.session_state.auth_active["password"]
    domain = st.session_state.auth_active["domain"]
    method = st.session_state.auth_active["method"]

    if not user:
        return None

    if method == "Base64":
        cred_string = f"{user}:{password}"
        cred_string_bytes = cred_string.encode("ascii")
        base64_bytes = base64.b64encode(cred_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        headers["Authorization"] = f"Basic {base64_string}"

    elif method == "NTLM":
        session.auth = HttpNtlmAuth(
            f"{domain}\\{user}", password
        )

    else:
        raise ValueError(f"Authentication method {method} not supported.")


def save_response_to_sidebar() -> None:
    if "sidebar_responses" not in st.session_state:
        st.session_state.sidebar_responses = []
    st.session_state.sidebar_responses.append(st.session_state.response)


def clear_header_form() -> None:
    st.session_state.header_form_name = ""
    st.session_state.header_form_value = ""


@st.dialog("Response Data")
def show_sidebar_response(response) -> None:
    st.write(response)


def delete_sidebar_response(index) -> None:
    del st.session_state.sidebar_responses[index]


def change_auth_form() -> None:
    init_auth_form()


st.fragment
def init_sidebar_auth() -> None:
    st.markdown("#####")
    st.subheader('Authentication')
    # with st.form("credentials"):
    auth_method = st.selectbox(
        "Method", ["Base64", "NTLM"], on_change=change_auth_form, key="auth_method"
    )
    st.text_input("User name", key="auth_user")
    st.text_input("User password", type="password", key="auth_password")
    if auth_method == "NTLM":
        st.selectbox("Domain", ["hr-appltest.de", "hr-applprep.de", "hannover-re.grp"], key="auth_domain")
    if st.button("Use creadentials", type='primary', icon=":material/login:"):
        st.session_state.auth_active = {
            "user": st.session_state.auth_user,
            "password": st.session_state.auth_password,
            "domain": st.session_state.auth_domain if auth_method == "NTLM" else "",
            "method": st.session_state.auth_method,
        }
        auth_error = False
        if len(st.session_state.auth_user) == 0:
            st.error('User fieled is required.')
            auth_error = True
        if len(st.session_state.auth_password) == 0:
            st.error("Password fieled is required.")
            auth_error = True
        if auth_method == "NTLM" and len(st.session_state.auth_domain) == 0:
            st.error("Domain fieled is required.")
            auth_error = True
        if auth_error:
            st.stop()

    if "auth_active" in st.session_state and len(
        st.session_state.auth_active["user"]
    ) > 0:
        st.success(
            f"Credentials for user {st.session_state.auth_active["user"].upper()} activated."
        )  


def init_sidebar_responses() -> None:
    if "sidebar_responses" in st.session_state and st.session_state.sidebar_responses:
        st.subheader("Responses Cache")
        for index, response in enumerate(st.session_state.sidebar_responses):
            col1, col2 = st.columns([5,1])
            col1.text(f"""
                      [{response["method"]}] 
                      {response["url"]}""")
            col2.button("", key=f"sidebar_response_show_{index}", on_click=show_sidebar_response, args=[response], icon=":material/preview:")
            col2.button("", key=f"sidebar_response_delete_{index}", on_click=delete_sidebar_response, args=[index], icon=":material/clear:")


def set_request_data(file) -> None:
    upload_data = file.getvalue().decode("utf-8")
    upload_object = json.loads(upload_data)
    st.session_state.request_method = upload_object["request_method"]
    st.session_state.request_url = upload_object["request_url"]
    delete_headers = [
        header_old
        for header_old in st.session_state.request_headers
        if not st.session_state.request_headers[header_old]["keep"]
    ]
    for header_delete in delete_headers:
        del st.session_state.request_headers[header_delete]
    for header in upload_object["request_headers"]:
        value = upload_object["request_headers"][header]
        add_header_to_request(header, value)
    st.session_state.request_body = upload_object["request_body"]


def init_request_method_url() -> None:
    col1, col2 = st.columns([1, 4])
    with col1:
        st.selectbox("Method", ["GET", "POST"], key="request_method")
    with col2:
        st.text_input(
            "URL",
            key="request_url",
    )


st.fragment
def init_request_headers() -> None:
    headers = [key for key in st.session_state.request_headers]
    st.button("Add Header", icon=":material/add:", on_click=add_header_dia)
    for header in headers:
        value = st.session_state.request_headers[header]["value"]
        col1, col2, col3, col4 = st.columns(
            [0.3, 0.4, 0.1, 0.1], vertical_alignment="center"
        )
        with col1:
            st.markdown(f"{header}")
        with col2:
            st.text_input(
                "",
                value=value,
                key=f"request_header_value_{header}",
                on_change=change_request_header_value,
                args=[header],
                label_visibility="collapsed"
            )
        with col3:
            st.checkbox(
                "Keep",
                key=f"request_header_keep_{header}",
                on_change=keep_request_header,
                args=[header],
            )
        with col4:
            st.button(
                "",
                key=f"header_del_{header}",
                on_click=delete_header,
                args=[header],
                icon=":material/clear:",
            )


def init_request_body() -> None:
    st.text_area(
        "JSON body",
        key="request_body",
        disabled=True if st.session_state["request_method"] == "GET" else False,
    )
