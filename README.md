# Terminal Chat System 💬

A lightweight, multi-user chat system designed to run in terminals. Connect multiple clients to a server and chat in real-time with timestamps and user notifications.

## Features

✨ **Core Features:**
- 🚀 Multi-client support with threading
- 📨 Real-time message broadcasting
- 👥 User join/leave notifications
- ⏰ Message timestamps
- 🎯 Command support (/users, /help, /quit)
- 🔌 Clean disconnection handling
- 📝 Colorful terminal output with emojis

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Installation

1. **Clone or download the files:**
   ```bash
   git clone <repository-url>
   cd terminal-chat-system
   # Or copy chat_server.py and chat_client.py to your directory
   ```

2. **Make files executable (optional):**
   ```bash
   chmod +x chat_server.py
   chmod +x chat_client.py
   ```

## Usage

### Step 1: Start the Server

Open a terminal and run:

```bash
python3 chat_server.py
```

You should see:
```
==================================================
     TERMINAL CHAT SYSTEM - SERVER
==================================================

[SERVER] 🚀 Server started on localhost:5000
[SERVER] ⏰ 2024-03-08 12:34:56
==================================================
[SERVER] Waiting for connections...
```

### Step 2: Connect Clients

Open new terminal windows and run:

```bash
python3 chat_client.py
```

Or with custom host/port:

```bash
python3 chat_client.py --host 192.168.1.100 --port 8000
```

**Command-line Options:**
- `--host` or `-h`: Server hostname/IP (default: localhost)
- `--port` or `-p`: Server port (default: 5000)

### Step 3: Start Chatting

1. Enter your username when prompted
2. Type messages and press Enter to send
3. Messages appear with timestamps and sender names
4. See notifications when users join/leave

## Commands

While chatting, you can use these commands:

| Command | Description |
|---------|-------------|
| `/users` | List all currently online users |
| `/help` | Show available commands |
| `/quit` or `/exit` | Disconnect from chat |
| `/leave` | Disconnect from chat |

Example:
```
alice: /users
Users online: alice, bob, charlie

bob: Hello everyone!
[12:34:56] alice: Hi Bob!
```

## Architecture

### Server (`chat_server.py`)

- **Port:** Listens on specified port (default 5000)
- **Threading:** One thread per client connection
- **Broadcast:** Sends messages to all connected clients
- **Thread Safety:** Uses locks to prevent race conditions

### Client (`chat_client.py`)

- **Two-thread model:**
  - Main thread: Handles user input
  - Receive thread: Listens for incoming messages
- **Message types:** Regular messages, system messages, commands

## Example Session

**Terminal 1 (Server):**
```
==================================================
     TERMINAL CHAT SYSTEM - SERVER
==================================================

[SERVER] 🚀 Server started on localhost:5000
[SERVER] ⏰ 2024-03-08 12:34:56
==================================================
[SERVER] Waiting for connections...

[SERVER] ✅ alice connected from 127.0.0.1:54321
[SERVER] 📨 [12:35:01] alice: Hey everyone!
[SERVER] ✅ bob connected from 127.0.0.1:54322
[SERVER] 📨 [12:35:05] bob: Hi Alice!
```

**Terminal 2 (Client - Alice):**
```
============================================================
          TERMINAL CHAT SYSTEM - CLIENT
============================================================

ℹ️  ✅ Connected! Users online: alice

Type your message (or /help for commands):

💬 [bob joined the chat]
alice: Hey everyone!
💬 [bob joined the chat]
[12:35:05] bob: Hi Alice!
alice: 
```

**Terminal 3 (Client - Bob):**
```
============================================================
          TERMINAL CHAT SYSTEM - CLIENT
============================================================

ℹ️  ✅ Connected! Users online: alice, bob

Type your message (or /help for commands):

💬 [You successfully connected]
[12:35:01] alice: Hey everyone!
bob: Hi Alice!
```

## Network Configuration

### Local Network:

To connect clients on the same network, replace `localhost` with the server's IP:

```bash
# On server machine, find IP:
hostname -I

# On client machine:
python3 chat_client.py --host 192.168.1.100
```

### Port Customization:

Change port on both server and all clients:

```bash
# Server
python3 chat_server.py  # Edit code to change default port

# Client
python3 chat_client.py --port 8000
```

## Troubleshooting

### "Connection refused" error
- ❌ Server is not running
- ✅ **Solution:** Start the server first

### "Address already in use" error
- ❌ Port 5000 is already in use
- ✅ **Solution:** Use different port: `python3 chat_server.py` (modify code)

### Messages not appearing
- ❌ Network connectivity issue
- ✅ **Solution:** Check if server and clients are on same network

### Client hangs on username prompt
- ❌ Connection timeout
- ✅ **Solution:** Check server is running and accessible

## Performance Notes

- **Max clients:** Limited by OS file descriptors (typically 1000+)
- **Message size:** Limited to 1024 bytes per message
- **Latency:** <100ms on local network

## Code Structure

```
chat_system/
├── chat_server.py       # Server implementation
├── chat_client.py       # Client implementation
└── README.md           # This file
```

## Security Considerations

⚠️ **Warning:** This is a demonstration system. Not suitable for production use:

- No encryption (messages sent in plaintext)
- No authentication
- No input validation
- No rate limiting

For secure communication, consider:
- Adding TLS/SSL encryption
- Implementing user authentication
- Validating and sanitizing inputs
- Adding rate limiting

## Future Enhancements

- 🔐 SSL/TLS encryption
- 👤 User authentication & passwords
- 💾 Message history/logging
- 🎨 Customizable colors and themes
- 📁 File sharing
- 🔊 Sound notifications
- 🌍 Unicode emoji support improvements
- 📱 Mobile client

## License

Free to use and modify for personal/educational purposes.

## Support

Having issues? Check:

1. Is Python 3.6+ installed? `python3 --version`
2. Is the server running?
3. Are both on the same network?
4. Are you using the same port?
5. Check firewall settings

## Author

Created as a demonstration of socket programming in Python.

---

**Happy chatting!** 🚀💬