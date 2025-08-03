"""Authentication management for Kite API."""

import os
import streamlit as st
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect
from config import KiteConfig
from typing import Optional, Tuple


class KiteAuth:
    """Handles Kite API authentication flow."""
    
    def __init__(self, config: KiteConfig):
        """Initialize with configuration.
        
        Args:
            config: Kite configuration
        """
        self.config = config
        self.kite = KiteConnect(api_key=config.api_key)
    
    def is_authenticated(self) -> bool:
        """Check if current access token is valid.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.config.access_token:
            return False
        
        try:
            self.kite.set_access_token(self.config.access_token)
            self.kite.profile()
            return True
        except Exception:
            return False
    
    def get_login_url(self) -> str:
        """Get login URL for authentication.
        
        Returns:
            Login URL string
        """
        return self.kite.login_url()
    
    def generate_session(self, request_token: str) -> Tuple[bool, str]:
        """Generate session using request token.
        
        Args:
            request_token: Request token from redirect URL
            
        Returns:
            Tuple of (success, message/access_token)
        """
        try:
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.config.api_secret
            )
            
            access_token = data["access_token"]
            
            # Update .env file
            self._update_env_file(access_token)
            
            # Update config
            self.config.access_token = access_token
            
            return True, access_token
            
        except Exception as e:
            return False, str(e)
    
    def _update_env_file(self, access_token: str) -> None:
        """Update .env file with new access token.
        
        Args:
            access_token: New access token
        """
        env_path = Path(__file__).parent.parent / ".env"
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update existing token line or add new one
            token_updated = False
            for i, line in enumerate(lines):
                if line.startswith("KITE_ACCESS_TOKEN="):
                    lines[i] = f"KITE_ACCESS_TOKEN={access_token}\n"
                    token_updated = True
                    break
            
            if not token_updated:
                lines.append(f"\nKITE_ACCESS_TOKEN={access_token}\n")
            
            with open(env_path, 'w') as f:
                f.writelines(lines)


def render_login_form(config: KiteConfig) -> Optional[KiteConnect]:
    """Render login form and handle authentication.
    
    Args:
        config: Kite configuration
        
    Returns:
        KiteConnect instance if authenticated, None otherwise
    """
    auth = KiteAuth(config)
    
    # Check if already authenticated
    if auth.is_authenticated():
        kite = KiteConnect(api_key=config.api_key)
        kite.set_access_token(config.access_token)
        return kite
    
    # Show login form
    st.error("🔐 Authentication Required")
    st.info("Your access token has expired or is invalid. Please authenticate to continue.")
    
    with st.container():
        st.subheader("Login to Kite")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Step 1:** Click the login button below")
            login_url = auth.get_login_url()
            
            if st.button("🌐 Login to Kite", type="primary", use_container_width=True):
                st.markdown(f'<a href="{login_url}" target="_blank">Click here if the page doesn\'t open automatically</a>', unsafe_allow_html=True)
                st.components.v1.html(f'<script>window.open("{login_url}", "_blank");</script>')
            
            st.markdown("**Step 2:** After login, paste the redirect URL below")
            
            redirect_url = st.text_input(
                "Redirect URL",
                placeholder="https://yourapp.com/?request_token=...",
                help="Complete the login in the opened browser, then copy and paste the full redirect URL here"
            )
            
            if st.button("🔑 Generate Access Token", disabled=not redirect_url):
                with st.spinner("Generating access token..."):
                    # Extract request token
                    try:
                        parsed_url = urlparse(redirect_url)
                        query_params = parse_qs(parsed_url.query)
                        
                        if 'request_token' not in query_params:
                            st.error("❌ No request_token found in URL. Please check the URL.")
                        else:
                            request_token = query_params['request_token'][0]
                            
                            success, result = auth.generate_session(request_token)
                            
                            if success:
                                st.success("✅ Authentication successful!")
                                st.info("🔄 Refreshing app...")
                                st.rerun()
                            else:
                                st.error(f"❌ Authentication failed: {result}")
                                
                    except Exception as e:
                        st.error(f"❌ Error processing URL: {str(e)}")
        
        with col2:
            st.markdown("**Instructions:**")
            st.markdown("""
            1. Click 'Login to Kite'
            2. Complete login in browser
            3. Copy the redirect URL
            4. Paste it in the text box
            5. Click 'Generate Access Token'
            """)
            
            with st.expander("ℹ️ About Access Tokens"):
                st.markdown("""
                - Access tokens expire daily
                - You need to login once per day
                - Tokens are automatically saved
                - Keep your API secret secure
                """)
    
    return None
