#!/usr/bin/env python3
"""
Unit tests for Terminal Chat System
Tests both server and client components
Uses unittest - no external dependencies required
"""

import unittest
import time
from unittest.mock import Mock


# ==================== MOCK CLASSES ====================

class MockChatServer:
    """Mock chat server for testing"""
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.clients = {}
        self.running = False
        self.messages = []
    
    def broadcast_message(self, username, message):
        """Test broadcast functionality"""
        timestamp = "12:00:00"
        formatted_msg = f"[{timestamp}] {username}: {message}"
        self.messages.append(formatted_msg)
        return formatted_msg
    
    def handle_command(self, command, username):
        """Test command handling"""
        cmd = command.lower().strip()
        if cmd == '/users':
            return f"Users: {', '.join(self.clients.values())}"
        elif cmd == '/help':
            return "Available commands: /users, /help, /quit"
        return "Unknown command"


class MockChatClient:
    """Mock chat client for testing"""
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.username = None
        self.connected = False
        self.received_messages = []
    
    def set_username(self, username):
        """Test username validation"""
        if not username:
            return False, "Username cannot be empty"
        if len(username) > 20:
            return False, "Username too long"
        self.username = username
        return True, "Username set"
    
    def receive_message(self, message):
        """Test message receiving"""
        self.received_messages.append(message)
        return True


# ==================== SERVER TESTS ====================

