"""Serve the compiled Angular SPA locally, including route refreshes."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

root = Path(__file__).resolve().parents[1] / 'front/dandr-web/dist/dandr-web/browser'
os.chdir(root)
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        candidate=Path(self.translate_path(self.path))
        if not candidate.exists() and '.' not in self.path.rsplit('/',1)[-1]:
            self.path='/index.html'
        super().do_GET()
ThreadingHTTPServer(('127.0.0.1',4200),Handler).serve_forever()
