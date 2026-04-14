"""
TLS 1.3 localhost client — for learning/simulation purposes only.

Prerequisites:
    1. Generate cert.pem + key.pem (see tls13_server.py header).
    2. Start tls13_server.py in another terminal.
    3. Run this script.

Optionally set SSLKEYLOGFILE to inspect traffic in Wireshark:
    SSLKEYLOGFILE=./tls_keys.log python3 tls13_client.py
"""

import pprint
import socket
import ssl

HOST = "127.0.0.1"
PORT = 8443


def run_client() -> None:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3

    # Trust only our self-signed certificate (never do check_hostname=False in production)
    ctx.load_verify_locations("cert.pem")
    # ctx.check_hostname is True by default — keep it that way

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        # server_hostname must match the CN / SAN in the certificate
        with ctx.wrap_socket(raw_sock, server_hostname="localhost") as tls_sock:
            tls_sock.connect((HOST, PORT))

            print("[client] === Handshake complete ===")
            print(f"[client] TLS version  : {tls_sock.version()}")
            cipher = tls_sock.cipher()
            print(f"[client] Cipher suite : {cipher[0] if cipher else 'unknown'}")
            print()

            cert = tls_sock.getpeercert()
            print("[client] Server certificate details:")
            pprint.pprint(cert if cert is not None else "(no certificate returned)")
            print()

            # Send a proper HTTP/1.1 GET request
            http_request = (
                "GET /hello HTTP/1.1\r\n"
                "Host: localhost\r\n"
                "Accept: text/html\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            tls_sock.sendall(http_request.encode())
            print(f"[client] HTTP request sent:\n{http_request.strip()}")
            print()

            # Read the full HTTP response
            raw = b""
            while True:
                chunk = tls_sock.recv(4096)
                if not chunk:
                    break
                raw += chunk

            response_text = raw.decode(errors="replace")
            # Split status line + headers from body
            if "\r\n\r\n" in response_text:
                head, body = response_text.split("\r\n\r\n", 1)
            else:
                head, body = response_text, ""

            status_line = head.splitlines()[0]
            headers = head.splitlines()[1:]

            print(f"[client] Status          : {status_line}")
            print("[client] Response headers:")
            for h in headers:
                print(f"         {h}")
            print()
            print(f"[client] Response body   :\n{body}")


if __name__ == "__main__":
    run_client()
