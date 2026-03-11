#!/usr/bin/env python3
"""
Terminal Chat System - Environment Setup & Auto-Installer
==========================================================
Checks system, installs dependencies, detects CGNAT,
sets up ngrok tunnel, and configures everything automatically.

Run this FIRST before starting the server!
"""

import os
import sys
import platform
import subprocess
import socket
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


class Colors:
    HEADER    = '\033[95m'
    BLUE      = '\033[94m'
    CYAN      = '\033[96m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    RED       = '\033[91m'
    BOLD      = '\033[1m'
    END       = '\033[0m'


def banner():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  🔐  ANONYMCHAT — ENVIRONMENT SETUP & AUTO-INSTALLER  🔐  ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"{Colors.END}")


def section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 68}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  ▶  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 68}{Colors.END}\n")


def ok(msg):    print(f"{Colors.GREEN}  ✅  {msg}{Colors.END}")
def fail(msg):  print(f"{Colors.RED}  ❌  {msg}{Colors.END}")
def warn(msg):  print(f"{Colors.YELLOW}  ⚠️   {msg}{Colors.END}")
def info(msg):  print(f"{Colors.CYAN}  ℹ️   {msg}{Colors.END}")
def step(msg):  print(f"{Colors.BOLD}  →   {msg}{Colors.END}")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd, timeout=30):
    """Run a shell command silently, return (success, output)"""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def pip_install(package, label=None):
    """Install a pip package, return True on success"""
    label = label or package
    print(f"  ⏳  Installing {label}...", end=" ", flush=True)
    success, out = run([sys.executable, "-m", "pip", "install",
                        package, "--break-system-packages", "-q"])
    if not success:
        # fallback: user mode
        success, out = run([sys.executable, "-m", "pip", "install",
                            package, "--user", "-q"])
    if success:
        print(f"{Colors.GREEN}done{Colors.END}")
    else:
        print(f"{Colors.RED}failed{Colors.END}")
        info(out[:200] if out else "No details")
    return success


def fetch_url(url, timeout=6):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode().strip()
    except:
        return None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_public_ip():
    for url in ["https://api.ipify.org",
                "https://checkip.amazonaws.com",
                "https://icanhazip.com"]:
        ip = fetch_url(url)
        if ip:
            return ip
    return None


def is_cgnat(public_ip):
    """
    Returns True if the ISP uses CGNAT (Carrier-Grade NAT).
    CGNAT IPs are in the 100.64.0.0/10 range (RFC 6598).
    Jio almost always uses CGNAT. Many Airtel connections do too.
    When CGNAT is active, port forwarding is impossible.
    """
    if not public_ip:
        return True
    if public_ip.startswith("100."):
        try:
            second = int(public_ip.split(".")[1])
            if 64 <= second <= 127:
                return True
        except:
            pass
    return False


