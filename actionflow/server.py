import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from actionflow.core import Flow

logs = []


# Custom HTTP Request Handler
class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, content, content_type="application/json", status_code=200):
        """Helper function to send response"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(content.encode())

    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/process":
            # Get the content length and read the POST data
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)

            # Process the YAML content
            result = post_data.decode("utf-8")
            print(result)

            Flow.load_all_actions()
            flow = Flow.from_string(result)

            flow_thread = threading.Thread(target=flow.execute)
            flow_thread.daemon = True
            flow_thread.start()

            # Send response (with last 3 log entries)
            response = json.dumps(
                {
                    "message": result,
                }
            )
            self._send_response(response)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/logs":
            # Stream logs
            def stream_logs():
                while True:
                    if logs:
                        for log in logs:
                            yield f"{log}\n"
                    time.sleep(1)  # Add a delay to simulate real-time log streaming

            # Send logs as plain text
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            for log in stream_logs():
                self.wfile.write(log.encode())
        elif self.path == "/status":
            # Return the current status
            status = {"status": "running", "uptime": time.ctime()}
            self._send_response(json.dumps(status))
        else:
            self.send_response(404)
            self.end_headers()


# Start the server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
