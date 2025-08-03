"""Fixed authentication flow that works properly with Streamlit."""

import os
import time
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import streamlit as st
from kiteconnect import KiteConnect
from config import KiteConfig
from redirect_server import TokenCaptureServer
import logging

logger = logging.getLogger(__name__)


class StreamlitKiteAuth:
    """Streamlit-optimized Kite authentication."""
    
    def __init__(self, config: KiteConfig):
        self.config = config
        self.kite = KiteConnect(api_key=config.api_key)
        self.token_file = Path(__file__).parent.parent / ".kite_session"
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid."""
        if not self.config.access_token:
            return False
        
        try:
            self.kite.set_access_token(self.config.access_token)
            self.kite.profile()
            return True
        except Exception:
            return False
    
    def save_token(self, access_token: str) -> None:
        """Save token with timestamp."""
        try:
            with open(self.token_file, 'w') as f:
                f.write(f"{access_token}|{time.time()}")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
    
    def start_auth_flow(self):
        """Start the authentication flow."""
        # Initialize session state
        if 'auth_step' not in st.session_state:
            st.session_state.auth_step = 'start'
        if 'auth_server' not in st.session_state:
            st.session_state.auth_server = None
        if 'auth_start_time' not in st.session_state:
            st.session_state.auth_start_time = None
        
        # Handle different steps of authentication
        if st.session_state.auth_step == 'start':
            self._show_start_screen()
        elif st.session_state.auth_step == 'waiting':
            self._show_waiting_screen()
        elif st.session_state.auth_step == 'success':
            self._show_success_screen()
        elif st.session_state.auth_step == 'error':
            self._show_error_screen()
    
    def _show_start_screen(self):
        """Show the initial start screen."""
        st.markdown("### 🚀 Automatic Authentication")
        st.info("Ready to start automatic login process")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔐 Start Login", type="primary", use_container_width=True):
                # Start the server
                server = TokenCaptureServer(port=3456)
                if server.start_server():
                    st.session_state.auth_server = server
                    st.session_state.auth_step = 'waiting'
                    st.session_state.auth_start_time = time.time()
                    
                    # Open browser
                    login_url = self.kite.login_url()
                    webbrowser.open(login_url)
                    
                    st.rerun()
                else:
                    st.error("❌ Failed to start server")
    
    def _show_waiting_screen(self):
        """Show waiting screen and check for tokens."""
        st.markdown("### ⏳ Waiting for Login")
        st.success("✅ Server running on http://localhost:3456")
        st.info("🌐 Complete login in the opened browser window")
        
        # Progress bar
        elapsed = time.time() - st.session_state.auth_start_time
        timeout = 180  # 3 minutes
        progress = min(elapsed / timeout, 1.0)
        
        progress_bar = st.progress(progress)
        status_placeholder = st.empty()
        
        if elapsed > timeout:
            status_placeholder.error("❌ Timeout")
            st.session_state.auth_step = 'error'
            st.session_state.auth_server.stop_server()
            st.rerun()
            return
        
        # Check for token
        server = st.session_state.auth_server
        token = server.wait_for_token(timeout=0.1)
        
        if token:
            st.session_state.captured_token = token
            st.session_state.auth_step = 'success'
            server.stop_server()
            st.rerun()
            return
        
        # Update status and auto-refresh
        remaining = int(timeout - elapsed)
        status_placeholder.info(f"⏳ Waiting... ({remaining}s remaining)")
        
        # Manual backup option
        with st.expander("🔧 Manual Backup"):
            manual_url = st.text_input("Paste redirect URL if automatic capture fails:")
            if st.button("Process Manual URL") and manual_url:
                try:
                    parsed_url = urlparse(manual_url)
                    query_params = parse_qs(parsed_url.query)
                    token = query_params.get('request_token', [None])[0]
                    
                    if token:
                        st.session_state.captured_token = token
                        st.session_state.auth_step = 'success'
                        server.stop_server()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing URL: {e}")
        
        # Auto-refresh every 2 seconds
        time.sleep(2)
        st.rerun()
    
    def _show_success_screen(self):
        """Show success screen and process token."""
        st.markdown("### ✅ Authentication Successful")
        
        token = st.session_state.captured_token
        st.success(f"Token captured: {token[:20]}...")
        
        try:
            # Generate session
            st.info("🔑 Generating access token...")
            data = self.kite.generate_session(
                request_token=token,
                api_secret=self.config.api_secret
            )
            
            access_token = data["access_token"]
            user_id = data.get("user_id", "Unknown")
            
            # Update configuration and save
            self.config.access_token = access_token
            self._update_env_token(access_token)
            self.save_token(access_token)
            
            st.success(f"✅ Authenticated as: {user_id}")
            st.success("🎉 Authentication completed successfully!")
            
            # Clear auth state and signal completion
            self._clear_auth_state()
            st.session_state.authentication_complete = True
            
            st.info("🔄 Reloading application...")
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Token processing error: {e}")
            st.error(f"❌ Authentication failed: {str(e)}")
            st.session_state.auth_step = 'error'
            st.rerun()
    
    def _show_error_screen(self):
        """Show error screen with retry option."""
        st.markdown("### ❌ Authentication Failed")
        st.error("Something went wrong during authentication")
        
        if st.button("🔄 Try Again"):
            self._clear_auth_state()
            st.rerun()
    
    def _clear_auth_state(self):
        """Clear authentication session state."""
        for key in ['auth_step', 'auth_server', 'auth_start_time', 'captured_token']:
            if key in st.session_state:
                del st.session_state[key]
    
    def _update_env_token(self, access_token: str) -> None:
        """Update .env file with new access token."""
        env_path = Path(__file__).parent.parent / ".env"
        
        try:
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                token_updated = False
                
                for i, line in enumerate(lines):
                    if line.startswith("KITE_ACCESS_TOKEN="):
                        lines[i] = f"KITE_ACCESS_TOKEN={access_token}"
                        token_updated = True
                        break
                
                if not token_updated:
                    for i, line in enumerate(lines):
                        if line.startswith("KITE_API_SECRET="):
                            lines.insert(i + 1, f"KITE_ACCESS_TOKEN={access_token}")
                            break
                    else:
                        lines.append(f"KITE_ACCESS_TOKEN={access_token}")
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                logger.info(f"Access token saved to {env_path}")
                    
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")


def render_streamlit_auth(config: KiteConfig) -> tuple[bool, any]:
    """Render the Streamlit-optimized authentication interface."""
    auth = StreamlitKiteAuth(config)
    
    # Check if authentication was just completed
    if st.session_state.get('authentication_complete', False):
        del st.session_state.authentication_complete
        # Return success and let the main app reload
        return True, None
    
    # Check if already authenticated
    if auth.is_token_valid():
        try:
            kite = KiteConnect(api_key=config.api_key)
            kite.set_access_token(config.access_token)
            kite.profile()
            return True, kite
        except Exception:
            pass
    
    # Show authentication flow
    st.warning("🔐 Authentication Required")
    
    with st.expander("ℹ️ About Authentication", expanded=False):
        st.markdown("""
        **Automatic Process:**
        - 🌐 Opens login page automatically
        - 🎯 Captures redirect token automatically
        - 💾 Saves token for future use
        - 🔄 Manual backup option available
        
        **Security:** Tokens expire daily for security
        """)
    
    auth.start_auth_flow()
    return False, None


def get_streamlit_authenticated_client(config: KiteConfig) -> any:
    """Get authenticated client for Streamlit."""
    auth = StreamlitKiteAuth(config)
    
    if auth.is_token_valid():
        kite = KiteConnect(api_key=config.api_key)
        kite.set_access_token(config.access_token)
        return kite
    
    return None
