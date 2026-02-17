"""Sticky note color palette definitions."""

# Each color has a single bg used everywhere, plus a translucent variant and text color.
PALETTE = {
    "yellow": {
        "bg": "rgb(245, 235, 120)",
        "bg_alpha": "rgba(245, 235, 120, 0.90)",
        "header": "rgb(245, 235, 120)",
        "header_alpha": "rgba(245, 235, 120, 0.90)",
        "text": "rgb(60, 50, 0)",
    },
    "blue": {
        "bg": "rgb(130, 195, 250)",
        "bg_alpha": "rgba(130, 195, 250, 0.90)",
        "header": "rgb(130, 195, 250)",
        "header_alpha": "rgba(130, 195, 250, 0.90)",
        "text": "rgb(0, 30, 60)",
    },
    "pink": {
        "bg": "rgb(250, 165, 180)",
        "bg_alpha": "rgba(250, 165, 180, 0.90)",
        "header": "rgb(250, 165, 180)",
        "header_alpha": "rgba(250, 165, 180, 0.90)",
        "text": "rgb(80, 10, 20)",
    },
    "green": {
        "bg": "rgb(160, 230, 145)",
        "bg_alpha": "rgba(160, 230, 145, 0.90)",
        "header": "rgb(160, 230, 145)",
        "header_alpha": "rgba(160, 230, 145, 0.90)",
        "text": "rgb(15, 50, 10)",
    },
    "purple": {
        "bg": "rgb(195, 170, 250)",
        "bg_alpha": "rgba(195, 170, 250, 0.90)",
        "header": "rgb(195, 170, 250)",
        "header_alpha": "rgba(195, 170, 250, 0.90)",
        "text": "rgb(35, 10, 70)",
    },
    "gray": {
        "bg": "rgb(205, 205, 205)",
        "bg_alpha": "rgba(205, 205, 205, 0.90)",
        "header": "rgb(205, 205, 205)",
        "header_alpha": "rgba(205, 205, 205, 0.90)",
        "text": "rgb(30, 30, 30)",
    },
}

COLOR_ORDER = ["purple", "blue", "pink", "green", "yellow", "gray"]

# Text colors available for rich text formatting
TEXT_COLORS = [
    ("#000000", "Black"),
    ("#cc0000", "Red"),
    ("#0000cc", "Blue"),
    ("#007700", "Green"),
    ("#cc6600", "Orange"),
    ("#7700aa", "Purple"),
    ("#666666", "Gray"),
    ("#ffffff", "White"),
]
