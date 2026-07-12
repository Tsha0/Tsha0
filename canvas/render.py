import json
import pathlib

CELL = 16
HERE = pathlib.Path(__file__).parent


def render():
    state = json.loads((HERE / "state.json").read_text())
    w, h = state["width"], state["height"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*CELL}" height="{h*CELL}" '
        f'viewBox="0 0 {w*CELL} {h*CELL}">',
        f'<rect width="{w*CELL}" height="{h*CELL}" fill="#0d1117"/>',
    ]
    for x in range(1, w):
        parts.append(f'<line x1="{x*CELL}" y1="0" x2="{x*CELL}" y2="{h*CELL}" stroke="#21262d" stroke-width="1"/>')
    for y in range(1, h):
        parts.append(f'<line x1="0" y1="{y*CELL}" x2="{w*CELL}" y2="{y*CELL}" stroke="#21262d" stroke-width="1"/>')
    for key, color in state["pixels"].items():
        x, y = map(int, key.split(","))
        parts.append(f'<rect x="{x*CELL+1}" y="{y*CELL+1}" width="{CELL-2}" height="{CELL-2}" rx="2" fill="{color}"/>')
    parts.append("</svg>")
    (HERE / "canvas.svg").write_text("\n".join(parts))


if __name__ == "__main__":
    render()
