"""Small static preview server with byte ranges for video seeking."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path
import argparse,re,shutil

class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range=None
        path=Path(self.translate_path(self.path))
        value=self.headers.get('Range','')
        if value and path.is_file():
            size=path.stat().st_size
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
            if not match or not any(match.groups()):
                self.send_error(416);return None
            start,end=match.groups()
            start_n=int(start) if start else max(0,size-int(end))
            end_n=min(int(end),size-1) if start and end else size-1
            if start_n>end_n or start_n>=size:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
            stream=path.open('rb');stream.seek(start_n)
            self.byte_range=(start_n,end_n)
            self.send_response(206)
            self.send_header('Content-Type',self.guess_type(str(path)))
            self.send_header('Content-Length',str(end_n-start_n+1))
            self.send_header('Content-Range',f'bytes {start_n}-{end_n}/{size}')
            self.send_header('Accept-Ranges','bytes')
            self.end_headers();return stream
        return super().send_head()

    def copyfile(self,source,outputfile):
        if self.byte_range:
            remaining=self.byte_range[1]-self.byte_range[0]+1
            while remaining:
                chunk=source.read(min(remaining,1024*1024))
                if not chunk:break
                outputfile.write(chunk);remaining-=len(chunk)
        else:shutil.copyfileobj(source,outputfile)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',default=str(Path(__file__).resolve().parents[1]/'docs'))
    parser.add_argument('--bind',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    server=ThreadingHTTPServer((args.bind,args.port),partial(Handler,directory=str(Path(args.directory).resolve())))
    print(f'Serving DriveTTO on http://{args.bind}:{args.port}',flush=True)
    server.serve_forever()
