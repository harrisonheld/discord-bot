import requests
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion


BASE = "http://127.0.0.1:8000"


state = {
    "guilds": {},  # {id: name}
    "channels": [],  # [(id, name)]

    "selected_guild": None,
    "selected_guild_name": None,

    "selected_channel": None,
    "selected_channel_name": None,
}


# -----------------------
# Fetch
# -----------------------
def fetch_guilds():
    r = requests.get(f"{BASE}/guilds")
    r.raise_for_status()
    state["guilds"] = r.json()


def fetch_channels(guild_id):
    r = requests.get(f"{BASE}/channels/{guild_id}")
    r.raise_for_status()
    state["channels"] = r.json()


def fetch_users(guild_id):
    r = requests.get(f"{BASE}/users/{guild_id}")
    r.raise_for_status()
    return r.json()


# -----------------------
# Resolution helpers
# -----------------------
def resolve_guild(arg):
    if arg is None:
        return None

    # index
    if arg.isdigit():
        return list(state["guilds"].items())[int(arg)]

    # name
    for gid, name in state["guilds"].items():
        if name.lower() == arg.lower():
            return gid, name

    return None


def resolve_channel(arg):
    if arg is None:
        return None

    # index
    if arg.isdigit():
        return state["channels"][int(arg)]

    # name
    for cid, name in state["channels"]:
        if name.lower() == arg.lower():
            return cid, name

    return None


# -----------------------
# Selection
# -----------------------
def set_server(arg):
    res = resolve_guild(arg)
    if not res:
        print("guild not found")
        return

    gid, name = res

    state["selected_guild"] = gid
    state["selected_guild_name"] = name

    fetch_channels(gid)

    state["selected_channel"] = None
    state["selected_channel_name"] = None

    print(f"Selected server: {name}")


def set_channel(arg):
    if not state["selected_guild"]:
        print("select server first")
        return

    res = resolve_channel(arg)
    if not res:
        print("channel not found")
        return

    cid, name = res

    state["selected_channel"] = cid
    state["selected_channel_name"] = name

    print(f"Selected channel: #{name}")


# -----------------------
# Display
# -----------------------
def print_servers():
    if not state["guilds"]:
        fetch_guilds()

    print("\nServers:")
    for i, (gid, name) in enumerate(state["guilds"].items()):
        print(f"  {i}: {name} ({gid})")


def print_channels():
    if not state["selected_guild"]:
        print("select server first")
        return

    print("\nChannels:")
    for i, (cid, name) in enumerate(state["channels"]):
        print(f"  {i}: #{name} ({cid})")


def print_users():
    if not state["selected_guild"]:
        print("select server first")
        return

    users = fetch_users(state["selected_guild"])
    print("\nUsers:")
    for uid, name in users:
        print(f"  {name} ({uid})")


# -----------------------
# Messaging
# -----------------------
def send_message(msg):
    if not state["selected_guild"] or not state["selected_channel"]:
        print("select server + channel first")
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
# Help
# -----------------------
def help_menu():
    print("""
Commands:

Navigation:
  servers
  channels
  users

Selection:
  server <name|index>
  channel <name|index>

Messaging:
  send <msg>

System:
  whoami
  refresh
  help
  exit
""")


def whoami():
    print("\nCurrent state:")
    print(f"  Guild:   {state['selected_guild_name']}")
    print(f"  Channel: {state['selected_channel_name']}")


def refresh():
    fetch_guilds()
    if state["selected_guild"]:
        fetch_channels(state["selected_guild"])
    print("refreshed.")


# -----------------------
# Completion
# -----------------------
class DiscordCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        commands = [
            "servers",
            "channels",
            "users",
            "send",
            "server",
            "channel",
            "whoami",
            "refresh",
            "help",
            "exit",
        ]

        # command completion
        if " " not in text:
            for cmd in commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return

        cmd, partial = text.split(" ", 1)

        if cmd == "server":
            for name in state["guilds"].values():
                if partial.lower() in name.lower():
                    yield Completion(name, start_position=-len(partial))

        elif cmd == "channel":
            for _, name in state["channels"]:
                if partial.lower() in name.lower():
                    yield Completion(name, start_position=-len(partial))


# -----------------------
# Prompt
# -----------------------
def prompt():
    g = state["selected_guild_name"] or "-"
    c = state["selected_channel_name"] or "-"
    return f"[{g} / #{c}] > "


# -----------------------
# Main loop
# -----------------------
def main():
    fetch_guilds()

    session = PromptSession(completer=DiscordCompleter())

    print("CLI ready. type 'help'.")

    while True:
        try:
            raw = session.prompt(prompt()).strip()
            if not raw:
                continue

            parts = raw.split(" ", 1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else None

            if cmd == "help":
                help_menu()

            elif cmd == "servers":
                print_servers()

            elif cmd == "channels":
                print_channels()

            elif cmd == "users":
                print_users()

            elif cmd == "server":
                set_server(arg)

            elif cmd == "channel":
                set_channel(arg)

            elif cmd == "send":
                send_message(arg)

            elif cmd == "whoami":
                whoami()

            elif cmd == "refresh":
                refresh()

            elif cmd == "exit":
                sys.exit(0)

            else:
                print("unknown command")

        except KeyboardInterrupt:
            print()
        except Exception as e:
            print("error:", e)


if __name__ == "__main__":
    main()