from functools import cache
from json import load
from typing import Literal, Optional, TypedDict
from os import remove, walk
from os.path import dirname, abspath, join as path_join
from sys import argv as args

CardTypes = Literal["king", "queen", "bishop", "knight", "rook", "pawn", "action"]


class CardJSON(TypedDict):
    name: str
    type: CardTypes
    cost: int
    life: int
    effects: Optional[str]
    attack: str
    defence: str


SVG_CSS = r"""
        rect {
            fill: white;
            stroke: black;
            stroke-width: 0.75;
            stroke-linejoin: round;
            stroke-linecap: round;
        }
        
        path {
            fill: none;
            stroke: black;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        
        path.fill {
            fill: black;
        }
        
        text {
            font-family: sans-serif;
            dominant-baseline: central;
        }
        
        text.title {
            font-size: 2px;
            text-anchor: middle;
        }
        
        text.cost {
            font-size: 1px;
            text-anchor: end;
        }

        text.effect {
            font-size: 1px;
            text-anchor: start;
            dominant-baseline: hanging;
        }
        
        text.label {
            font-size: 1px;
            text-anchor: start;
        }
        
        text.dice {
            font-size: 2px;
            text-anchor: end;
        }
"""
SVG_TEMPLATE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -21 30 42">
    <defs>
        <style>{style}</style>
        <symbol id="heart" viewBox="-10 -10 20 20">
            <path class="fill" d="M 0,-5 A 1,1 0 0 1 8,0 Q 0,10 0,10 Q 0,10 -8,0 A 1,1 0 0 1 0,-5 Z" />
        </symbol>
        <symbol id="icon" viewBox="-25 -25 50 50">
            {icon_svg}
        </symbol>
    </defs>
    <!-- Card Layout -->
    <rect x="-14" y="-20" width="28" height="40" />
    <rect x="-14" y="-20" width="21" height="4" />
    <rect x="7" y="-20" width="7" height="7" />
    <rect x="-14" y="-16" width="21" height="21" />
    <use href="#icon" x="8" y="-19" width="5" height="5" />
    <rect x="7" y="-13" width="7" height="2" />
    <text x="7.5" y="-12" class="label">Cost</text>
    <rect x="7" y="-11" width="7" height="16" />
    <rect x="-14" y="5" width="28" height="11" />
    <rect x="-14" y="16" width="14" height="4" />
    <rect x="0" y="16" width="14" height="4" />
    <text x="-13.5" y="17" class="label">Attack</text>
    <text x="0.5" y="17" class="label">Defence</text>
    <!-- Card Details -->
    <text x="-3.5" y="-18" class="title">{name}</text>
    <text x="13.5" y="-12" class="cost">{cost}</text>
    <g>
        {hearts}
    </g>
    <text x="-13.5" y="4.5" class="effect">
        {effects}
    </text>
    <text x="-0.5" y="18" class="dice">{attack}</text>
    <text x="13.5" y="18" class="dice">{defence}</text>
</svg>
"""
ICON_SVG: dict[CardTypes, str] = {
    "king": """
    <path d="
        M 0,-24 0,-18 -6,-18 6,-18 0,-18 0,-10 Z
        M 21,7 21,14 Q 0,25 -21,14 L -21,7 Z
    " />
    <path class="fill" d="
        M 0,-10 Q 25,-25 21,0 Q 0,14 -21,0 Q -25,-25 0,-10 Z
        M 21,0 21,7 Q 0,25 -21,7 L -21,0 Z
    " />
""",
    "pawn": """
    <path class="fill" d="
        M 0,-20 Q -25,25 20,20 L -20,20 Q 25,25 0,-20 Z
    " />
""",
}

USE_HEART_SVG = """<use href="#heart" x="{x}" y="{y}" width="{width}" height="{height}" />"""


@cache
def heart_svg(life: int) -> str:
    hearts: list[str] = []
    # Max size = 6 x 15
    # With init size = 5 and width = 0.9 * height, it is impossible for width to get bigger than max
    max_height = 15
    init_size = 5
    cols = 1
    while True:
        height = init_size / cols
        width = height * 0.9
        max_rows = max_height // height
        if cols * max_rows >= life:
            break
        cols += 1
    for index in range(life):
        hearts.append(
            USE_HEART_SVG.format(
                x=10.5 - ((cols * width) / 2) + ((index % cols) * width),
                y=-3 - ((height * max_rows) / 2) + ((index // cols) * height),
                width=width,
                height=height,
            )
        )

    return "\n".join(hearts)


def generate_single_svg(card_data: CardJSON) -> str:
    return SVG_TEMPLATE.format(
        style=SVG_CSS,
        icon_svg=ICON_SVG.get(card_data["type"], ""),
        name=card_data["name"],
        cost=card_data["cost"],
        hearts=heart_svg(card_data["life"]),
        effects="".join(
            f'<tspan x="-13.5" dy="1.2em">{effect}</tspan>'
            for effect in (card_data.get("effects") or "").split("\n")
        ),
        attack=card_data["attack"],
        defence=card_data["defence"],
    )


if __name__ == "__main__":
    SCRIPT_DIR = dirname(abspath(args[0]))
    SVG_DIR = path_join(SCRIPT_DIR, "card_svgs")
    for base, _, files in walk(SVG_DIR):
        for file in files:
            remove(path_join(base, file))
    card_data_list: list[CardJSON]
    with open(path_join(SCRIPT_DIR, "card_defs.json"), "rt") as json:
        card_data_list = load(json)
    for card_data in card_data_list:
        output_filename = path_join(SVG_DIR, f"{card_data['name'].replace(' ','_')}.svg")
        print(f"{output_filename=} | {card_data=}")
        with open(output_filename, "wt+") as svg:
            svg.write(generate_single_svg(card_data))
