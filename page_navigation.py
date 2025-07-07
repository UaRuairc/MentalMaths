import streamlit as st

def initialise_and_begin_navigation():
    setup_screen_page = st.Page("pages/1_setup_screen.py", title="setup")
    stat_screen_page = st.Page("pages/2_stats_screen.py", title="stats")
    # pages = get_available_pages()
    pages = [setup_screen_page, stat_screen_page]
    page = st.navigation(pages)
    page.run()