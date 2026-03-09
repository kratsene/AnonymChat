#!/usr/bin/env python3
"""
Terminal Chat System - Tor-Enabled Client
Encrypts all traffic through Tor SOCKS proxy for anonymity and privacy

Features:
- Routes through Tor network
- End-to-end encryption
- SOCKS5 proxy support
- Fallback to direct connection
"""

import socket
import threading
import sys
import time
from datetime import datetime

# Try to import PySocks for SOCKS support
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError as e:
    SOCKS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TorChatClient:
    """Chat client with Tor SOCKS proxy support"""
    
    def __init__(self, host="localhost", port=5000, use_tor=True, tor_port=9050):
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.connected = False
        self.use_tor = use_tor and SOCKS_AVAILABLE
        self.tor_port = tor_port
        self.connection_method = "Tor" if self.use_tor else "Direct"
    
    def connect(self):
        """Connect to the chat server"""
        try:
            # Create socket
            if self.use_tor:
                self.print_status("🔐 Connecting through Tor SOCKS proxy...")
                self.socket = self._create_tor_socket()
            else:
                self.print_status("📡 Connecting directly (Tor disabled)...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to server
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Receive username prompt
            prompt = self.socket.recv(1024).decode('utf-8').strip()
            if prompt == "USERNAME:":
                self.get_username()
                self.socket.send(self.username.encode('utf-8'))
            
            # Receive user list
            users_msg = self.socket.recv(1024).decode('utf-8')
            if users_msg.startswith("USERS:"):
                users = users_msg.replace("USERS:", "").strip()
                self.clear_screen()
                self.print_header()
                self.print_info(f"✅ Connected via {self.connection_method}!")
                self.print_info(f"👥 Users online: {users}")
                self.print_divider()
            
            # Start receiving messages
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # Start input loop
            self.input_loop()
            
        except ConnectionRefusedError:
            self.print_error("❌ Connection refused. Is the server running?")
        except Exception as e:
            self.print_error(f"Connection error: {e}")
            if self.use_tor:
                self.print_error("💡 Tip: Make sure Tor is running (tor --SocksPort 9050)")
        finally:
            self.disconnect()
    
    def _create_tor_socket(self):
        """Create a socket connected through Tor SOCKS5 proxy"""
        if not SOCKS_AVAILABLE:
            raise ImportError("PySocks not installed. Install with: pip3 install PySocks")
        
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, "localhost", self.tor_port)
        return sock
    
    def get_username(self):
        """Get username from user"""
        while not self.username:
            try:
                username = input("\n👤 Enter your username: ").strip()
                if not username:
                    self.print_error("Username cannot be empty!")
                    continue
                if len(username) > 20:
                    self.print_error("Username too long (max 20 characters)")
                    continue
                self.username = username
            except KeyboardInterrupt:
                sys.exit(0)
    
    def input_loop(self):
        """Main input loop for sending messages"""
        try:
            print("Type your message (or /help for commands):\n")
            while self.connected:
                try:
                    message = input(f"{self.username}: ").strip()
                    if message:
                        self.socket.send(message.encode('utf-8'))
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
        except Exception as e:
            self.print_error(f"Input error: {e}")
    
    def receive_messages(self):
        """Receive messages from server"""
        try:
            while self.connected:
                message = self.socket.recv(1024).decode('utf-8').strip()
                if not message:
                    continue
                
                if message.startswith("MSG:"):
                    msg_content = message.replace("MSG:", "").strip()
                    print(f"\r{msg_content}\n{self.username}: ", end="", flush=True)
                elif message.startswith("SYSTEM:"):
                    msg_content = message.replace("SYSTEM:", "").strip()
                    print(f"\r💬 {msg_content}\n{self.username}: ", end="", flush=True)
                else:
                    print(f"\r{message}\n{self.username}: ", end="", flush=True)
        except:
            pass
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.print_info("👋 Disconnected from chat server")
    
    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="")
    
    def print_header(self):
        """Print chat header with Tor indicator"""
        print("=" * 70)
        if self.use_tor:
            print("     TERMINAL CHAT SYSTEM - TOR ENCRYPTED CLIENT 🔐🧅")
        else:
            print("     TERMINAL CHAT SYSTEM - DIRECT CONNECTION CLIENT 📡")
        print("=" * 70)
        print()
    
    def print_divider(self):
        """Print divider line"""
        print("-" * 70)
    
    def print_status(self, message):
        """Print status message"""
        print(f"[STATUS] {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"⚠️  {message}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Terminal Chat System - Tor-Enabled Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE EXAMPLES:

  With Tor (encrypted, requires 'tor --SocksPort 9050'):
    python3 chat_client_tor.py

  Connect to custom server via Tor:
    python3 chat_client_tor.py --host 192.168.1.100

  Custom Tor SOCKS port:
    python3 chat_client_tor.py --tor-port 9150

  Disable Tor (direct connection):
    python3 chat_client_tor.py --no-tor

REQUIREMENTS:

  For Tor support:
    pip3 install PySocks --break-system-packages
  
  For hidden services:
    pip3 install stem --break-system-packages
  
  External:
    Download and run Tor from torproject.org
    Or: sudo apt-get install tor (Linux)

SECURITY NOTES:

  ✅ Always start Tor before connecting: tor --SocksPort 9050
  ✅ Wait for "Tor has successfully opened a circuit"
  ✅ Don't use real names in username (can be logged)
  ✅ Check your Tor circuit regularly
  
  ❌ Don't use if local Tor is compromised
  ❌ Don't maximize window (fingerprinting)
  ❌ Don't visit other sites while chatting (breaks anonymity)

TROUBLESHOOTING:

  Connection refused?
    1. Start Tor: tor --SocksPort 9050
    2. Wait for bootstrap message
    3. Try again
  
  PySocks not found?
    pip3 install PySocks --break-system-packages
  
  Slow connection?
    Normal with Tor (3-5 second latency expected)
        """
    )
    
    parser.add_argument("--host",
                       default="localhost",
                       help="Server host (default: localhost)")
    parser.add_argument("--port",
                       type=int,
                       default=5000,
                       help="Server port (default: 5000)")
    parser.add_argument("--no-tor",
                       action="store_true",
                       help="Disable Tor (use direct connection)")
    parser.add_argument("--tor-port",
                       type=int,
                       default=9050,
                       help="Tor SOCKS port (default: 9050)")
    
    args = parser.parse_args()
    
    # Check PySocks availability
    if not SOCKS_AVAILABLE and not args.no_tor:
        print("\n⚠️  WARNING: PySocks not installed!")
        print("   Install with: pip3 install PySocks --break-system-packages")
        print("   Or use --no-tor flag for direct connection\n")
    
    try:
        client = TorChatClient(
            host=args.host,
            port=args.port,
            use_tor=not args.no_tor,
            tor_port=args.tor_port
        )
        client.connect()
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()