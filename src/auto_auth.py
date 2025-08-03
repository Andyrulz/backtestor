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
        """Get login session with minimal user interaction.
        
        Returns:
            Tuple of (success, message/access_token)
        """
        try:
            # Check if we have a valid token
            if self.is_token_valid():
                return True, self.config.access_token
            
            # Start automated login process
            login_url = self.kite.login_url()
            
            st.info("🔐 Daily authentication required. Opening login page...")
            
            # Auto-open browser
            try:
                webbrowser.open(login_url)
            except Exception:
                pass
            
            # Display simplified login interface
            with st.container():
                st.markdown("### Quick Login")
                st.markdown("1. **Complete login in the opened browser**")
                st.markdown("2. **Copy the redirect URL and paste below**")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    redirect_url = st.text_input(
                        "🔗 Redirect URL",
                        placeholder="Paste the complete URL after login...",
                        help="Complete the login and paste the full redirect URL here"
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                    process_btn = st.button("🚀 Login", type="primary")
                
                if process_btn and redirect_url:
                    return self._process_redirect_url(redirect_url)
                
                # Show status message instead of auto-refresh
                if not redirect_url:
                    st.info("💡 Waiting for you to complete login and paste the redirect URL above...")
            
            return False, "Waiting for login completion"
            
        except Exception as e:
            logger.error(f"Login session error: {e}")
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
    """Render automated login interface.
    
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
    
    with st.expander("ℹ️ About Daily Authentication", expanded=False):
        st.markdown("""
        **Why daily login is required:**
        - Zerodha requires daily authentication for security
        - Access tokens expire every 24 hours
        - This prevents unauthorized automated trading
        
        **This process:**
        - Opens login automatically
        - Requires only URL copy-paste
        - Saves token for 23+ hours
        - Minimal daily interaction
        """)
    
    # Get login session
    success, result = auth.get_login_session()
    
    if success:
        st.success("✅ Authentication successful!")
        st.info("🔄 Reloading app with authenticated session...")
        # Use a small delay before rerun to prevent loops
        time.sleep(2)
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
