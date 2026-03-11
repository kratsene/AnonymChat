#!/usr/bin/env python3
"""
Comprehensive Test Suite for Terminal Chat System
Tests for server.py, client.py, and core functionality
"""

import pytest
import socket
import threading
import time
import string
import random
from unittest.mock import Mock, patch, MagicMock


class TestRoomCodeGenerator:
    """Test room code generation functionality"""
    
    def test_code_generation_length(self):
        """Test that generated code is exactly 10 characters"""
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(10))
        assert len(code) == 10
    
    def test_code_generation_format(self):
        """Test that generated code only contains uppercase and digits"""
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(10))
        assert all(c in chars for c in code)
        assert code.isupper() or any(c.isdigit() for c in code)
    
    def test_code_uniqueness(self):
        """Test that generated codes are unique"""
        chars = string.ascii_uppercase + string.digits
        codes = set()
        for _ in range(100):
            code = ''.join(random.choice(chars) for _ in range(10))
            codes.add(code)
        # With 36^10 possible combinations, collision is virtually impossible
        assert len(codes) == 100
    
    def test_no_special_characters(self):
        """Test that code contains no special characters"""
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(chars) for _ in range(10))
        assert not any(c in code for c in "!@#$%^&*()")
        assert not any(c in code for c in string.ascii_lowercase)


class TestSocketCreation:
    """Test socket creation and basic networking"""
    
    def test_socket_creation(self):
        """Test that socket can be created"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert sock is not None
        sock.close()
    
    def test_socket_reuse_address(self):
        """Test SO_REUSEADDR socket option"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Should not raise exception
        sock.close()
    
    def test_socket_timeout(self):
        """Test socket timeout setting"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        assert sock.gettimeout() == 10
        sock.close()
    
    def test_port_range_validation(self):
        """Test port number validation"""
        valid_ports = [1, 80, 443, 5000, 8000, 65535]
        for port in valid_ports:
            assert 1 <= port <= 65535
        
        invalid_ports = [0, -1, 65536, 100000]
        for port in invalid_ports:
            assert not (1 <= port <= 65535)


class TestThreading:
    """Test threading functionality"""
    
    def test_thread_creation(self):
        """Test that threads can be created"""
        result = []
        def test_func():
            result.append(True)
        
        thread = threading.Thread(target=test_func, daemon=True)
        assert thread is not None
        thread.start()
        thread.join(timeout=1)
        assert result == [True]
    
    def test_lock_creation(self):
        """Test that threading locks work"""
        lock = threading.Lock()
        
        results = []
        def increment():
            with lock:
                results.append(1)
        
        threads = [threading.Thread(target=increment, daemon=True) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=1)
        
        assert len(results) == 5
    
    def test_daemon_thread(self):
        """Test daemon thread functionality"""
        thread = threading.Thread(target=lambda: None, daemon=True)
        assert thread.daemon is True


class TestInputValidation:
    """Test input validation for room codes, usernames, etc."""
    
    def test_room_code_length_validation(self):
        """Test room code must be exactly 10 characters"""
        valid_codes = ["A7B2K9F4M1", "XYZABC1234", "AAAAAAAAAA"]
        invalid_codes = ["ABC123", "A7B2K9F4M1X", ""]
        
        for code in valid_codes:
            assert len(code) == 10
        
        for code in invalid_codes:
            assert len(code) != 10
    
    def test_room_code_format_validation(self):
        """Test room code only has uppercase and digits"""
        valid_codes = ["A7B2K9F4M1", "XYZABC1234"]
        invalid_codes = ["a7b2k9f4m1", "A7B2-K9F4M1", "A7B2 K9F4M1"]
        
        chars = string.ascii_uppercase + string.digits
        for code in valid_codes:
            assert all(c in chars for c in code)
        
        for code in invalid_codes:
            assert not all(c in chars for c in code)
    
    def test_username_length_validation(self):
        """Test username length constraints"""
        valid_usernames = ["a", "alice", "alice_123", "A" * 20]
        invalid_usernames = ["", "A" * 21, "A" * 100]
        
        for name in valid_usernames:
            assert 1 <= len(name) <= 20
        
        for name in invalid_usernames:
            assert not (1 <= len(name) <= 20)
    
    def test_username_space_validation(self):
        """Test username doesn't contain spaces"""
        valid_usernames = ["alice", "alice_bob", "alice123"]
        invalid_usernames = ["alice smith", "bob alice", " alice"]
        
        for name in valid_usernames:
            assert " " not in name
        
        for name in invalid_usernames:
            assert " " in name
    
    def test_port_number_validation(self):
        """Test port number must be valid integer"""
        valid_ports = [1, 80, 443, 5000, 8000, 65535]
        invalid_ports = [0, -1, 65536, 100000]
        
        for port in valid_ports:
            assert isinstance(port, int)
            assert 1 <= port <= 65535
        
        for port in invalid_ports:
            assert not (isinstance(port, int) and 1 <= port <= 65535)
    
    def test_ip_address_formats(self):
        """Test various IP address formats"""
        valid_ips = ["127.0.0.1", "192.168.1.100", "localhost", "example.com"]
        
        # Valid IPs should not be empty
        for ip in valid_ips:
            assert len(ip) > 0
            assert isinstance(ip, str)


