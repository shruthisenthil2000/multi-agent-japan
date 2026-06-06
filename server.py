import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = "."  # Changed from "public" to root directory to serve premium files

class SPAHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Translate the path to a local file
        path = self.translate_path(self.path)

        # If the requested file doesn't exist, route to index.html (premium app experience)
        if not os.path.exists(path) or (os.path.isdir(path) and not os.path.exists(os.path.join(path, "index.html"))):
            self.path = '/index.html'

        return super().do_GET()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SPAHTTPRequestHandler) as httpd:
        print(f"Serving premium UI at http://localhost:{PORT}")
        print(f"Access landing page at http://localhost:{PORT}/landing.html")
        print(f"Access app interface at http://localhost:{PORT}/index.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
