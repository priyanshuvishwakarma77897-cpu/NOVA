
import asyncio
import shutil
import textwrap

from backend.app.core.config import settings
from backend.app.services.ai.orchestrator import generate_ai_response


# ─────────────────────────────────────────────
# Terminal styling
# ─────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
WHITE = "\033[97m"


def terminal_width():
    return max(50, min(shutil.get_terminal_size().columns, 90))


def line(char="─"):
    print(f"{DIM}{char * terminal_width()}{RESET}")


def print_message(label, message, color):
    width = terminal_width()
    prefix = f"  {color}{BOLD}{label}{RESET} "

    available_width = max(20, width - 14)

    wrapped = textwrap.fill(
        str(message),
        width=available_width,
        subsequent_indent=" " * 11,
    )

    print(f"\n{prefix}{wrapped}\n")


# ─────────────────────────────────────────────
# NOVA interface
# ─────────────────────────────────────────────

def show_header():
    width = terminal_width()
    inner_width = width - 4

    print()
    print(f"{CYAN}{'╭' + '─' * inner_width + '╮'}{RESET}")
    print(f"{CYAN}│{' ' * inner_width}│{RESET}")
    print(
        f"{CYAN}│{RESET}"
        f"{BOLD}{WHITE}{'✦ N O V A'.center(inner_width)}{RESET}"
        f"{CYAN}│{RESET}"
    )
    print(
        f"{CYAN}│{RESET}"
        f"{DIM}{'PERSONAL AI ASSISTANT'.center(inner_width)}{RESET}"
        f"{CYAN}│{RESET}"
    )
    print(f"{CYAN}│{' ' * inner_width}│{RESET}")
    print(
        f"{CYAN}│{RESET}"
        f"{GREEN}{'● SYSTEM ONLINE'.center(inner_width)}{RESET}"
        f"{CYAN}│{RESET}"
    )
    print(f"{CYAN}│{' ' * inner_width}│{RESET}")
    print(f"{CYAN}{'╰' + '─' * inner_width + '╯'}{RESET}")

    print()
    print(f"  {DIM}Provider   {RESET}{settings.AI_PROVIDER}")

    if settings.AI_PROVIDER.lower() == "groq":
        print(f"  {DIM}Model      {RESET}{settings.GROQ_MODEL}")

    print(f"  {DIM}Interface  {RESET}Terminal")
    print()

    line()
    print()
    print(f"  {WHITE}Hello! I'm NOVA. It's good to have you here.{RESET}")
    print(f"  {DIM}I'm ready whenever you are.{RESET}")
    print()
    print(f"  {DIM}Commands: exit / quit{RESET}")
    print()
    line()


def show_thinking():
    print(f"\n  {YELLOW}◌ NOVA is thinking...{RESET}\n")


def show_error(message):
    print(f"\n  {RED}{BOLD}● REQUEST STOPPED{RESET}")
    print(f"  {RED}{message}{RESET}")
    print(f"  {DIM}No automatic retry was attempted.{RESET}\n")


# ─────────────────────────────────────────────
# Conversation
# ─────────────────────────────────────────────

async def main():
    show_header()

    while True:
        try:
            user_message = input(
                f"\n  {CYAN}{BOLD}YOU{RESET} {DIM}›{RESET} "
            ).strip()

            if not user_message:
                continue

            if user_message.lower() in {"exit", "quit"}:
                print()
                line()
                print(
                    f"\n  {GREEN}NOVA: Goodbye! "
                    f"See you next time. ✦{RESET}\n"
                )
                line()
                break

            show_thinking()

            response = await generate_ai_response(user_message)

            print_message(
                "NOVA ›",
                response["content"],
                GREEN,
            )

        except KeyboardInterrupt:
            print(
                f"\n\n  {YELLOW}Session interrupted. "
                f"Goodbye!{RESET}\n"
            )
            break

        except Exception as exc:
            show_error(str(exc))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}NOVA session closed.{RESET}\n")
