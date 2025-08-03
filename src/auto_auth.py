"""Automated authentication handler for Kite API."""

import os
import time
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import streamlit as st
from kiteconnect import KiteConnect
from config import KiteConfig
from redirect_server import TokenCaptureServer
import logging

logger = logging.getLogger(__name__)


class AutoKiteAuth:
    """Automated Kite authentication with minimal user interaction."""
    
    def __init__(self, config: KiteConfig):
        """Initialize with configuration.
        
        Args:
            config: Kite configuration
        """
        self.config = config
        self.kite = KiteConnect(api_key=config.api_key)
        self.token_file = Path(__file__).parent.parent / ".kite_session"
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid and not expired.
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.config.access_token:
            return False
        
        # Check if token file exists and is recent
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token_data = f.read().strip().split('|')
                    if len(token_data) >= 2:
                        saved_token = token_data[0]
                        timestamp = float(token_data[1])
                        
                        # Check if token is less than 23 hours old
                        if (time.time() - timestamp) < (23 * 3600):
                            if saved_token == self.config.access_token:
                                # Test the token
                                try:
                                    self.kite.set_access_token(self.config.access_token)
                                    self.kite.profile()
                                    return True
                                except Exception:
                                    pass
            except Exception:
                pass
        
        return False
    
    def save_token(self, access_token: str) -> None:
        """Save token with timestamp.
        
        Args:
            access_token: Access token to save
        """
        try:
            with open(self.token_file, 'w') as f:
                f.write(f"{access_token}|{time.time()}")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
    
    def get_login_session(self) -> tuple[bool, str]:
        """Get login session with automatic token capture.
        
        Returns:
            Tuple of (success, message/access_token)
        """
        try:
            # Check if we have a valid token
            if self.is_token_valid():
                return True, self.config.access_token
            
            # Start redirect server for automatic token capture
            st.info("🔐 Starting automatic authentication...")
            
            redirect_server = TokenCaptureServer(port=3456)
            
            if not redirect_server.start_server():
                st.error("❌ Failed to start redirect server on port 3456")
                return self._fallback_manual_login()
            
            # Get login URL
            login_url = self.kite.login_url()
            
            # Display status
            with st.container():
                st.markdown("### � Automatic Authentication")
                st.success("✅ Redirect server started on http://localhost:3456")
                st.info("🌐 Opening login page automatically...")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**What's happening:**")
                    st.markdown("1. 🌐 Opening Kite login in your browser")
                    st.markdown("2. 🔄 Waiting for you to complete login")
                    st.markdown("3. 🎯 Automatically capturing redirect token")
                    st.markdown("4. 🔑 Generating access token")
                    
                    # Auto-open browser
                    try:
                        webbrowser.open(login_url)
                        st.success("✅ Login page opened in browser")
                    except Exception as e:
                        st.warning("⚠️ Could not auto-open browser")
                        st.markdown(f'**Please manually open:** [Kite Login]({login_url})')
                
                with col2:
                    st.markdown("**Status:**")
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    
                    # Show manual backup option
                    with st.expander("🔧 Manual Backup Option"):
                        st.markdown("If automatic capture fails, you can paste the redirect URL manually:")
                        manual_url = st.text_input("Redirect URL", placeholder="Paste URL if needed...")
                        if st.button("🔑 Process Manual URL") and manual_url:
                            redirect_server.stop_server()
                            return self._process_redirect_url(manual_url)
                
                # Wait for token with progress indication
                timeout = 180  # 3 minutes
                start_time = time.time()
                
                # Use session state to track the waiting process
                if 'waiting_start_time' not in st.session_state:
                    st.session_state.waiting_start_time = start_time
                
                # Check if we should continue waiting or if this is a fresh start
                if 'token_capture_complete' not in st.session_state:
                    st.session_state.token_capture_complete = False
                
                # Quick check for immediate token capture
                token = redirect_server.wait_for_token(timeout=0.1)  # Very quick check
                
                if token:
                    status_placeholder.success("✅ Token captured successfully!")
                    progress_bar.progress(1.0)
                    
                    # Mark completion in session state
                    st.session_state.token_capture_complete = True
                    st.session_state.captured_token = token
                    
                    # Process the token
                    redirect_server.stop_server()
                    return self._process_token_directly(token)
                
                # If no immediate token, show waiting state and use rerun approach
                elapsed = time.time() - st.session_state.waiting_start_time
                remaining = timeout - elapsed
                
                if remaining <= 0:
                    status_placeholder.error("❌ Timeout waiting for login")
                    redirect_server.stop_server()
                    st.warning("⚠️ Automatic capture timed out. Falling back to manual method...")
                    return self._fallback_manual_login()
                
                progress = elapsed / timeout
                progress_bar.progress(min(progress, 1.0))
                
                status_placeholder.info(f"⏳ Waiting for login completion... ({int(remaining)}s remaining)")
                
                # Auto-refresh every 2 seconds to check for token
                time.sleep(2)
                st.rerun()
            
        except Exception as e:
            logger.error(f"Login session error: {e}")
            return False, str(e)
    
    def _fallback_manual_login(self) -> tuple[bool, str]:
        """Fallback to manual URL pasting method.
        
        Returns:
            Tuple of (success, message)
        """
        st.markdown("### 📋 Manual Login Method")
        st.info("Complete the login process and paste the redirect URL below:")
        
        login_url = self.kite.login_url()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            redirect_url = st.text_input(
                "🔗 Redirect URL",
                placeholder="Paste the complete URL after login...",
                help="Complete the login and paste the full redirect URL here"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.button("🌐 Open Login", type="secondary"):
                webbrowser.open(login_url)
                st.success("Login page opened!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            process_btn = st.button("🚀 Process URL", type="primary")
        
        if process_btn and redirect_url:
            return self._process_redirect_url(redirect_url)
        
        # Show helpful information
        with st.expander("ℹ️ Instructions"):
            st.markdown(f"""
            1. Click 'Open Login' or manually go to: {login_url}
            2. Complete the Kite login process
            3. After login, you'll be redirected to a URL starting with `http://localhost:3456/store_tokens`
            4. Copy the entire URL and paste it in the text box above
            5. Click 'Process URL'
            """)
        
        return False, "Waiting for manual URL input"
    
    def _process_token_directly(self, request_token: str) -> tuple[bool, str]:
        """Process request token directly.
        
        Args:
            request_token: Request token from redirect
            
        Returns:
            Tuple of (success, message/access_token)
        """
        try:
            st.info("� Generating access token...")
            
            # Generate session
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.config.api_secret
            )
            
            access_token = data["access_token"]
            user_id = data.get("user_id", "Unknown")
            
            st.success(f"✅ Access token generated for user: {user_id}")
            
            # Update environment and save token
            st.info("💾 Saving token...")
            self._update_env_token(access_token)
            self.save_token(access_token)
            
            # Update config
            self.config.access_token = access_token
            
            st.success("🎉 Authentication completed successfully!")
            return True, access_token
            
        except Exception as e:
            logger.error(f"Token processing error: {e}")
            st.error(f"❌ Authentication failed: {str(e)}")
            return False, str(e)
    
    def _process_redirect_url(self, redirect_url: str) -> tuple[bool, str]:
        """Process redirect URL to extract token.
        
        Args:
            redirect_url: Redirect URL from browser
            
        Returns:
            Tuple of (success, message/access_token)
        """
        try:
            st.info("🔄 Processing login URL...")
            
            # Extract request token
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'request_token' not in query_params:
                st.error("❌ No request_token found in URL")
                return False, "No request_token found in URL"
            
            request_token = query_params['request_token'][0]
            st.info(f"✅ Request token extracted: {request_token[:20]}...")
            
            # Generate session
            st.info("🔑 Generating access token...")
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.config.api_secret
            )
            
            access_token = data["access_token"]
            user_id = data.get("user_id", "Unknown")
            
            st.success(f"✅ Access token generated for user: {user_id}")
            
            # Update environment and save token
            st.info("💾 Saving token...")
            self._update_env_token(access_token)
            self.save_token(access_token)
            
            # Update config
            self.config.access_token = access_token
            
            st.success("🎉 Authentication completed successfully!")
            return True, access_token
            
        except Exception as e:
            logger.error(f"Token processing error: {e}")
            st.error(f"❌ Authentication failed: {str(e)}")
            return False, str(e)
    
    def _update_env_token(self, access_token: str) -> None:
        """Update .env file with new access token.
        
        Args:
            access_token: New access token
        """
        env_path = Path(__file__).parent.parent / ".env"
        
        try:
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace or add access token
                lines = content.split('\n')
                token_updated = False
                
                for i, line in enumerate(lines):
                    if line.startswith("KITE_ACCESS_TOKEN="):
                        lines[i] = f"KITE_ACCESS_TOKEN={access_token}"
                        token_updated = True
                        break
                
                if not token_updated:
                    # Find where to insert the token (after API_SECRET)
                    for i, line in enumerate(lines):
                        if line.startswith("KITE_API_SECRET="):
                            lines.insert(i + 1, f"KITE_ACCESS_TOKEN={access_token}")
                            break
                    else:
                        # If not found, append
                        lines.append(f"KITE_ACCESS_TOKEN={access_token}")
                
                # Write back to file
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                logger.info(f"Access token saved to {env_path}")
                    
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")
            print(f"❌ Failed to save token to .env file: {e}")


