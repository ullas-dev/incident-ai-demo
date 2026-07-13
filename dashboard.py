import pandas as pd
import streamlit as st

from database import get_upcoming_briefs, get_open_actions

st.title("Meeting Assistant Dashboard")

briefs = get_upcoming_briefs(hours=24)
actions = get_open_actions()

st.subheader("Upcoming Briefs")
if briefs:
    st.dataframe(pd.DataFrame(briefs))
else:
    st.write("No upcoming briefs found.")

st.subheader("Open Action Items")
if actions:
    st.dataframe(pd.DataFrame(actions))
else:
    st.write("No open action items.")