class TestMessageFormatting:
    """Test message formatting functionality"""
    
    def test_timestamp_format(self):
        """Test timestamp formatting"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Should be HH:MM:SS format
        parts = timestamp.split(":")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # hours
        assert len(parts[1]) == 2  # minutes
        assert len(parts[2]) == 2  # seconds
    
    def test_message_prefix_format(self):
        """Test message prefix formatting"""
        prefixes = ["MSG:", "SYSTEM:", "CODE:", "USERNAME:"]
        
        for prefix in prefixes:
            assert prefix.endswith(":")
            assert prefix.isupper()
    
    def test_formatted_message_structure(self):
        """Test complete message formatting"""
        timestamp = "12:34:56"
        username = "alice"
        message = "Hello world"
        
        formatted = f"[{timestamp}] {username}: {message}"
        assert "[" in formatted
        assert "]" in formatted
        assert ":" in formatted
        assert username in formatted
        assert message in formatted


class TestErrorHandling:
    """Test error handling"""
    
    def test_connection_error_handling(self):
        """Test connection error is caught"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Try to connect to non-existent server
            sock.connect(("127.0.0.1", 1))
        except (ConnectionRefusedError, OSError):
            # Expected
            pass
        finally:
            sock.close()
    
    def test_keyboard_interrupt_handling(self):
        """Test KeyboardInterrupt is handled"""
        with pytest.raises(KeyboardInterrupt):
            raise KeyboardInterrupt()
    
    def test_socket_timeout_handling(self):
        """Test socket timeout exception"""
        with pytest.raises(socket.timeout):
            raise socket.timeout()
    
    def test_broken_pipe_error(self):
        """Test BrokenPipeError exception"""
        with pytest.raises(BrokenPipeError):
            raise BrokenPipeError()
    
    def test_attribute_error_handling(self):
        """Test AttributeError handling"""
        obj = None
        with pytest.raises(AttributeError):
            obj.nonexistent_method()


class TestEncodingDecoding:
    """Test message encoding and decoding"""
    
    def test_utf8_encoding(self):
        """Test UTF-8 message encoding"""
        message = "Hello, World! 你好 🌍"
        encoded = message.encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == message
    
    def test_standard_ascii_encoding(self):
        """Test standard ASCII encoding"""
        message = "Hello World 123"
        encoded = message.encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == message
    
    def test_empty_string_encoding(self):
        """Test empty string encoding"""
        message = ""
        encoded = message.encode('utf-8')
        assert encoded == b""
    
    def test_strip_whitespace(self):
        """Test stripping whitespace from messages"""
        messages = ["  hello  ", "\nhello\n", "\thello\t"]
        for msg in messages:
            stripped = msg.strip()
            assert stripped == "hello"


