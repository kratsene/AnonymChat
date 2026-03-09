#!/usr/bin/env python3
"""
Terminal Chat System - Secure Client with Room Authentication
Uses 10-digit alphanumeric room codes for secure access

Features:
- Room authentication with unique codes
- Routes through Tor network (optional)
- End-to-end encryption ready
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
except ImportError:
    SOCKS_AVAILABLE = False


class TorChatClient:
    """Chat client with room authentication and Tor SOCKS proxy support"""
    
    def __init__(self, host=None, port=None, use_tor=False, tor_port=9050):
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.room_code = None
        self.connected = False
        self.use_tor = use_tor and SOCKS_AVAILABLE
        self.tor_port = tor_port
        self.connection_method = "Tor" if self.use_tor else "Direct"
        self.receiving = False
    
    def get_connection_details(self):
        """Get server IP, port, and room code from user interactively"""
        self.clear_screen()
        self.print_header()
        
        print("\n📡 CONNECTION SETUP")
        print("=" * 70)
        
        # Get server IP/Host
        while not self.host:
            try:
                host_input = input("\n🌐 Enter server IP or hostname (default: 127.0.0.1): ").strip()
                if not host_input:
                    self.host = "127.0.0.1"
                else:
                    self.host = host_input
            except KeyboardInterrupt:
                sys.exit(0)
            except EOFError:
                sys.exit(0)
        
        # Get port
        while not self.port:
            try:
                port_input = input("🔌 Enter server port (default: 5000): ").strip()
                if not port_input:
                    self.port = 5000
                else:
                    try:
                        port_num = int(port_input)
                        if 1 <= port_num <= 65535:
                            self.port = port_num
                        else:
                            self.print_error("Port must be between 1 and 65535")
                            continue
                    except ValueError:
                        self.print_error("Port must be a number")
                        continue
            except KeyboardInterrupt:
                sys.exit(0)
            except EOFError:
                sys.exit(0)
        
        # Get room code
        self.get_room_code()
        
        print("\n" + "=" * 70)
        self.print_info(f"Connecting to {self.host}:{self.port}")
        time.sleep(1)
    
    def connect(self):
        """Connect to the chat server with authentication"""
        try:
            # Create socket
            if self.use_tor:
                self.print_status("🔐 Connecting through Tor SOCKS proxy...")
                self.socket = self._create_tor_socket()
            else:
                self.print_status("📡 Connecting to server...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            self.socket.settimeout(10)
            
            # Connect to server
            try:
                self.socket.connect((self.host, self.port))
            except socket.timeout:
                self.print_error("❌ Connection timeout. Server not responding.")
                self.disconnect()
                return
            except ConnectionRefusedError:
                self.print_error("❌ Connection refused. Is the server running?")
                self.disconnect()
                return
            
            self.connected = True
            
            # Step 1: Authenticate with room code
            if not self._authenticate():
                self.disconnect()
                return
            
            # Step 2: Set username
            if not self._setup_username():
                self.disconnect()
                return
            
            # Step 3: Receive and display user list
            if not self._receive_user_list():
                self.disconnect()
                return
            
            # Clear screen and show welcome
            self.clear_screen()
            self.print_header()
            self.print_info(f"✅ Connected via {self.connection_method}!")
            self.print_info(f"👤 Username: {self.username}")
            self.print_info(f"🔐 Room Code: {self.room_code}")
            self.print_divider()
            
            # Start receiving messages in background
            self.receiving = True
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # Start input loop
            self.input_loop()
            
        except Exception as e:
            self.print_error(f"Connection error: {e}")
            if self.use_tor:
                self.print_error("💡 Tip: Make sure Tor is running (tor --SocksPort 9050)")
        finally:
            self.disconnect()
    
    def _authenticate(self):
        """Authenticate with room code"""
        try:
            # Wait for code prompt
            prompt = self.socket.recv(1024).decode('utf-8').strip()
            
            if prompt != "CODE:":
                self.print_error("❌ Invalid server response")
                return False
            
            # Get room code from user
            self.get_room_code()
            
            # Send code
            self.socket.send(self.room_code.encode('utf-8'))
            
            # Wait for authentication response
            response = self.socket.recv(1024).decode('utf-8').strip()
            
            if response == "INVALID_CODE":
                self.print_error("❌ Invalid room code. Access denied!")
                return False
            elif response == "CODE_OK":
                self.print_info("✅ Room code accepted")
                return True
            else:
                self.print_error(f"❌ Unexpected server response: {response}")
                return False
        
        except socket.timeout:
            self.print_error("❌ Authentication timeout")
            return False
        except Exception as e:
            self.print_error(f"❌ Authentication error: {e}")
            return False
    
    def _setup_username(self):
        """Set up username with server"""
        try:
            # Wait for username prompt
            prompt = self.socket.recv(1024).decode('utf-8').strip()
            
            if prompt != "USERNAME:":
                self.print_error("❌ Invalid server response")
                return False
            
            # Get username from user
            self.get_username()
            
            # Send username
            self.socket.send(self.username.encode('utf-8'))
            
            # Wait for username response
            response = self.socket.recv(1024).decode('utf-8').strip()
            
            if response == "INVALID_USERNAME":
                self.print_error("❌ Invalid username")
                return False
            elif response == "USERNAME_LONG":
                self.print_error("❌ Username too long (max 20 characters)")
                return False
            elif response == "USERNAME_TAKEN":
                self.print_error("❌ Username already taken")
                return False
            elif response == "USERNAME_OK":
                self.print_info("✅ Username accepted")
                return True
            else:
                self.print_error(f"❌ Unexpected response: {response}")
                return False
        
        except socket.timeout:
            self.print_error("❌ Username setup timeout")
            return False
        except Exception as e:
            self.print_error(f"❌ Username setup error: {e}")
            return False
    
    def _receive_user_list(self):
        """Receive initial user list from server"""
        try:
            users_msg = self.socket.recv(1024).decode('utf-8').strip()
            
            if users_msg.startswith("USERS:"):
                users = users_msg.replace("USERS:", "").strip()
                self.print_info(f"👥 Users online: {users}")
                return True
            else:
                self.print_error(f"❌ Unexpected response: {users_msg}")
                return False
        
        except socket.timeout:
            self.print_error("❌ User list timeout")
            return False
        except Exception as e:
            self.print_error(f"❌ Error receiving user list: {e}")
            return False
    
    def _create_tor_socket(self):
        """Create a socket connected through Tor SOCKS5 proxy"""
        if not SOCKS_AVAILABLE:
            raise ImportError("PySocks not installed. Install with: pip3 install PySocks --break-system-packages")
        
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, "localhost", self.tor_port)
        return sock
    
    def get_room_code(self):
        """Get room code from user"""
        while not self.room_code:
            try:
                code = input("\n🔐 Enter room code (10 characters): ").strip().upper()
                if not code:
                    self.print_error("Room code cannot be empty!")
                    continue
                if len(code) != 10:
                    self.print_error("Room code must be exactly 10 characters!")
                    continue
                self.room_code = code
            except KeyboardInterrupt:
                sys.exit(0)
            except EOFError:
                sys.exit(0)
    
    def get_username(self):
        """Get username from user"""
        while not self.username:
            try:
                username = input("👤 Enter your username (max 20 characters): ").strip()
                if not username:
                    self.print_error("Username cannot be empty!")
                    continue
                if len(username) > 20:
                    self.print_error("Username too long (max 20 characters)")
                    continue
                if " " in username:
                    self.print_error("Username cannot contain spaces")
                    continue
                self.username = username
            except KeyboardInterrupt:
                sys.exit(0)
            except EOFError:
                sys.exit(0)
    
    def input_loop(self):
        """Main input loop for sending messages"""
        try:
            self.print_info("Type your message (or /help for commands):\n")
            while self.connected:
                try:
                    message = input(f"{self.username}: ").strip()
                    if not message:
                        continue
                    
                    self.socket.send(message.encode('utf-8'))
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except BrokenPipeError:
                    break
        except Exception as e:
            if self.connected:
                self.print_error(f"Input error: {e}")
    
    def receive_messages(self):
        """Receive messages from server"""
        try:
            while self.connected and self.receiving:
                try:
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
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except (UnicodeDecodeError, AttributeError):
                    continue
        except Exception:
            pass
        finally:
            self.receiving = False
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        self.receiving = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.print_info("👋 Disconnected from chat server")
    
    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="", flush=True)
    
    def print_header(self):
        """Print chat header with connection info"""
        print("=" * 70)
        if self.use_tor:
            print("     TERMINAL CHAT SYSTEM - TOR ENCRYPTED CLIENT 🔐🧅")
        else:
            print("     TERMINAL CHAT SYSTEM - SECURE CLIENT 🔐")
        print("=" * 70)
        print()
    
    def print_divider(self):
        """Print divider line"""
        print("-" * 70)
        print("Type /help for commands\n")
    
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
        description="Terminal Chat System - Secure Client with Room Authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE:

  Interactive mode (recommended):
    python3 client.py
    
    The program will ask for:
      - Server IP/hostname
      - Server port
      - Room authentication code

  Command line mode:
    python3 client.py --host 127.0.0.1 --port 5000

  With Tor encryption:
    python3 client.py --use-tor

EXAMPLE FLOW:

  Server: runs on 127.0.0.1:5000
          generates code: A7B2K9F4M1
  
  Client: python3 client.py
          Server IP: 127.0.0.1
          Server port: 5000
          Room code: A7B2K9F4M1
          Username: alice
          ✅ Connected!

AUTHENTICATION:

  ✅ Server provides a 10-digit room code
  ✅ Enter this code when prompted
  ✅ Without code, connection is rejected
  ✅ Only authorized users can join

SECURITY NOTES:

  ✅ Always use unique, non-identifiable usernames
  ✅ For maximum privacy, use Tor: --use-tor
  ✅ Don't share room code with untrusted people
  ✅ Check username list regularly
  
  ❌ Don't use your real name as username
  ❌ Don't maximize window (fingerprinting)
  ❌ Don't run other applications while chatting

COMMANDS IN CHAT:

  /help    - Show help message
  /users   - List all online users
  /count   - Show number of users
  /quit    - Disconnect from chat

REQUIREMENTS:

  Basic (direct connection):
    - Python 3.6+

  For Tor support (encrypted):
    - pip3 install PySocks --break-system-packages
    - Tor running: tor --SocksPort 9050

TROUBLESHOOTING:

  "Connection refused"?
    1. Make sure server is running
    2. Check correct IP and port
    3. Verify room code is correct
  
  "Invalid room code"?
    1. Get correct code from server
    2. Code must be exactly 10 characters
    3. Use UPPERCASE letters
  
  Tor not working?
    1. Start Tor: tor --SocksPort 9050
    2. Wait for "circuit opened"
    3. Try again
        """
    )
    
    parser.add_argument("--host",
                       default=None,
                       help="Server host (skip prompt if provided)")
    parser.add_argument("--port",
                       type=int,
                       default=None,
                       help="Server port (skip prompt if provided)")
    parser.add_argument("--use-tor",
                       action="store_true",
                       help="Use Tor SOCKS proxy (requires Tor running)")
    parser.add_argument("--tor-port",
                       type=int,
                       default=9050,
                       help="Tor SOCKS port (default: 9050)")
    
    args = parser.parse_args()
    
    # Check PySocks availability for Tor
    if args.use_tor and not SOCKS_AVAILABLE:
        print("\n⚠️  WARNING: PySocks not installed!")
        print("   Install with: pip3 install PySocks --break-system-packages")
        print("   Or run without --use-tor flag for direct connection\n")
        sys.exit(1)
    
    try:
        client = TorChatClient(
            host=args.host,
            port=args.port,
            use_tor=args.use_tor,
            tor_port=args.tor_port
        )
        
        # Get connection details interactively if not provided via command line
        if not client.host or not client.port:
            client.get_connection_details()
        else:
            # If provided via args, still need room code
            client.clear_screen()
            client.print_header()
            client.get_room_code()
        
        client.connect()
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()