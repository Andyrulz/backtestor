"""Simple test to check token capture flow."""

import streamlit as st
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from redirect_server import TokenCaptureServer

def test_token_flow():
    """Test the token capture and Streamlit flow."""
    st.title("🧪 Token Capture Flow Test")
    
    if 'server_started' not in st.session_state:
        st.session_state.server_started = False
    if 'token_captured' not in st.session_state:
        st.session_state.token_captured = None
    
    if not st.session_state.server_started:
        if st.button("🚀 Start Server and Capture Test"):
            server = TokenCaptureServer(port=3456)
            if server.start_server():
                st.session_state.server_started = True
                st.session_state.server = server
                st.success("✅ Server started!")
                st.rerun()
    else:
        st.info("🔄 Server is running, checking for tokens...")
        
        # Check for token
        server = st.session_state.server
        token = server.wait_for_token(timeout=0.1)
        
        if token and not st.session_state.token_captured:
            st.session_state.token_captured = token
            st.success(f"✅ Token captured: {token}")
            server.stop_server()
            st.balloons()
            st.info("🔄 Reloading to show main app...")
            time.sleep(2)
            st.rerun()
        elif st.session_state.token_captured:
            st.success(f"🎉 Token was captured: {st.session_state.token_captured}")
            st.info("This demonstrates the token capture working!")
        else:
            st.info("⏳ Waiting for token... Go to: http://localhost:3456/store_tokens?action=login&type=login&status=success&request_token=TEST123")
            time.sleep(2)
            st.rerun()

if __name__ == "__main__":
    test_token_flow()