def render_auto_login(config: KiteConfig) -> tuple[bool, any]:
    """Render automated login interface with automatic redirect capture.
    
    Args:
        config: Kite configuration
        
    Returns:
        Tuple of (authenticated, kite_client)
    """
    auth = AutoKiteAuth(config)
    
    # Check if already authenticated
    if auth.is_token_valid():
        try:
            kite = KiteConnect(api_key=config.api_key)
            kite.set_access_token(config.access_token)
            # Test connection
            kite.profile()
            return True, kite
        except Exception:
            pass
    
    # Show auto-login interface
    st.warning("🔐 Authentication Required")
    
    with st.expander("ℹ️ About Automatic Authentication", expanded=False):
        st.markdown("""
        **New Automatic Process:**
        - ✅ Automatic redirect capture (no copy-pasting needed!)
        - 🌐 Auto-opens login page
        - 🎯 Captures token automatically from redirect
        - 💾 Saves token for 23+ hours
        - 🔄 Manual backup option available
        
        **Why daily login is required:**
        - Zerodha requires daily authentication for security
        - Access tokens expire every 24 hours
        - This prevents unauthorized automated trading
        """)
    
    # Initialize session state for authentication process
    if 'auth_in_progress' not in st.session_state:
        st.session_state.auth_in_progress = False
    if 'auth_started' not in st.session_state:
        st.session_state.auth_started = False
    if 'token_capture_complete' not in st.session_state:
        st.session_state.token_capture_complete = False
    
    # Check if token capture was completed
    if st.session_state.token_capture_complete:
        st.success("✅ Authentication completed successfully!")
        st.info("🔄 Reloading application...")
        
        # Reset all auth session state
        st.session_state.auth_started = False
        st.session_state.auth_in_progress = False
        st.session_state.token_capture_complete = False
        if 'waiting_start_time' in st.session_state:
            del st.session_state.waiting_start_time
        if 'captured_token' in st.session_state:
            del st.session_state.captured_token
        
        # Force app rerun to refresh authentication status
        time.sleep(1)
        st.rerun()
    
    # If authentication hasn't started, show start button
    if not st.session_state.auth_started:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Automatic Login", type="primary", use_container_width=True):
                st.session_state.auth_started = True
                st.session_state.auth_in_progress = True
                # Clear any previous state
                if 'waiting_start_time' in st.session_state:
                    del st.session_state.waiting_start_time
                st.session_state.token_capture_complete = False
                st.rerun()
        return False, None
    
    # If authentication is in progress or started
    if st.session_state.auth_started:
        success, result = auth.get_login_session()
        
        if success:
            st.success("✅ Authentication successful!")
            st.info("🔄 Reloading app with authenticated session...")
            
            # Reset session state
            st.session_state.auth_started = False
            st.session_state.auth_in_progress = False
            
            # Small delay before rerun to prevent loops
            time.sleep(1)
            st.rerun()
        else:
            # Authentication failed or still in progress
            if "Waiting" in result:
                # Still waiting for completion
                pass
            else:
                # Failed - allow retry
                st.error(f"Authentication failed: {result}")
                if st.button("🔄 Retry Authentication"):
                    st.session_state.auth_started = False
                    st.session_state.auth_in_progress = False
                    st.rerun()
    
    return False, None


def get_auto_authenticated_client(config: KiteConfig) -> any:
    """Get automatically authenticated Kite client.
    
    Args:
        config: Kite configuration
        
    Returns:
        KiteConnect client or None
    """
    auth = AutoKiteAuth(config)
    
    if auth.is_token_valid():
        kite = KiteConnect(api_key=config.api_key)
        kite.set_access_token(config.access_token)
        return kite
    
    return None
