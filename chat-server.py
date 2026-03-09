#!/usr/bin/env python3
"""
Terminal Chat System - Secure Server with Room Authentication
Generates unique 10-digit alphanumeric codes for chat room access

Features:
- Unique 10-digit room authentication codes
- Secure client verification
- Support for Tor hidden service (.onion address)
- Server IP never exposed when using Tor
- Perfect for censorship resistance
"""

import socket
import threading
import time
import string
import random
from datetime import datetime
from typing import Dict, Set
import sys

# Try to import Tor control library
try:
    from stem.control import Controller
    from stem.util import term
    TOR_AVAILABLE = True
except ImportError:
    TOR_AVAILABLE = False


class RoomCodeGenerator:
    """Generates and manages unique room authentication codes"""
    
    @staticmethod
    def generate_code(length=10):
        """
        Generate a unique 10-digit alphanumeric code
        
        Args:
            length (int): Length of code (default: 10)
        
        Returns:
            str: Random alphanumeric code (e.g., "A7B2K9F4M1")
        """
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(length))
        return code


class TorHiddenService:
    """Manages Tor hidden service setup"""
    
    def __init__(self, local_host="127.0.0.1", local_port=5000, control_port=9051):
        self.local_host = local_host
        self.local_port = local_port
        self.control_port = control_port
        self.onion_address = None
        self.controller = None
        
    def setup(self):
        """Setup Tor hidden service"""
        if not TOR_AVAILABLE:
            print("⚠️  stem not installed. Install with: pip3 install stem --break-system-packages")
            return False
        
        try:
            print("[TOR] Connecting to Tor control port...")
            self.controller = Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            
            print("[TOR] Setting up hidden service...")
            response = self.controller.add_ephemeral_hidden_service(
                ports={80: (self.local_host, self.local_port)},
                await_publication=True
            )
            
            self.onion_address = response.service_id
            print(f"\n{'='*70}")
            print(f"✅ Tor Hidden Service Created!")
            print(f"{'='*70}")
            print(f"🧅 Onion Address: {self.onion_address}.onion")
            print(f"📍 Local Port: {self.local_port}")
            print(f"🔐 Clients connect via Tor only")
            print(f"{'='*70}\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up hidden service: {e}")
            print(f"💡 Troubleshooting:")
            print(f"   1. Make sure Tor is running: tor --ControlPort 9051 --CookieAuthentication 1")
            print(f"   2. Check control port {self.control_port} is accessible")
            print(f"   3. Install stem: pip3 install stem --break-system-packages")
            return False
    
    def cleanup(self):
        """Cleanup Tor connection"""
        if self.controller:
            try:
                self.controller.close()
            except:
                pass


