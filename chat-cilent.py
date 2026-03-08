#!/usr/bin/env python3
"""
Terminal Chat System - Client Component
Connects to chat server and provides interactive terminal interface
"""

import socket
import threading
import sys
import time
from datetime import datetime

class ChatClient:
    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.connected = False
        
    def connect(self):
        """Connect to the chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                self.print_info(f"✅ Connected! Users online: {users}")
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
        finally:
            self.disconnect()
    
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
        """Print chat header"""
        print("=" * 60)
        print("          TERMINAL CHAT SYSTEM - CLIENT")
        print("=" * 60)
        print()
    
    def print_divider(self):
        """Print divider line"""
        print("-" * 60)
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"⚠️  {message}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Terminal Chat System Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 chat_client.py                    # Connect to localhost:5000
  python3 chat_client.py -h 192.168.1.100  # Connect to specific host
  python3 chat_client.py -p 8000            # Connect to specific port
        """
    )
    parser.add_argument("-host", "-h", "--host", 
                       default="localhost",
                       help="Server host (default: localhost)")
    parser.add_argument("-port", "-p", "--port", 
                       type=int, 
                       default=5000,
                       help="Server port (default: 5000)")
    
    args = parser.parse_args()
    
    try:
        client = ChatClient(host=args.host, port=args.port)
        client.connect()
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
