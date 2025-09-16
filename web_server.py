"""
Simple web server for health checks and status monitoring in cloud deployment
"""
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
from datetime import datetime
import config_cloud as config

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def __init__(self, bot_instance, *args, **kwargs):
        self.bot_instance = bot_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/health':
            self.send_health_check()
        elif self.path == '/status':
            self.send_status()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def send_health_check(self):
        """Basic health check endpoint"""
        try:
            # Simple health check
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'InChrist AI Bot'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_status).encode())
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'unhealthy', 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def send_status(self):
        """Detailed status endpoint"""
        try:
            if self.bot_instance:
                status = self.bot_instance.get_status()
            else:
                status = {'status': 'Bot not initialized'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status, default=str).encode())
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'status': 'error', 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"HTTP: {format % args}")

class WebServer:
    def __init__(self, bot_instance=None, port=None):
        self.bot_instance = bot_instance
        self.port = port or config.PORT
        self.server = None
        self.server_thread = None
        
    def create_handler(self):
        """Create handler with bot instance"""
        def handler(*args, **kwargs):
            return HealthCheckHandler(self.bot_instance, *args, **kwargs)
        return handler
    
    def start(self):
        """Start the web server in a separate thread"""
        try:
            handler_class = self.create_handler()
            self.server = HTTPServer(('0.0.0.0', self.port), handler_class)
            
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"Health check server started on port {self.port}")
            logger.info(f"Health check: http://localhost:{self.port}/health")
            logger.info(f"Status check: http://localhost:{self.port}/status")
            
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    def stop(self):
        """Stop the web server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Web server stopped")

def start_health_server(bot_instance=None, port=None):
    """Convenience function to start health check server"""
    web_server = WebServer(bot_instance, port)
    web_server.start()
    return web_server
