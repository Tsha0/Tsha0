import datetime
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent

TILE = 52
GAP = 6
COLORS = {"g": "#2ea043", "y": "#d29922", "x": "#30363d", "empty": "#161b22"}


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def answer_for(date):
    words = (HERE / "answers.txt").read_text().split()
    n = int(hashlib.sha256(f"tsha0-wordle-{date}".encode()).hexdigest(), 16)
    return words[n % len(words)]


def score(guess, answer):
    result = ["x"] * 5
    remaining = list(answer)
    for i, c in enumerate(guess):
        if answer[i] == c:
            result[i] = "g"
            remaining.remove(c)
    for i, c in enumerate(guess):
        if result[i] == "x" and c in remaining:
            result[i] = "y"
            remaining.remove(c)
    return "".join(result)


def render(state):
    w = 5 * TILE + 4 * GAP
    h = 6 * TILE + 5 * GAP
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w+24}" height="{h+24}" viewBox="0 0 {w+24} {h+24}">',
        f'<rect width="{w+24}" height="{h+24}" fill="#0d1117"/>',
    ]
    for row in range(6):
        guess = state["guesses"][row] if row < len(state["guesses"]) else None
        for col in range(5):
            x = 12 + col * (TILE + GAP)
            y = 12 + row * (TILE + GAP)
            fill = COLORS[guess["score"][col]] if guess else COLORS["empty"]
            parts.append(f'<rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="4" fill="{fill}"/>')
            if guess:
                parts.append(
                    f'<text x="{x + TILE/2}" y="{y + TILE/2 + 8}" text-anchor="middle" '
                    f'font-family="ui-monospace,Menlo,monospace" font-size="26" font-weight="bold" '
                    f'fill="#e6edf3">{guess["word"][col].upper()}</text>'
                )
    parts.append("</svg>")
    (HERE / "board.svg").write_text("\n".join(parts))


def update_status(state):
    readme = HERE.parent / "README.md"
    text = readme.read_text()
    used = len(state["guesses"])
    if state["solved"]:
        by = state["guesses"][-1]["by"]
        line = f"Today's puzzle: solved in {used}/6 by [@{by}](https://github.com/{by}). New word at 00:00 UTC."
    elif used >= 6:
        line = f"Today's puzzle: out of guesses — the word was `{state['answer'].upper()}`. New word at 00:00 UTC."
    elif used == 0:
        line = "Today's puzzle: no guesses yet."
    else:
        by = state["guesses"][-1]["by"]
        line = f"Today's puzzle: {used}/6 guesses used — last guess by [@{by}](https://github.com/{by})."
    text = re.sub(
        r"<!-- wordle-status -->.*?<!-- /wordle-status -->",
        f"<!-- wordle-status -->\n{line}\n<!-- /wordle-status -->",
        text,
        flags=re.S,
    )
    readme.write_text(text)


def pretty(word, sc):
    marks = {"g": "G", "y": "y", "x": "."}
    top = " ".join(word.upper())
    bottom = " ".join(marks[c] for c in sc)
    return f"```\n{top}\n{bottom}\n```\nG = right letter, right spot. y = right letter, wrong spot."


def main():
    title, author = sys.argv[1], sys.argv[2]
    date = today()
    state = json.loads((HERE / "state.json").read_text())
    if state.get("date") != date:
        state = {"date": date, "answer": answer_for(date), "guesses": [], "solved": False}

    m = re.fullmatch(r"wordle\|([a-zA-Z]{5})", title.strip())
    if not m:
        print("Couldn't parse that. Use the title format `wordle|guess` with a five-letter word, e.g. `wordle|crane`.")
        sys.exit(1)
    word = m.group(1).lower()

    if state["solved"]:
        print("Today's word was already solved — come back after 00:00 UTC for a new puzzle.")
        sys.exit(1)
    if len(state["guesses"]) >= 6:
        print("All six guesses are used up for today — a new puzzle starts at 00:00 UTC.")
        sys.exit(1)

    answers = set((HERE / "answers.txt").read_text().split())
    allowed = set((HERE / "allowed.txt").read_text().split())
    if word not in answers and word not in allowed:
        print(f"`{word.upper()}` isn't in the word list. Try another five-letter word.")
        sys.exit(1)
    if word in [g["word"] for g in state["guesses"]]:
        print(f"`{word.upper()}` was already guessed today. Check the board and try another word.")
        sys.exit(1)

    sc = score(word, state["answer"])
    state["guesses"].append({"word": word, "score": sc, "by": author})
    if sc == "ggggg":
        state["solved"] = True

    (HERE / "state.json").write_text(json.dumps(state, indent=1))
    render(state)
    update_status(state)

    used = len(state["guesses"])
    if state["solved"]:
        print(f"{pretty(word, sc)}\n\nThat's it! You solved today's word in {used}/6. Nice one, @{author}.")
    elif used >= 6:
        print(f"{pretty(word, sc)}\n\nThat was the last guess — the word was `{state['answer'].upper()}`. New puzzle at 00:00 UTC.")
    else:
        print(f"{pretty(word, sc)}\n\n{6 - used} guesses left today. Thanks for playing, @{author}!")


if __name__ == "__main__":
    main()
