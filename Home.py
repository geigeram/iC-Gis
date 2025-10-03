import streamlit as st

st.title("GIS Overview")

# List of pages
pages = [
    {"file": "pages/1_🌍_Bohrloecher.py", "title": "Bohrloecher", "icon": "🌍"},
    {"file": "pages/2_🪟_Projectmap.py", "title": "Projectmap", "icon": "🪟"},
    {"file": "pages/3_😄_Projectdataframe.py", "title": "Projectdataframe", "icon": "😄"},
    {"file": "pages/4_Messtation.py", "title": "Messtation", "icon": "📊"},
    {"file": "pages/5_convert.py", "title": "Convert", "icon": "🔄"},
]

# Create columns for grid
cols = st.columns(3)

for i, page in enumerate(pages):
    with cols[i % 3]:
        # Create a card-like container
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; text-align: center; background-color: #f9f9f9; margin-bottom: 10px;">
            <div style="font-size: 50px; margin-bottom: 10px;">{page["icon"]}</div>
            <h3>{page["title"]}</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to " + page["title"], key=page["file"]):
            st.switch_page(page["file"])
