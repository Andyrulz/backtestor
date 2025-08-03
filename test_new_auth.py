"""Test the new Streamlit authentication flow."""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import KiteConfig
from streamlit_auth import render_streamlit_auth

def main():
    """Test the new authentication flow."""
    st.title("🧪 New Authentication Flow Test")
    
    try:
        config = KiteConfig.from_env()
        st.success("✅ Configuration loaded successfully")
        
        # Test the new auth flow
        authenticated, kite_client = render_streamlit_auth(config)
        
        if authenticated:
            st.success("🎉 Authentication successful!")
            st.balloons()
            if kite_client:
                st.info("✅ Kite client ready for trading")
            else:
                st.info("🔄 Reloading with authenticated session...")
        else:
            st.info("⏳ Authentication in progress...")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