class ChatServer:
    """Main chat server with room authentication"""
    
    def __init__(self, host="127.0.0.1", port=5000, use_tor_hidden=False):
        self.host = host
        self.port = port
        self.server = None
        self.clients: Dict[socket.socket, str] = {}
        self.lock = threading.Lock()
        self.running = False
        
        # Room authentication
        self.room_code = RoomCodeGenerator.generate_code(10)
        
        self.tor_service = None
        if use_tor_hidden:
            self.tor_service = TorHiddenService(local_host=host, local_port=port)
    
    def start(self):
        """Start the chat server"""
        try:
            # Create server socket
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Setup Tor if requested
            if self.tor_service:
                if not self.tor_service.setup():
                    print("⚠️  Continuing without Tor hidden service...")
                    self.tor_service = None
            
            # Bind and listen
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.running = True
            
            self.print_header()
            self.print_status(f"🚀 Server started on {self.host}:{self.port}")
            self.print_status(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.print_status("")
            self.print_room_info()
            self.print_status("=" * 70)
            self.print_status("Waiting for connections...\n")
            
            while self.running:
                try:
                    client_socket, address = self.server.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    if self.running:
                        self.print_error(f"Error accepting connection: {e}")
                    
        except OSError as e:
            self.print_error(f"Failed to start server: {e}")
            if "Address already in use" in str(e):
                self.print_error(f"Port {self.port} is already in use. Try a different port with --port option")
        except Exception as e:
            self.print_error(f"Fatal error: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual client connections with authentication"""
        username = None
        try:
            # Step 1: Request room code
            client_socket.send(b"CODE:")
            received_code = client_socket.recv(1024).decode('utf-8').strip()
            
            if received_code != self.room_code:
                self.print_error(f"❌ Invalid room code from {address[0]}:{address[1]} (provided: {received_code})")
                client_socket.send(b"INVALID_CODE")
                client_socket.close()
                return
            
            # Code is valid, send confirmation
            client_socket.send(b"CODE_OK")
            
            # Step 2: Request username
            client_socket.send(b"USERNAME:")
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            if not username or len(username) == 0:
                client_socket.send(b"INVALID_USERNAME")
                client_socket.close()
                return
            
            if len(username) > 20:
                client_socket.send(b"USERNAME_LONG")
                client_socket.close()
                return
            
            with self.lock:
                # Check if username already exists
                if username in self.clients.values():
                    client_socket.send(b"USERNAME_TAKEN")
                    client_socket.close()
                    return
                
                self.clients[client_socket] = username
            
            # Send confirmation
            client_socket.send(b"USERNAME_OK")
            
            # Announce user join
            join_msg = f"✅ {username} joined the chat"
            connection_type = f"(IP: {address[0]}:{address[1]})"
            if self.tor_service and self.tor_service.onion_address:
                connection_type = "(via Tor 🧅)"
            
            self.print_status(f"✅ {username} connected {connection_type}")
            self.broadcast(join_msg, exclude=client_socket, is_system=True)
            
            # Send user list
            user_list = ", ".join(sorted(self.clients.values()))
            client_socket.send(f"USERS:{user_list}".encode('utf-8'))
            
            # Main message loop
            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8').strip()
                    
                    if not message:
                        continue
                    
                    if message.lower() in ['/quit', '/exit', '/leave']:
                        break
                    
                    if message.startswith('/'):
                        self.handle_command(client_socket, message, username)
                    else:
                        self.broadcast_message(username, message)
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
        
        except Exception as e:
            if self.running and str(e) != "":
                self.print_error(f"Error handling client {address[0]}: {e}")
        finally:
            if client_socket in self.clients:
                with self.lock:
                    username = self.clients.pop(client_socket, username)
                if username:
                    leave_msg = f"👋 {username} left the chat"
                    self.print_status(f"❌ {username} disconnected")
                    self.broadcast(leave_msg, is_system=True)
            
            try:
                client_socket.close()
            except:
                pass
    
    def handle_command(self, client_socket: socket.socket, command: str, username: str):
        """Handle special commands"""
        cmd = command.lower().strip()
        
        if cmd == '/users':
            user_list = ", ".join(sorted(self.clients.values()))
            response = f"👥 Users online ({len(self.clients)}): {user_list}"
            client_socket.send(response.encode('utf-8'))
        elif cmd == '/help':
            help_text = (
                "📋 Available Commands:\n"
                "  /users   - List all online users\n"
                "  /help    - Show this help message\n"
                "  /quit    - Disconnect from chat"
            )
            client_socket.send(help_text.encode('utf-8'))
        elif cmd == '/count':
            count = len(self.clients)
            client_socket.send(f"👥 Total users connected: {count}".encode('utf-8'))
        else:
            client_socket.send(f"❌ Unknown command: {cmd}. Type /help for available commands.".encode('utf-8'))
    
    def broadcast_message(self, username: str, message: str):
        """Broadcast a message from a user"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {username}: {message}"
        self.broadcast(formatted_msg)
        self.print_status(f"💬 {formatted_msg}")
    
    def broadcast(self, message: str, exclude: socket.socket = None, is_system: bool = False):
        """Send message to all connected clients"""
        with self.lock:
            for client_socket in list(self.clients.keys()):
                if client_socket == exclude:
                    continue
                try:
                    if is_system:
                        prefix = "SYSTEM:"
                    else:
                        prefix = "MSG:"
                    client_socket.send(f"{prefix}{message}".encode('utf-8'))
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception:
                    pass
    
    def print_header(self):
        """Print server header"""
        print("\n" + "="*70)
        print("     TERMINAL CHAT SYSTEM - SERVER")
        if self.tor_service:
            print("     🧅 TOR HIDDEN SERVICE MODE 🧅")
        print("="*70)
    
    def print_room_info(self):
        """Print room authentication code"""
        print(f"\n🔐 ROOM AUTHENTICATION CODE: {self.room_code}")
        print(f"   Share this code with clients to join the chat room")
        print(f"   (Keep this code secret!)\n")
    
    def print_status(self, message: str):
        """Print server status"""
        if message.strip():
            print(f"[SERVER] {message}")
        else:
            print()
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def stop(self):
        """Stop the server"""
        self.running = False
        self.print_status("Shutting down server...")
        
        if self.tor_service:
            self.tor_service.cleanup()
        
        try:
            if self.server:
                self.server.close()
        except:
            pass
        
        self.print_status("Server stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Terminal Chat System - Secure Server with Room Authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE EXAMPLES:

  Basic server (recommended first time):
    python3 server.py

  With Tor hidden service (requires Tor + stem):
    python3 server.py --hidden-service

  Custom port:
    python3 server.py --port 8000

  Custom host and port:
    python3 server.py --host 0.0.0.0 --port 8000

SETUP FOR TOR HIDDEN SERVICE:

  1. Install stem:
     pip3 install stem --break-system-packages

  2. Start Tor with ControlPort enabled:
     tor --ControlPort 9051 --CookieAuthentication 1

  3. Run server with hidden service:
     python3 server.py --hidden-service

  4. Copy the .onion address and share with clients

  5. Clients connect with:
     python3 client.py --host <address>.onion

AUTHENTICATION:

  ✅ Server generates a unique 10-digit room code
  ✅ Share code with authorized users only
  ✅ Clients must provide code to join
  ✅ All other users are rejected

SECURITY:

  ✅ Room code prevents unauthorized access
  ✅ Hidden Service keeps server IP private
  ✅ Maximum anonymity with Tor
  ✅ Resistant to censorship
        """
    )
    
    parser.add_argument("--host",
                       default="127.0.0.1",
                       help="Bind to host (default: 127.0.0.1)")
    parser.add_argument("--port",
                       type=int,
                       default=5000,
                       help="Port (default: 5000)")
    parser.add_argument("--hidden-service",
                       action="store_true",
                       help="Run as Tor hidden service (requires Tor + stem)")
    
    args = parser.parse_args()
    
    # Check dependencies for hidden service
    if args.hidden_service and not TOR_AVAILABLE:
        print("\n⚠️  WARNING: stem not installed!")
        print("   Install with: pip3 install stem --break-system-packages")
        print("   Continuing without hidden service...\n")
        args.hidden_service = False
    
    try:
        server = ChatServer(
            host=args.host,
            port=args.port,
            use_tor_hidden=args.hidden_service
        )
        server.start()
    except KeyboardInterrupt:
        print("\n\n👋 Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()