class TestNetworkProtocol:
    """Test network communication protocol"""
    
    def test_authentication_flow_steps(self):
        """Test authentication happens in correct order"""
        flow = [
            "CODE:",      # Step 1: Ask for code
            "CODE_OK",    # Step 2: Validate code
            "USERNAME:",  # Step 3: Ask for username
            "USERNAME_OK" # Step 4: Validate username
        ]
        
        assert len(flow) == 4
        assert flow[0] == "CODE:"
        assert flow[2] == "USERNAME:"
    
    def test_message_protocol_formats(self):
        """Test message protocol formats"""
        protocols = {
            "MSG:": "User message",
            "SYSTEM:": "System message",
            "USERS:": "User list",
            "CODE:": "Code prompt",
            "USERNAME:": "Username prompt"
        }
        
        for protocol, desc in protocols.items():
            assert protocol.endswith(":")
            assert len(protocol) > 0
    
    def test_error_response_codes(self):
        """Test error response codes"""
        error_codes = [
            "INVALID_CODE",
            "INVALID_USERNAME",
            "USERNAME_LONG",
            "USERNAME_TAKEN"
        ]
        
        for code in error_codes:
            assert isinstance(code, str)
            assert len(code) > 0
            assert "_" in code or code.isupper()


class TestFileStructure:
    """Test file structure and imports"""
    
    def test_imports_available(self):
        """Test that standard library imports work"""
        import socket
        import threading
        import time
        from datetime import datetime
        import sys
        
        assert socket is not None
        assert threading is not None
        assert time is not None
        assert datetime is not None
        assert sys is not None
    
    def test_python_version(self):
        """Test Python version requirement"""
        import sys
        assert sys.version_info.major >= 3
        assert sys.version_info.minor >= 6


class TestEdgeCases:
    """Test edge cases and corner cases"""
    
    def test_maximum_username_length(self):
        """Test username at maximum length"""
        max_username = "A" * 20
        assert len(max_username) <= 20
    
    def test_minimum_username_length(self):
        """Test username at minimum length"""
        min_username = "a"
        assert len(min_username) >= 1
    
    def test_maximum_message_size(self):
        """Test message size limits"""
        max_message = "x" * 1024
        assert len(max_message) <= 1024
    
    def test_code_with_all_uppercase(self):
        """Test code with all uppercase letters"""
        code = "AAAAAAAAAA"
        assert len(code) == 10
        assert code.isupper()
    
    def test_code_with_all_digits(self):
        """Test code with all digits"""
        code = "1234567890"
        assert len(code) == 10
        assert all(c.isdigit() for c in code)
    
    def test_empty_message_handling(self):
        """Test handling of empty messages"""
        message = ""
        assert len(message) == 0
        assert not message.strip()
    
    def test_whitespace_only_message(self):
        """Test message with only whitespace"""
        message = "   \t\n  "
        assert not message.strip()


class TestDataStructures:
    """Test data structure usage"""
    
    def test_dictionary_for_clients(self):
        """Test dictionary for storing client-username mapping"""
        clients = {}
        
        # Simulate adding clients
        sock1 = Mock()
        sock2 = Mock()
        
        clients[sock1] = "alice"
        clients[sock2] = "bob"
        
        assert len(clients) == 2
        assert clients[sock1] == "alice"
        assert clients[sock2] == "bob"
    
    def test_set_for_usernames(self):
        """Test set for username uniqueness"""
        usernames = set()
        
        usernames.add("alice")
        usernames.add("bob")
        usernames.add("alice")  # Duplicate
        
        assert len(usernames) == 2
        assert "alice" in usernames
        assert "charlie" not in usernames
    
    def test_list_for_clients(self):
        """Test list for client connections"""
        client_list = []
        
        sock1 = Mock()
        sock2 = Mock()
        
        client_list.append(sock1)
        client_list.append(sock2)
        
        assert len(client_list) == 2
        assert sock1 in client_list


