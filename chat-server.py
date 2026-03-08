#!/usr/bin/env python3
"""
Terminal Chat System - Server Component
Handles multiple client connections and message broadcasting
"""

import socket
import threading
import time
from datetime import datetime
from typing import Dict, Set
import sys

class ChatServer:
    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[socket.socket, str] = {}
        self.lock = threading.Lock()
        self.running = False
        
    def start(self):
        """Start the chat server"""
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.running = True
            self.print_status(f"🚀 Server started on {self.host}:{self.port}")
            self.print_status(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.print_status("=" * 50)
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
                    
        except Exception as e:
            self.print_error(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual client connections"""
        username = None
        try:
            # Request username
            client_socket.send(b"USERNAME:")
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            if not username:
                client_socket.close()
                return
            
            with self.lock:
                self.clients[client_socket] = username
            
            # Announce user join
            join_msg = f"[{username} joined the chat]"
            self.print_status(f"✅ {username} connected from {address[0]}:{address[1]}")
            self.broadcast(join_msg, exclude=client_socket, is_system=True)
            
            # Send user list
            user_list = ", ".join(self.clients.values())
            client_socket.send(f"USERS:{user_list}".encode('utf-8'))
            
            # Main message loop
            while self.running:
                message = client_socket.recv(1024).decode('utf-8').strip()
                
                if not message:
                    continue
                
                if message.lower() in ['/quit', '/exit', '/leave']:
                    break
                
                if message.startswith('/'):
                    self.handle_command(client_socket, message, username)
                else:
                    self.broadcast_message(username, message)
        
        except ConnectionResetError:
            pass
        except Exception as e:
            if self.running:
                self.print_error(f"Error handling client: {e}")
        finally:
            if client_socket in self.clients:
                with self.lock:
                    username = self.clients.pop(client_socket, username)
                if username:
                    leave_msg = f"[{username} left the chat]"
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
            user_list = ", ".join(self.clients.values())
            client_socket.send(f"Users online: {user_list}".encode('utf-8'))
        elif cmd == '/help':
            help_text = (
                "Available commands:\n"
                "  /users  - List all online users\n"
                "  /help   - Show this help message\n"
                "  /quit   - Disconnect from chat"
            )
            client_socket.send(help_text.encode('utf-8'))
        else:
            client_socket.send(f"Unknown command: {cmd}. Type /help for available commands.".encode('utf-8'))
    
    def broadcast_message(self, username: str, message: str):
        """Broadcast a message from a user to all clients"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {username}: {message}"
        self.broadcast(formatted_msg)
        self.print_status(f"📨 {formatted_msg}")
    
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
                except:
                    pass
    
    def print_status(self, message: str):
        """Print server status message"""
        print(f"[SERVER] {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def stop(self):
        """Stop the server"""
        self.running = False
        self.print_status("Shutting down server...")
        try:
            self.server.close()
        except:
            pass


if __name__ == "__main__":
    print("\n" + "="*50)
    print("     TERMINAL CHAT SYSTEM - SERVER")
    print("="*50 + "\n")
    
    try:
        server = ChatServer()
        server.start()
    except KeyboardInterrupt:
        print("\n\nServer interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")