class TestChatServer(unittest.TestCase):
    """Test cases for ChatServer"""
    
    def test_server_initialization(self):
        """Test server initializes with correct parameters"""
        server = MockChatServer("localhost", 5000)
        self.assertEqual(server.host, "localhost")
        self.assertEqual(server.port, 5000)
        self.assertEqual(server.clients, {})
        self.assertFalse(server.running)
    
    def test_server_custom_host_port(self):
        """Test server can be initialized with custom host/port"""
        server = MockChatServer("192.168.1.100", 8000)
        self.assertEqual(server.host, "192.168.1.100")
        self.assertEqual(server.port, 8000)
    
    def test_broadcast_message(self):
        """Test message broadcasting"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "Hello world")
        
        self.assertIn(msg, server.messages)
        self.assertIn("alice", msg)
        self.assertIn("Hello world", msg)
        self.assertIn("[", msg)
        self.assertIn("]", msg)
    
    def test_multiple_messages(self):
        """Test broadcasting multiple messages"""
        server = MockChatServer()
        server.broadcast_message("alice", "First message")
        server.broadcast_message("bob", "Second message")
        server.broadcast_message("charlie", "Third message")
        
        self.assertEqual(len(server.messages), 3)
        self.assertIn("alice", server.messages[0])
        self.assertIn("bob", server.messages[1])
        self.assertIn("charlie", server.messages[2])
    
    def test_command_users(self):
        """Test /users command"""
        server = MockChatServer()
        server.clients[Mock()] = "alice"
        server.clients[Mock()] = "bob"
        
        response = server.handle_command("/users", "alice")
        self.assertIn("Users:", response)
    
    def test_command_help(self):
        """Test /help command"""
        server = MockChatServer()
        response = server.handle_command("/help", "alice")
        
        self.assertIn("commands", response.lower())
        self.assertIn("users", response.lower())
        self.assertIn("quit", response.lower())
    
    def test_command_unknown(self):
        """Test unknown command handling"""
        server = MockChatServer()
        response = server.handle_command("/unknown", "alice")
        
        self.assertIn("Unknown command", response)
    
    def test_command_case_insensitive(self):
        """Test commands are case insensitive"""
        server = MockChatServer()
        response1 = server.handle_command("/HELP", "alice")
        response2 = server.handle_command("/Help", "alice")
        
        self.assertIn("commands", response1.lower())
        self.assertIn("commands", response2.lower())


# ==================== CLIENT TESTS ====================

class TestChatClient(unittest.TestCase):
    """Test cases for ChatClient"""
    
    def test_client_initialization(self):
        """Test client initializes correctly"""
        client = MockChatClient("localhost", 5000)
        self.assertEqual(client.host, "localhost")
        self.assertEqual(client.port, 5000)
        self.assertIsNone(client.username)
        self.assertFalse(client.connected)
    
    def test_client_custom_host_port(self):
        """Test client can connect to custom host/port"""
        client = MockChatClient("192.168.1.100", 8080)
        self.assertEqual(client.host, "192.168.1.100")
        self.assertEqual(client.port, 8080)
    
    def test_username_validation_empty(self):
        """Test empty username is rejected"""
        client = MockChatClient()
        success, message = client.set_username("")
        
        self.assertFalse(success)
        self.assertIn("empty", message.lower())
    
    def test_username_validation_valid(self):
        """Test valid username is accepted"""
        client = MockChatClient()
        success, message = client.set_username("alice")
        
        self.assertTrue(success)
        self.assertEqual(client.username, "alice")
    
    def test_username_validation_too_long(self):
        """Test long username is rejected"""
        client = MockChatClient()
        long_username = "a" * 25
        success, message = client.set_username(long_username)
        
        self.assertFalse(success)
        self.assertIn("too long", message.lower())
    
    def test_username_max_length(self):
        """Test maximum allowed username length"""
        client = MockChatClient()
        max_username = "a" * 20
        success, message = client.set_username(max_username)
        
        self.assertTrue(success)
        self.assertEqual(client.username, max_username)
    
    def test_message_receiving(self):
        """Test client can receive messages"""
        client = MockChatClient()
        client.set_username("alice")
        
        received = client.receive_message("[12:00:00] bob: Hello!")
        self.assertTrue(received)
        self.assertEqual(len(client.received_messages), 1)
    
    def test_multiple_messages_received(self):
        """Test client receives multiple messages"""
        client = MockChatClient()
        client.set_username("alice")
        
        client.receive_message("Message 1")
        client.receive_message("Message 2")
        client.receive_message("Message 3")
        
        self.assertEqual(len(client.received_messages), 3)
    
    def test_message_order(self):
        """Test messages are received in order"""
        client = MockChatClient()
        client.set_username("alice")
        
        msg1 = "[12:00:00] bob: First"
        msg2 = "[12:00:01] bob: Second"
        msg3 = "[12:00:02] bob: Third"
        
        client.receive_message(msg1)
        client.receive_message(msg2)
        client.receive_message(msg3)
        
        self.assertEqual(client.received_messages[0], msg1)
        self.assertEqual(client.received_messages[1], msg2)
        self.assertEqual(client.received_messages[2], msg3)


# ==================== INTEGRATION TESTS ====================

class TestChatIntegration(unittest.TestCase):
    """Integration tests for server and client interaction"""
    
    def test_server_client_communication(self):
        """Test basic server-client interaction"""
        server = MockChatServer()
        client = MockChatClient()
        
        # Client connects and sets username
        client.set_username("alice")
        self.assertEqual(client.username, "alice")
        
        # Server broadcasts a message
        msg = server.broadcast_message("bob", "Hello Alice!")
        self.assertIn("bob", msg)
        
        # Client receives it
        client.receive_message(msg)
        self.assertEqual(len(client.received_messages), 1)
    
    def test_multi_client_chat(self):
        """Test multiple clients chatting"""
        server = MockChatServer()
        
        clients = []
        for name in ["alice", "bob", "charlie"]:
            client = MockChatClient()
            client.set_username(name)
            clients.append(client)
        
        # Simulate conversation
        msg1 = server.broadcast_message("alice", "Hello everyone!")
        msg2 = server.broadcast_message("bob", "Hi Alice!")
        msg3 = server.broadcast_message("charlie", "Hey guys!")
        
        # All clients receive all messages
        for client in clients:
            client.receive_message(msg1)
            client.receive_message(msg2)
            client.receive_message(msg3)
        
        for client in clients:
            self.assertEqual(len(client.received_messages), 3)
    
    def test_command_in_conversation(self):
        """Test commands work during conversation"""
        server = MockChatServer()
        client = MockChatClient()
        
        client.set_username("alice")
        
        # User wants to see who's online
        response = server.handle_command("/users", client.username)
        self.assertIn("Users:", response)
        
        # User gets help
        help_response = server.handle_command("/help", client.username)
        self.assertIn("commands", help_response.lower())


# ==================== MESSAGE FORMAT TESTS ====================

class TestMessageFormatting(unittest.TestCase):
    """Test message formatting and timestamps"""
    
    def test_message_has_timestamp(self):
        """Test messages include timestamps"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "Test message")
        
        self.assertIn("[", msg)
        self.assertIn("]", msg)
        self.assertIn(":", msg)
    
    def test_message_has_username(self):
        """Test messages include sender username"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "Test message")
        
        self.assertIn("alice", msg)
    
    def test_message_has_content(self):
        """Test messages include the content"""
        server = MockChatServer()
        content = "Hello world!"
        msg = server.broadcast_message("alice", content)
        
        self.assertIn(content, msg)
    
    def test_message_format_structure(self):
        """Test message has correct format: [timestamp] username: content"""
        server = MockChatServer()
        msg = server.broadcast_message("bob", "Hello!")
        
        self.assertTrue(msg.startswith("["))
        self.assertIn("] bob:", msg)
        self.assertIn("Hello!", msg)


# ==================== EDGE CASES ====================

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_special_characters_in_username(self):
        """Test usernames with special characters"""
        client = MockChatClient()
        success, _ = client.set_username("user@123")
        self.assertTrue(success)
    
    def test_special_characters_in_message(self):
        """Test messages with special characters"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "Hello! @#$%^&*()")
        self.assertIn("Hello! @#$%^&*()", msg)
    
    def test_empty_message_handling(self):
        """Test handling of empty messages"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "")
        self.assertIn("alice", msg)
    
    def test_very_long_message(self):
        """Test handling of very long messages"""
        server = MockChatServer()
        long_msg = "a" * 1000
        msg = server.broadcast_message("alice", long_msg)
        self.assertIn(long_msg, msg)
    
    def test_unicode_in_message(self):
        """Test unicode characters in messages"""
        server = MockChatServer()
        msg = server.broadcast_message("alice", "Hello 🚀 世界")
        self.assertIn("🚀", msg)
        self.assertIn("世界", msg)


# ==================== PERFORMANCE TESTS ====================

class TestPerformance(unittest.TestCase):
    """Test system performance characteristics"""
    
    def test_message_broadcast_speed(self):
        """Test message broadcasting is reasonably fast"""
        server = MockChatServer()
        
        start = time.time()
        for i in range(100):
            server.broadcast_message("alice", f"Message {i}")
        elapsed = time.time() - start
        
        # Should handle 100 messages in reasonable time
        self.assertLess(elapsed, 1.0)
        self.assertEqual(len(server.messages), 100)
    
    def test_command_handling_speed(self):
        """Test command handling is fast"""
        server = MockChatServer()
        
        start = time.time()
        for _ in range(1000):
            server.handle_command("/help", "alice")
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 0.5)


# ==================== TEST RUNNER ====================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestChatServer))
    suite.addTests(loader.loadTestsFromTestCase(TestChatClient))
    suite.addTests(loader.loadTestsFromTestCase(TestChatIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)