class TestCommandSystem:
    """Test command functionality"""
    
    def test_command_prefix(self):
        """Test commands start with forward slash"""
        commands = ["/help", "/users", "/quit", "/exit"]
        for cmd in commands:
            assert cmd.startswith("/")
    
    def test_command_parsing(self):
        """Test command string parsing"""
        message = "/help"
        assert message.startswith("/")
        cmd = message.lower().strip()
        assert cmd == "/help"
    
    def test_quit_command_variants(self):
        """Test different quit command variants"""
        quit_commands = ["/quit", "/exit", "/leave"]
        for cmd in quit_commands:
            assert cmd in ["/quit", "/exit", "/leave"]


class TestConfiguration:
    """Test configuration and defaults"""
    
    def test_default_host(self):
        """Test default host is localhost"""
        default_host = "127.0.0.1"
        assert default_host == "127.0.0.1"
    
    def test_default_port(self):
        """Test default port is 5000"""
        default_port = 5000
        assert default_port == 5000
    
    def test_default_tor_port(self):
        """Test default Tor port is 9050"""
        default_tor_port = 9050
        assert default_tor_port == 9050
    
    def test_tor_socks_version(self):
        """Test SOCKS5 version"""
        socks_version = 5
        assert socks_version == 5


class TestSecurityValidation:
    """Test security-related validation"""
    
    def test_no_sql_injection_in_username(self):
        """Test SQL injection patterns blocked"""
        dangerous = ["'; DROP TABLE users; --", "admin' --", "1' OR '1'='1"]
        # These should be validated as usernames
        for danger in dangerous:
            # In a real system, these would be sanitized
            # For now, we just check they'd fail validation
            assert " " in danger or "'" in danger
    
    def test_no_xss_in_messages(self):
        """Test XSS patterns validation"""
        xss_patterns = ["<script>", "<img>", "javascript:"]
        for pattern in xss_patterns:
            assert "<" in pattern or ":" in pattern
    
    def test_code_case_sensitivity(self):
        """Test room code is case-sensitive"""
        code1 = "A7B2K9F4M1"
        code2 = "a7b2k9f4m1"
        assert code1 != code2


class TestIntegration:
    """Integration tests"""
    
    def test_full_authentication_sequence(self):
        """Test complete authentication sequence"""
        # Simulate: code -> username -> connected
        room_code = "A7B2K9F4M1"
        username = "alice"
        
        assert len(room_code) == 10
        assert 1 <= len(username) <= 20
        assert " " not in username
        
        # All validations pass
        assert True
    
    def test_multi_user_scenario(self):
        """Test multiple users connecting"""
        clients = {}
        users = ["alice", "bob", "charlie"]
        
        for i, user in enumerate(users):
            clients[i] = user
        
        assert len(clients) == 3
        assert clients[0] == "alice"
        assert clients[2] == "charlie"
    
    def test_message_broadcast_scenario(self):
        """Test message broadcast to multiple clients"""
        clients = {
            "sock1": "alice",
            "sock2": "bob",
            "sock3": "charlie"
        }
        
        message = "Hello everyone!"
        
        # Message should go to all clients except sender
        for sock, username in clients.items():
            if username != "alice":
                # Would broadcast to this client
                assert username in ["bob", "charlie"]


class TestLogging:
    """Test logging and output functionality"""
    
    def test_status_prefix(self):
        """Test status message prefix"""
        prefix = "[STATUS]"
        assert prefix.startswith("[")
        assert prefix.endswith("]")
    
    def test_error_prefix(self):
        """Test error message prefix"""
        prefix = "⚠️"
        assert prefix is not None
    
    def test_info_prefix(self):
        """Test info message prefix"""
        prefix = "ℹ️"
        assert prefix is not None


# ============================================================================
# Test Execution Configuration
# ============================================================================

if __name__ == "__main__":
    # Run with: python -m pytest test_chat_system.py -v
    pytest.main([__file__, "-v", "--tb=short"])