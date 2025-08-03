"""Local redirect server to automatically capture Kite login tokens."""

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
import webbrowser
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class RedirectHandler(BaseHTTPRequestHandler):
    """HTTP request handler for capturing redirect tokens."""
    
    # Class variable to store the callback
    token_callback = None
    
    def do_GET(self):
        """Handle GET request from Kite redirect."""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Log the incoming request for debugging
            logger.info(f"Received request: {self.path}")
            
            # Check if this is the store_tokens endpoint
            if parsed_url.path == '/store_tokens':
                request_token = query_params.get('request_token', [None])[0]
                status = query_params.get('status', [None])[0]
                
                logger.info(f"Processing store_tokens: token={request_token[:20] if request_token else None}..., status={status}")
                
                if request_token and status == 'success':
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    success_html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Authentication Successful</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f2f6; }}
                            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
                            .success {{ color: #00c851; font-size: 24px; margin-bottom: 20px; }}
                            .token {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all; margin: 20px 0; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="success">✅ Authentication Successful!</div>
                            <p>Your token has been captured and is being processed automatically.</p>
                            <div class="token">Request Token: {}</div>
                            <p>You can close this window and return to the trading app.</p>
                            <p><strong>The app will automatically continue...</strong></p>
                        </div>
                        <script>
                            // Auto-close after 3 seconds
                            setTimeout(() => window.close(), 3000);
                        </script>
                    </body>
                    </html>
                    """.format(request_token[:20] + "...")
                    
                    self.wfile.write(success_html.encode())
                    
                    # Call the token callback
                    if RedirectHandler.token_callback:
                        RedirectHandler.token_callback(request_token)
                    
                    logger.info(f"Token captured successfully: {request_token[:20]}...")
                    
                else:
                    # Send error response
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    error_html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Authentication Failed</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f2f6; }}
                            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
                            .error {{ color: #ff4444; font-size: 24px; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="error">❌ Authentication Failed</div>
                            <p>No valid request token received or authentication was denied.</p>
                            <p>Please return to the app and try again.</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(error_html.encode())
                    
            else:
                # Handle other paths
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>404 Not Found</h1></body></html>")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_page = f"<html><body><h1>500 Internal Server Error</h1><p>Error: {str(e)}</p></body></html>"
            self.wfile.write(error_page.encode())
    
    def log_message(self, format, *args):
        """Override to suppress default request logging but keep errors."""
        # Only log errors and important messages
        if "500" in str(args) or "Error" in format:
            logger.error(f"Server error: {format % args}")
        else:
            # Suppress normal request logging
            pass


class TokenCaptureServer:
    """Server to capture authentication tokens from Kite redirects."""
    
    def __init__(self, port: int = 3456):
        """Initialize the token capture server.
        
        Args:
            port: Port to run the server on
        """
        self.port = port
        self.server = None
        self.server_thread = None
        self.captured_token = None
        self.token_event = threading.Event()
        self.running = False
    
    def token_callback(self, token: str):
        """Callback function called when token is captured.
        
        Args:
            token: Captured request token
        """
        self.captured_token = token
        self.token_event.set()
        logger.info(f"Token captured and stored: {token[:20]}...")
    
    def start_server(self):
        """Start the redirect server."""
        try:
            # Set the callback in the handler class
            RedirectHandler.token_callback = self.token_callback
            
            self.server = HTTPServer(('localhost', self.port), RedirectHandler)
            self.running = True
            
            def run_server():
                logger.info(f"Starting redirect server on http://localhost:{self.port}")
                self.server.serve_forever()
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Give the server a moment to start
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start redirect server: {e}")
            return False
    
    def stop_server(self):
        """Stop the redirect server."""
        if self.server:
            self.server.shutdown()
            self.running = False
            logger.info("Redirect server stopped")
    
    def wait_for_token(self, timeout: int = 300) -> Optional[str]:
        """Wait for token to be captured.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Captured token or None if timeout
        """
        if self.token_event.wait(timeout):
            return self.captured_token
        return None
    
    def reset(self):
        """Reset the token capture state."""
        self.captured_token = None
        self.token_event.clear()


def test_server():
    """Test function for the redirect server."""
    server = TokenCaptureServer(port=3456)
    
    if server.start_server():
        print("Server started successfully!")
        print("Waiting for token...")
        
        # Open a test URL
        test_url = "http://localhost:3456/store_tokens?action=login&type=login&status=success&request_token=test_token_123"
        webbrowser.open(test_url)
        
        # Wait for token
        token = server.wait_for_token(timeout=30)
        
        if token:
            print(f"Token captured: {token}")
        else:
            print("No token captured")
        
        server.stop_server()
    else:
        print("Failed to start server")


if __name__ == "__main__":
    test_server()