def check_port_open(port, timeout=3):
    """Check if a local port is already in use"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — SYSTEM INFO
# ─────────────────────────────────────────────────────────────────────────────

def check_system():
    section("System Information")
    print(f"  OS          : {platform.system()} {platform.release()}")
    print(f"  Platform    : {platform.machine()}")
    print(f"  Python      : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"  Time        : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if sys.version_info < (3, 6):
        fail("Python 3.6+ is required. Please upgrade Python.")
        sys.exit(1)
    else:
        ok(f"Python {sys.version_info.major}.{sys.version_info.minor} — OK")

    # Check pip
    success, out = run([sys.executable, "-m", "pip", "--version"])
    if success:
        ok("pip is available")
    else:
        fail("pip not found — install pip first")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — INTERNET & CGNAT DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def check_network():
    section("Network & ISP Detection")

    # Internet connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        ok("Internet connection — active")
        has_internet = True
    except:
        warn("No internet connection detected")
        has_internet = False

    local_ip  = get_local_ip()
    public_ip = get_public_ip()

    print(f"\n  Local IP   (LAN / WiFi)  : {local_ip}")
    print(f"  Public IP  (internet)    : {public_ip or 'Could not fetch'}")

    cgnat = is_cgnat(public_ip)

    if cgnat:
        warn("CGNAT detected — your ISP (likely Jio/Airtel) shares")
        print(f"        your public IP with many users.")
        print(f"        ➜  Port forwarding will NOT work on this connection.")
        print(f"        ➜  ngrok will be set up automatically to bypass this.")
    else:
        ok("Direct public IP detected — port forwarding is possible")
        print(f"\n  To allow friends to connect over internet:")
        print(f"    1. Open your router at http://192.168.1.1")
        print(f"    2. Add port forwarding rule:")
        print(f"       External Port : 5000")
        print(f"       Internal IP   : {local_ip}")
        print(f"       Internal Port : 5000")
        print(f"       Protocol      : TCP")
        print(f"    3. Share Public IP {public_ip} and Room Code with friend")

    return has_internet, cgnat, local_ip, public_ip


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — INSTALL CORE DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────

def install_core():
    section("Core Dependencies")

    # pyngrok — needed for CGNAT bypass
    try:
        from pyngrok import ngrok
        ok("pyngrok already installed")
    except ImportError:
        warn("pyngrok not installed — installing now...")
        if pip_install("pyngrok", "pyngrok (ngrok tunnel)"):
            ok("pyngrok installed successfully")
        else:
            fail("Could not install pyngrok — ngrok tunnel will not work")

    # PySocks — needed for Tor mode
    try:
        import socks
        ok("PySocks already installed")
    except ImportError:
        warn("PySocks not installed (needed for Tor mode) — installing...")
        if pip_install("PySocks", "PySocks (Tor proxy)"):
            ok("PySocks installed successfully")
        else:
            warn("PySocks install failed — Tor mode won't work (chat still works)")

    # stem — needed for Tor hidden services
    try:
        from stem.control import Controller
        ok("stem already installed")
    except ImportError:
        warn("stem not installed (needed for Tor hidden services) — installing...")
        if pip_install("stem", "stem (Tor hidden services)"):
            ok("stem installed successfully")
        else:
            warn("stem install failed — Tor hidden services won't work (chat still works)")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — NGROK SETUP (auto-bypass for CGNAT)
# ─────────────────────────────────────────────────────────────────────────────

def setup_ngrok(cgnat: bool):
    section("ngrok Tunnel Setup (Internet Bypass)")

    try:
        from pyngrok import ngrok, conf
    except ImportError:
        fail("pyngrok is not installed — skipping ngrok setup")
        return False

    # ── Auth token ────────────────────────────────────────────────────────────
    # Check if a token is already saved
    config_path = Path.home() / ".config" / "ngrok" / "ngrok.yml"
    alt_config   = Path.home() / ".ngrok2" / "ngrok.yml"

    token_saved = config_path.exists() or alt_config.exists()

    if token_saved:
        ok("ngrok auth token already configured")
    else:
        print(f"\n  ngrok requires a free account to create tunnels.")
        print(f"\n  {'─' * 60}")
        print(f"  HOW TO GET YOUR FREE ngrok AUTH TOKEN:")
        print(f"  {'─' * 60}")
        print(f"  1. Open  https://dashboard.ngrok.com/signup  in your browser")
        print(f"  2. Sign up for free (Google/GitHub login works)")
        print(f"  3. After login go to:  https://dashboard.ngrok.com/get-started/your-authtoken")
        print(f"  4. Copy the token (looks like: 2abc...xyz_...)")
        print(f"  {'─' * 60}\n")

        try:
            token = input(f"  Paste your ngrok auth token here (or press Enter to skip): ").strip()
        except (KeyboardInterrupt, EOFError):
            token = ""

        if token:
            success, out = run([sys.executable, "-m", "pyngrok", "authtoken", token])
            if not success:
                # Try via pyngrok API directly
                try:
                    conf.get_default().auth_token = token
                    ngrok.set_auth_token(token)
                    ok("ngrok auth token saved")
                    token_saved = True
                except Exception as e:
                    warn(f"Could not save token automatically: {e}")
                    info("Run manually:  ngrok authtoken <your_token>")
            else:
                ok("ngrok auth token saved successfully")
                token_saved = True
        else:
            warn("Skipped ngrok auth token — tunnels may not work without it")
            info("You can add it later by running this script again")

    # ── Test tunnel ───────────────────────────────────────────────────────────
    print()
    if cgnat:
        info("CGNAT detected — testing ngrok tunnel on port 5000...")
    else:
        info("Testing ngrok tunnel (useful even without CGNAT as a backup)...")

    try:
        from pyngrok import ngrok as ng
        # Kill any existing tunnels first
        try:
            ng.kill()
            time.sleep(1)
        except:
            pass

        print("  ⏳  Opening test tunnel...", end=" ", flush=True)
        tunnel = ng.connect(5000, "tcp")
        url    = tunnel.public_url.replace("tcp://", "")
        host, port = url.rsplit(":", 1)
        print(f"{Colors.GREEN}success{Colors.END}\n")

        ok("ngrok tunnel is working!")
        print(f"\n  {'═' * 60}")
        print(f"  📌  SHARE THESE WITH YOUR FRIEND:")
        print(f"  {'═' * 60}")
        print(f"  Server IP   →  {Colors.BOLD}{host}{Colors.END}")
        print(f"  Port        →  {Colors.BOLD}{port}{Colors.END}")
        print(f"  {'═' * 60}")
        print(f"\n  ⚠️  This test tunnel will close when this script exits.")
        print(f"      When you start chat-server.py, it will open a new")
        print(f"      tunnel automatically and show fresh IP + Port.\n")

        # Close the test tunnel
        ng.disconnect(tunnel.public_url)
        ng.kill()
        return True

    except Exception as e:
        fail(f"ngrok tunnel test failed: {e}")

        if "authentication" in str(e).lower() or "authtoken" in str(e).lower() or "auth" in str(e).lower():
            warn("Your ngrok auth token is missing or invalid.")
            print(f"\n  Fix:")
            print(f"  1. Go to https://dashboard.ngrok.com/get-started/your-authtoken")
            print(f"  2. Copy your token")
            print(f"  3. Run:  python3 enviorment-check.py  again and paste it")
        elif "limit" in str(e).lower():
            warn("You have reached the ngrok free tier tunnel limit.")
            info("Close other ngrok sessions or wait a few minutes and try again.")
        else:
            info(f"Details: {e}")

        return False


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — TOR CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_tor():
    section("Tor Setup (Optional — for Anonymous Chat)")

    info("Tor is optional. The chat works fine without it.")
    info("Use Tor only if you need privacy/anonymity.\n")

    # Tor binary
    success, out = run(["tor", "--version"], timeout=5)
    if success:
        version = out.split("\n")[0]
        ok(f"Tor binary installed: {version}")
        tor_running = check_port_open(9050)
        if tor_running:
            ok("Tor SOCKS proxy is running on port 9050")
        else:
            warn("Tor installed but not running")
            info("Start it with:  tor --SocksPort 9050")
    else:
        warn("Tor binary not found")
        print(f"\n  Install Tor (optional):")
        print(f"    Linux  :  sudo apt install tor")
        print(f"    macOS  :  brew install tor")
        print(f"    Windows:  https://www.torproject.org/download/tor/")
        print(f"    Android:  Install 'Orbot' from Play Store / F-Droid")
        print(f"              (NOT Tor Browser — that won't work)\n")

    # PySocks
    try:
        import socks
        ok("PySocks installed — Tor mode supported")
    except ImportError:
        warn("PySocks not available — Tor mode (--tor flag) won't work")

    # stem
    try:
        from stem.control import Controller
        ok("stem installed — Tor hidden services supported")
    except ImportError:
        warn("stem not available — Tor hidden services won't work")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — VERIFY CHAT FILES
# ─────────────────────────────────────────────────────────────────────────────

def check_chat_files():
    section("Chat Application Files")

    files = {
        "chat-server.py"     : "Server  (run this to host)",
        "chat-cilent.py"     : "Client  (run this to join)",
        "test-chat.py"       : "Tests   (run to verify)",
        "enviorment-check.py": "This setup script",
        "README.md"          : "Documentation",
    }

    all_found = True
    for filename, desc in files.items():
        if Path(filename).exists():
            ok(f"{filename:25s}  —  {desc}")
        else:
            warn(f"{filename:25s}  —  NOT FOUND")
            all_found = False

    if not all_found:
        info("Missing files won't break setup but make sure you have the main server/client files.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — FINAL SUMMARY & QUICK START
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(cgnat: bool, ngrok_ok: bool):
    section("Setup Complete — Quick Start Guide")

    if cgnat and ngrok_ok:
        print(f"  {Colors.GREEN}{Colors.BOLD}✅  Your system is ready! (ngrok will handle internet access){Colors.END}\n")
        print(f"  HOW TO START CHATTING WITH YOUR FRIEND:\n")
        print(f"  {Colors.BOLD}Step 1{Colors.END}  — Start the server (your machine):")
        print(f"           python3 chat-server.py\n")
        print(f"           The server will print a ROOM CODE and ngrok IP + Port.")
        print(f"           Share those 3 things with your friend.\n")
        print(f"  {Colors.BOLD}Step 2{Colors.END}  — Your friend runs (their machine):")
        print(f"           python3 chat-cilent.py\n")
        print(f"           They enter the ngrok IP, Port, Room Code, and username.\n")
        print(f"  {Colors.BOLD}Step 3{Colors.END}  — You also connect as a client (new terminal):")
        print(f"           python3 chat-cilent.py")
        print(f"           Enter 127.0.0.1 as the IP (since you are the server)\n")

    elif not cgnat and ngrok_ok:
        print(f"  {Colors.GREEN}{Colors.BOLD}✅  Your system is ready! (direct public IP + ngrok available){Colors.END}\n")
        print(f"  You have a proper public IP — you can use port forwarding OR ngrok.\n")
        print(f"  Easiest option — just run the server and use ngrok:")
        print(f"           python3 chat-server.py\n")

    elif cgnat and not ngrok_ok:
        print(f"  {Colors.YELLOW}{Colors.BOLD}⚠️   Partial setup — ngrok is not working yet{Colors.END}\n")
        print(f"  Your ISP uses CGNAT so port forwarding won't work.")
        print(f"  You need to fix the ngrok auth token to connect over internet.\n")
        print(f"  Fix:")
        print(f"  1. Go to https://dashboard.ngrok.com/get-started/your-authtoken")
        print(f"  2. Copy your token")
        print(f"  3. Run:  python3 enviorment-check.py  again")
        print(f"\n  Local chat (same WiFi) still works without ngrok:")
        print(f"           python3 chat-server.py")

    else:
        print(f"  {Colors.GREEN}{Colors.BOLD}✅  Your system is ready!{Colors.END}\n")
        print(f"  Run:  python3 chat-server.py")

    print(f"\n  {'─' * 60}")
    print(f"  Optional Tor mode (for anonymous chat):")
    print(f"    Server :  python3 chat-server.py --tor")
    print(f"    Client :  python3 chat-cilent.py --tor")
    print(f"    (Requires Tor/Orbot running on port 9050 first)")
    print(f"  {'─' * 60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    banner()

    # Step 1 — System
    check_system()

    # Step 2 — Network
    has_internet, cgnat, local_ip, public_ip = check_network()

    if not has_internet:
        warn("No internet — skipping package installs and ngrok setup")
        warn("Connect to the internet and run this script again")
        sys.exit(1)

    # Step 3 — Install packages
    install_core()

    # Step 4 — ngrok
    ngrok_ok = setup_ngrok(cgnat)

    # Step 5 — Tor (informational only)
    check_tor()

    # Step 6 — Files
    check_chat_files()

    # Step 7 — Summary
    print_summary(cgnat, ngrok_ok)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}  Setup interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}  Unexpected error: {e}{Colors.END}\n")
        sys.exit(1)