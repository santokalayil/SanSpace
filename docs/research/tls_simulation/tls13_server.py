"""
TLS 1.3 localhost server — for learning/simulation purposes only.

Prerequisites:
    Generate a self-signed cert first:
        openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
            -days 365 -nodes \
            -subj "/CN=localhost" \
            -addext "subjectAltName=IP:127.0.0.1,DNS:localhost"

    Run the server in one terminal, then run tls13_client.py in another.
"""

import ssl
import socket

HOST = "127.0.0.1"
PORT = 8443


def run_server() -> None:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_sock.bind((HOST, PORT))
        raw_sock.listen(1)
        print(f"[server] Listening on {HOST}:{PORT}  (TLS 1.3 only)")
        print("[server] Waiting for a client connection...")

        with ctx.wrap_socket(raw_sock, server_side=True) as tls_sock:
            conn, addr = tls_sock.accept()
            with conn:
                print()
                print(f"[server] Connected from : {addr}")
                print(f"[server] TLS version    : {conn.version()}")
                print(f"[server] Cipher suite   : {conn.cipher()[0]}")

                # Read the full HTTP request (ends with \r\n\r\n)
                raw = b""
                while b"\r\n\r\n" not in raw:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    raw += chunk

                request_line = raw.decode(errors="replace").splitlines()[0]
                print(f"[server] HTTP request   : {request_line}")

                # Parse method + path
                parts = request_line.split()
                method = parts[0] if parts else "?"
                path   = parts[1] if len(parts) > 1 else "/"

                # Build HTTP/1.1 response
                body = (
                    f"<html><body>"
                    f"<h1>TLS 1.3 HTTPS works!</h1>"
                    f"<p>Method: {method}</p>"
                    f"<p>Path: {path}</p>"
                    f"<p>Protocol: {conn.version()}</p>"
                    f"<p>Cipher: {conn.cipher()[0]}</p>"
                    f"</body></html>"
                )
                response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/html\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n"
                    f"\r\n"
                    f"{body}"
                )
                conn.sendall(response.encode())
                print(f"[server] HTTP response  : 200 OK  ({len(body)} bytes body sent)")


if __name__ == "__main__":
    run_server()
