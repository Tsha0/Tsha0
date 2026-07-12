import json
import pathlib
import re
import sys

import render

HERE = pathlib.Path(__file__).parent


def main():
    title, author = sys.argv[1], sys.argv[2]
    state = json.loads((HERE / "state.json").read_text())
    w, h = state["width"], state["height"]

    m = re.fullmatch(r"place\|(\d{1,3})\|(\d{1,3})\|(#[0-9a-fA-F]{6})", title.strip())
    if not m:
        print(f"Couldn't parse that. Use the title format `place|x|y|#RRGGBB`, e.g. `place|12|5|#ff4757` (x 0-{w-1}, y 0-{h-1}).")
        sys.exit(1)
    x, y, color = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if x >= w or y >= h:
        print(f"({x}, {y}) is off the canvas. x must be 0-{w-1} and y must be 0-{h-1}.")
        sys.exit(1)

    state["pixels"][f"{x},{y}"] = color
    state["log"] = ([{"x": x, "y": y, "color": color, "by": author}] + state.get("log", []))[:50]
    (HERE / "state.json").write_text(json.dumps(state, indent=1))
    render.render()

    readme = HERE.parent / "README.md"
    text = readme.read_text()
    latest = f"<!-- canvas-latest -->\nLatest pixel: ({x}, {y}) painted {color} by [@{author}](https://github.com/{author})\n<!-- /canvas-latest -->"
    text = re.sub(r"<!-- canvas-latest -->.*?<!-- /canvas-latest -->", latest, text, flags=re.S)
    readme.write_text(text)

    print(f"Painted ({x}, {y}) {color}. Thanks for contributing, @{author}! The canvas updates in about a minute.")


if __name__ == "__main__":
    main()
