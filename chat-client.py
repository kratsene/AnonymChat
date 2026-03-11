#!/usr/bin/env python3
"""
Terminal Chat System - Client
Auto connection + Optional Tor privacy
"""

import socket
import threading
import sys

# Optional Tor import
try:
    import socks
    TOR_AVAILABLE = True
except ImportError:
    TOR_AVAILABLE = False
    socks = None


class ChatClient:
    """Chat client with auto connection"""
    
    def __init__(self, use_tor=False):
        self.socket = None
        self.username = None
        self.room_code = None
        self.connected = False
        self.receiving = False
        self.use_tor = use_tor and TOR_AVAILABLE
    
    def connect(self):
        """Connect to server"""
        print("\n" + "="*70)
        print("     TERMINAL CHAT SYSTEM - CLIENT")
        if self.use_tor:
            print("     🧅 TOR MODE 🧅")
        print("="*70 + "\n")
        
        # Get server IP
        print("🌐 Server IP (press Enter for 127.0.0.1):")
        host = input("   > ").strip()
        if not host:
            host = "127.0.0.1"
        
        port = 5000
        
        # Get room code
        print("\n🔐 Room code (from server):")
        self.room_code = input("   > ").strip().upper()
        
        if len(self.room_code) != 10:
            print("❌ Code must be 10 characters!")
            return
        
        # Get username
        print("\n👤 Username:")
        self.username = input("   > ").strip()
        
        if not self.username or len(self.username) > 20:
            print("❌ Username must be 1-20 characters!")
            return
        
        print(f"\n{self._divider()}")
        print(f"📡 Connecting to {host}:{port}...\n")
        
        try:
            # Create socket
            if self.use_tor and socks:
                # Tor connection
                self.socket = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.set_proxy(socks.SOCKS5, "localhost", 9050)
            else:
                # Direct connection
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            self.socket.settimeout(5)
            self.socket.connect((host, port))
            self.connected = True
            
            # Authenticate with code
            prompt = self.socket.recv(1024).decode('utf-8').strip()
            if prompt == "CODE:":
                self.socket.send(self.room_code.encode('utf-8'))
                response = self.socket.recv(1024).decode('utf-8').strip()
                
                if response != "CODE_OK":
                    print("❌ Invalid room code!")
                    self.disconnect()
                    return
            
            # Send username
            prompt = self.socket.recv(1024).decode('utf-8').strip()
            if prompt == "USERNAME:":
                self.socket.send(self.username.encode('utf-8'))
                response = self.socket.recv(1024).decode('utf-8').strip()
                
                if response != "USERNAME_OK":
                    print(f"❌ {response}")
                    self.disconnect()
                    return
            
            # Get user list
            users_msg = self.socket.recv(1024).decode('utf-8').strip()
            users = "Unknown"
            if users_msg.startswith("USERS:"):
                users = users_msg.replace("USERS:", "").strip()
            
            # Connected
            print(f"✅ Connected!")
            print(f"👤 Username: {self.username}")
            print(f"👥 Users: {users}")
            print(f"{self._divider()}\n")
            
            # Start receiving
            self.receiving = True
            receive_thread = threading.Thread(
                target=self.receive_messages,
                daemon=True
            )
            receive_thread.start()
            
            # Input loop
            self.input_loop()
            
        except socket.timeout:
            print("❌ Timeout! Server not responding")
        except ConnectionRefusedError:
            print("❌ Connection refused! Is server running?")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.disconnect()
    
    def input_loop(self):
        """Main input loop"""
        try:
            while self.connected:
                try:
                    message = input(f"{self.username}: ").strip()
                    if not message:
                        continue
                    
                    self.socket.send(message.encode('utf-8'))
                    
                    if message.lower() in ['/quit', '/exit', '/leave']:
                        break
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
        except:
            pass
    
    def receive_messages(self):
        """Receive messages from server"""
        try:
            while self.connected and self.receiving:
                try:
                    message = self.socket.recv(1024).decode('utf-8').strip()
                    if not message:
                        continue
                    
                    if message.startswith("MSG:"):
                        content = message.replace("MSG:", "").strip()
                        print(f"\r{content}\n{self.username}: ", end="", flush=True)
                    elif message.startswith("SYSTEM:"):
                        content = message.replace("SYSTEM:", "").strip()
                        print(f"\r💬 {content}\n{self.username}: ", end="", flush=True)
                    else:
                        print(f"\r{message}\n{self.username}: ", end="", flush=True)
                except:
                    break
        except:
            pass
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        self.receiving = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("👋 Disconnected\n")
    
    def _divider(self):
        """Get divider line"""
        return "="*70


if __name__ == "__main__":
    use_tor = len(sys.argv) > 1 and sys.argv[1] == '--tor'
    
    if use_tor and not TOR_AVAILABLE:
        print("\n⚠️  PySocks not installed!")
        print("   pip3 install PySocks --break-system-packages\n")
        sys.exit(1)
    
    try:
        client = ChatClient(use_tor=use_tor)
        client.connect()
    except KeyboardInterrupt:
        print("\n👋 Client stopped")
    except Exception as e:
        print(f"Error: {e}")