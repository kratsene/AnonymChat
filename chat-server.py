#!/usr/bin/env python3
"""
AnonymChat - Server
Zero-trace chat via Tor hidden service.
No accounts. No port forwarding. No third-party services.
"""

import socket
import threading
import string
import random
from datetime import datetime
from typing import Dict
import sys

try:
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


class ChatServer:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[socket.socket, str] = {}
        self.lock = threading.Lock()
        self.running = False
        self.room_code = self._generate_code()
        self.onion_address = None
        self._tor_controller = None

    def _generate_code(self):
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choice(chars) for _ in range(10))

    def _port_open(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(("127.0.0.1", port))
            s.close()
            return result == 0
        except:
            return False

    def _create_hidden_service(self):
        if not STEM_AVAILABLE:
            print("\n❌ stem is not installed.")
            print("   Run: python3 enviorment-check.py")
            return False

        if not self._port_open(9051):
            print("\n❌ Tor control port 9051 is not open.")
            print("   Start Tor Expert Bundle in a separate terminal with:")
            print("   .\\tor.exe --SocksPort 9050 --ControlPort 9051 --CookieAuthentication 1")
            return False

        try:
            print("⏳ Connecting to Tor and creating .onion address...", end=" ", flush=True)
            self._tor_controller = Controller.from_port(port=9051)
            self._tor_controller.authenticate()

            # create_ephemeral_hidden_service is the correct method for stem 1.5+
            response = self._tor_controller.create_ephemeral_hidden_service(
                {80: self.port},
                await_publication=True
            )
            self.onion_address = response.service_id
            print("done\n")
            return True

        except Exception as e:
            print(f"\n❌ Hidden service creation failed: {e}")
            print("   Make sure Tor is running with --ControlPort 9051 --CookieAuthentication 1")
            return False

    def start(self):
        print("\n" + "=" * 70)
        print("     AnonymChat — SERVER")
        print("     Zero-trace | Tor hidden service | No accounts")
        print("=" * 70)
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not STEM_AVAILABLE:
            print("\n❌ stem is not installed.")
            print("   Run: python3 enviorment-check.py")
            return

        try:
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(10)
        except OSError as e:
            if "Address already in use" in str(e) or "10048" in str(e):
                print(f"\n❌ Port {self.port} is already in use.")
                print("   Close the other server instance and try again.")
            else:
                print(f"\n❌ Could not bind: {e}")
            return

        if not self._create_hidden_service():
            self.server.close()
            return

        self.running = True

        print("=" * 70)
        print("🧅 TOR HIDDEN SERVICE ACTIVE")
        print("=" * 70)
        print(f"\n  .onion address : {self.onion_address}.onion")
        print(f"  Room Code      : {self.room_code}")
        print(f"\n  ✉️  Send ONLY these two things to your friend:")
        print(f"     1. {self.onion_address}.onion")
        print(f"     2. {self.room_code}")
        print(f"\n  Your real IP is never revealed.")
        print(f"  .onion stops working the moment you close this server.")
        print("=" * 70)
        print("\nWaiting for connections...\n")

        while self.running:
            try:
                client_socket, address = self.server.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                if self.running:
                    print(f"[ERROR] {e}")

        self.stop()

    def handle_client(self, client_socket: socket.socket, address: tuple):
        username = None
        try:
            client_socket.settimeout(120)  # .onion connections need more time

            # Send code prompt and wait — Tor circuit probes connect then send nothing,
            # so we catch TimeoutError here quietly instead of crashing the thread
            try:
                client_socket.send(b"CODE:")
                received_code = client_socket.recv(1024).decode("utf-8").strip()
            except (socket.timeout, TimeoutError, OSError):
                # Silent drop — Tor probe or slow connection that never sent data
                client_socket.close()
                return

            if received_code != self.room_code:
                client_socket.send(b"INVALID_CODE")
                client_socket.close()
                print(f"[-] Wrong room code attempt")
                return

            client_socket.send(b"CODE_OK")

            try:
                client_socket.send(b"USERNAME:")
                username = client_socket.recv(1024).decode("utf-8").strip()
            except (socket.timeout, TimeoutError, OSError):
                client_socket.close()
                return

            if not username or len(username) > 20 or " " in username:
                client_socket.send(b"INVALID_USERNAME")
                client_socket.close()
                return

            with self.lock:
                if username in self.clients.values():
                    client_socket.send(b"USERNAME_TAKEN")
                    client_socket.close()
                    return
                self.clients[client_socket] = username

            client_socket.send(b"USERNAME_OK")
            client_socket.settimeout(None)

            print(f"[+] {username} joined")
            self.broadcast(f"✅ {username} joined", exclude=client_socket, is_system=True)

            user_list = ", ".join(sorted(self.clients.values()))
            client_socket.send(f"USERS:{user_list}".encode("utf-8"))

            while self.running:
                try:
                    message = client_socket.recv(4096).decode("utf-8").strip()
                    if not message:
                        continue
                    if message.lower() in ["/quit", "/exit", "/leave"]:
                        break
                    if message.startswith("/"):
                        self.handle_command(client_socket, message)
                    else:
                        self.broadcast_message(username, message)
                except:
                    break

        finally:
            if client_socket in self.clients:
                with self.lock:
                    username = self.clients.pop(client_socket, username)
                if username:
                    print(f"[-] {username} left")
                    self.broadcast(f"👋 {username} left", is_system=True)
            try:
                client_socket.close()
            except:
                pass

    def handle_command(self, client_socket: socket.socket, command: str):
        cmd = command.lower().strip()
        if cmd == "/users":
            user_list = ", ".join(sorted(self.clients.values()))
            client_socket.send(f"SYSTEM:👥 Online: {user_list}".encode("utf-8"))
        elif cmd == "/help":
            client_socket.send(b"SYSTEM:Commands: /users  /count  /help  /quit")
        elif cmd == "/count":
            client_socket.send(
                f"SYSTEM:👥 {len(self.clients)} user(s) online".encode("utf-8")
            )

    def broadcast_message(self, username: str, message: str):
        timestamp = datetime.now().strftime("%H:%M")
        formatted = f"[{timestamp}] {username}: {message}"
        self.broadcast(formatted)
        print(f"[MSG] {formatted}")

    def broadcast(self, message: str, exclude=None, is_system: bool = False):
        with self.lock:
            for sock in list(self.clients.keys()):
                if sock == exclude:
                    continue
                try:
                    prefix = "SYSTEM:" if is_system else "MSG:"
                    sock.send(f"{prefix}{message}".encode("utf-8"))
                except:
                    pass

    def stop(self):
        self.running = False
        if self._tor_controller:
            try:
                if self.onion_address:
                    self._tor_controller.remove_ephemeral_hidden_service(
                        self.onion_address
                    )
                self._tor_controller.close()
            except:
                pass
        try:
            self.server.close()
        except:
            pass
        print("\n[SERVER] Stopped — .onion address is now dead\n")


if __name__ == "__main__":
    try:
        server = ChatServer()
        server.start()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"Error: {e}")
