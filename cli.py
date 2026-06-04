import requests
import sys

BASE = "http://127.0.0.1:8000"


state = {
    "guilds": {},
    "channels": [],
    "selected_guild": None,
    "selected_channel": None,
}


# -----------------------
# Helpers
# -----------------------
def fetch_guilds():
    r = requests.get(f"{BASE}/guilds")
    r.raise_for_status()
    state["guilds"] = r.json()


def fetch_channels(guild_id):
    r = requests.get(f"{BASE}/channels/{guild_id}")
    r.raise_for_status()
    state["channels"] = r.json()


def print_servers():
    if not state["guilds"]:
        fetch_guilds()

    print("\nServers:")
    for i, (gid, name) in enumerate(state["guilds"].items()):
        print(f"  {i}: {name} ({gid})")


def select_server(index):
    try:
        gid = list(state["guilds"].keys())[int(index)]
        state["selected_guild"] = gid
        fetch_channels(gid)
        state["selected_channel"] = None
        print(f"Selected server: {state['guilds'][gid]}")
    except Exception:
        print("Invalid server index")


def print_channels():
    if not state["selected_guild"]:
        print("No server selected. Use: servers + use <index>")
        return

    print("\nChannels:")
    for i, (cid, name) in enumerate(state["channels"]):
        print(f"  {i}: #{name} ({cid})")


def select_channel(index):
    try:
        cid, name = state["channels"][int(index)]
        state["selected_channel"] = cid
        print(f"Selected channel: #{name}")
    except Exception:
        print("Invalid channel index")


def send_message(msg):
    if not state["selected_guild"] or not state["selected_channel"]:
        print("Select server and channel first.")
        return

    payload = {
        "guild_id": int(state["selected_guild"]),
        "channel_id": int(state["selected_channel"]),
        "message": msg,
    }

    r = requests.post(f"{BASE}/send", json=payload)
    if r.ok:
        print("sent.")
    else:
        print("failed:", r.text)


# -----------------------
# Help system
# -----------------------
def help_text(cmd=None):
    if not cmd:
        print("""
Available commands:

Navigation:
  servers                List servers
  use <index>           Select server
  channels              List channels in selected server
  usec <index>          Select channel

Messaging:
  send <msg>            Send message to selected channel
  say <msg>             Alias for send

System:
  whoami                Show current selection
  refresh               Reload server data
  help                  Show this help
  exit                  Quit CLI
""")
        return

    docs = {
        "send": "send <message>\nSends a message to the selected Discord channel.",
        "use": "use <index>\nSelects a server from the servers list.",
        "usec": "usec <index>\nSelects a channel from the channel list.",
        "servers": "servers\nLists all servers the bot is in.",
        "channels": "channels\nLists channels in the selected server.",
        "whoami": "whoami\nShows current selected server/channel.",
    }

    print(docs.get(cmd, "No help available for that command."))


# -----------------------
# Status
# -----------------------
def whoami():
    guild = state["guilds"].get(state["selected_guild"])
    channel = None

    if state["selected_channel"]:
        channel = state["selected_channel"]

    print("\nCurrent state:")
    print(f"  Server:  {guild}")
    print(f"  Channel: {channel}")


def refresh():
    fetch_guilds()
    if state["selected_guild"]:
        fetch_channels(state["selected_guild"])
    print("refreshed.")


# -----------------------
# Main loop
# -----------------------
def main():
    fetch_guilds()

    print("CLI ready. Type 'help'.")

    while True:
        try:
            raw = input("> ").strip()
            if not raw:
                continue

            parts = raw.split(" ", 1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else None

            if cmd == "help":
                help_text(arg)

            elif cmd == "servers":
                print_servers()

            elif cmd == "use":
                if arg is None:
                    print("usage: use <index>")
                else:
                    select_server(arg)

            elif cmd == "channels":
                print_channels()

            elif cmd == "usec":
                if arg is None:
                    print("usage: usec <index>")
                else:
                    select_channel(arg)

            elif cmd in ("send", "say"):
                if arg is None:
                    print("usage: send <message>")
                else:
                    send_message(arg)

            elif cmd == "whoami":
                whoami()

            elif cmd == "refresh":
                refresh()

            elif cmd == "exit":
                sys.exit(0)

            else:
                print("Unknown command. Type 'help'.")

        except KeyboardInterrupt:
            print("\nexit")
            break
        except Exception as e:
            print("error:", e)


if __name__ == "__main__":
    main()
