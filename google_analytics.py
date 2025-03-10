import streamlit as st

def inject_ga():
    GA_ID = "G-ET1W3PTQGE"
    GA_SCRIPT = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', '{GA_ID}');
    </script>
    """
    st.markdown(GA_SCRIPT, unsafe_allow_html=True)