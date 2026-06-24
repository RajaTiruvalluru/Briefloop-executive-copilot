import streamlit as st

from src.data_loader import load_all_data, get_meeting_bundle
from src.followup import build_followup_prompt
from src.llm_client import LLMConfig, call_chat_model, test_connection
from src.prompts import BRIEF_SYSTEM_PROMPT, FOLLOWUP_SYSTEM_PROMPT, build_brief_prompt
from src.retrieval import retrieve_relevant_docs


APP_NAME = "BriefLoop"
APP_SUBTITLE = "Executive Prep & Follow-Up Copilot"


st.set_page_config(
    page_title=f"{APP_NAME} — {APP_SUBTITLE}",
    layout="wide",
)

st.title(f"{APP_NAME}")
st.subheader(APP_SUBTITLE)
st.caption(
    "Privacy-safe proof of concept using fully synthetic executive-operations data. "
    "No real CEO, donor, grantee, inbox, calendar, or private relationship data is used."
)

data = load_all_data()


with st.sidebar:
    st.header("Local vLLM Settings")

    base_url = st.text_input(
        "Base URL",
        value="http://localhost:8000/v1",
        help="If vLLM runs in WSL and localhost fails, use your WSL IP, e.g. http://172.xx.xx.xx:8000/v1",
    )
    model_name = st.text_input(
        "Model name",
        value="Qwen/Qwen2.5-14B-Instruct",
        help="Use exactly the model name shown by your vLLM /v1/models endpoint.",
    )
    api_key = st.text_input(
        "API key",
        value="local-vllm-key",
        type="password",
        help="Use the same key you used when starting vLLM. If you did not set one, any placeholder often works.",
    )

    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    max_tokens = st.slider("Max tokens", 500, 3000, 1600, 100)

    llm_config = LLMConfig(
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if st.button("Test vLLM connection"):
        ok, message = test_connection(llm_config)
        if ok:
            st.success(message)
        else:
            st.error(message)


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Meeting Brief",
        "Follow-Up Extractor",
        "Inbox Requests",
        "Data Browser",
        "About",
    ]
)


with tab1:
    st.header("Generate a Meeting Prep Brief")

    meetings = data["meetings"]
    meeting_options = [
        f"{row.meeting_id} — {row.meeting_title}"
        for row in meetings.itertuples(index=False)
    ]

    selected_option = st.selectbox("Select a synthetic meeting", meeting_options)
    meeting_id = selected_option.split(" — ")[0]

    bundle = get_meeting_bundle(meeting_id, data)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### Meeting")
        st.dataframe(bundle["meeting"], use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("### Linked Contact")
        st.dataframe(bundle["contact"], use_container_width=True, hide_index=True)

    st.markdown("### Retrieved Context")
    context_cols = st.columns(3)
    with context_cols[0]:
        st.markdown("**Prior notes**")
        st.dataframe(bundle["prior_notes"], use_container_width=True, hide_index=True)
    with context_cols[1]:
        st.markdown("**Open follow-ups**")
        st.dataframe(bundle["followups"], use_container_width=True, hide_index=True)
    with context_cols[2]:
        st.markdown("**Related inbox requests**")
        st.dataframe(bundle["inbox"], use_container_width=True, hide_index=True)

    extra_context = st.text_area(
        "Optional instruction for this brief",
        placeholder="Example: Make this concise. Focus on open loops, agenda, and human review notes.",
        height=100,
    )

    if st.button("Generate Brief", type="primary"):
        relevant_docs = retrieve_relevant_docs(
            meeting=bundle["meeting"],
            contact=bundle["contact"],
            docs=data["source_docs"],
            top_k=4,
        )

        prompt = build_brief_prompt(
            bundle=bundle,
            strategic_priorities=data["strategic_priorities"],
            relevant_docs=relevant_docs,
            extra_context=extra_context,
        )

        with st.spinner("Generating with local Qwen through vLLM..."):
            try:
                brief = call_chat_model(
                    config=llm_config,
                    system_prompt=BRIEF_SYSTEM_PROMPT,
                    user_prompt=prompt,
                )
                st.session_state["brief_output"] = brief
            except Exception as exc:
                st.error(f"Model call failed: {exc}")

    if "brief_output" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["brief_output"])
        st.download_button(
            label="Download brief as Markdown",
            data=st.session_state["brief_output"],
            file_name=f"{meeting_id}_briefloop_meeting_brief.md",
            mime="text/markdown",
        )


with tab2:
    st.header("Extract Follow-Ups From Rough Notes")

    default_notes = (
        "We agreed that Lena will send the workflow tracker draft by Friday. "
        "The Chief of Staff will decide whether board packet dependencies should be tracked there. "
        "No one committed to emailing external contacts yet."
    )

    notes = st.text_area("Paste rough meeting notes", value=default_notes, height=180)

    if st.button("Extract Follow-Ups", type="primary"):
        prompt = build_followup_prompt(notes)
        with st.spinner("Extracting follow-ups with local Qwen through vLLM..."):
            try:
                followup_output = call_chat_model(
                    config=llm_config,
                    system_prompt=FOLLOWUP_SYSTEM_PROMPT,
                    user_prompt=prompt,
                )
                st.session_state["followup_output"] = followup_output
            except Exception as exc:
                st.error(f"Model call failed: {exc}")

    if "followup_output" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["followup_output"])
        st.download_button(
            label="Download follow-ups as Markdown",
            data=st.session_state["followup_output"],
            file_name="briefloop_extracted_followups.md",
            mime="text/markdown",
        )


with tab3:
    st.header("Synthetic Inbox Requests")
    st.caption("These are synthetic inbound requests. A later version can add model-based triage.")
    st.dataframe(data["inbox"], use_container_width=True, hide_index=True)


with tab4:
    st.header("Data Browser")

    dataset_name = st.selectbox(
        "Choose dataset",
        [
            "contacts",
            "meetings",
            "inbox",
            "prior_notes",
            "followups",
            "travel",
            "source_docs",
            "strategic_priorities",
        ],
    )

    if dataset_name == "source_docs":
        st.json(data["source_docs"])
    elif dataset_name == "strategic_priorities":
        st.json(data["strategic_priorities"])
    else:
        st.dataframe(data[dataset_name], use_container_width=True, hide_index=True)


with tab5:
    st.header("About BriefLoop")
    st.markdown(
        """
**BriefLoop** is a privacy-safe proof of concept for executive-operations workflows.

It demonstrates how a local LLM can help an operator:

1. Prepare concise meeting briefs.
2. Surface relationship context.
3. Identify open loops and unresolved commitments.
4. Draft agenda items and prep checklists.
5. Convert rough meeting notes into follow-up actions.

### Privacy boundary

This demo uses synthetic data only. It does not use real executive data, real donor data,
real grantee data, real inboxes, real calendars, or confidential relationship history.

### Design principle

AI prepares and organizes. The operator reviews, edits, and decides.
        """
    )
