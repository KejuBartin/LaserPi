import colorsys


def rainbow(t):
    r, g, b = colorsys.hsv_to_rgb(t, 1.0, 1.0)

    return (
        int(r * 255),
        int(g * 255),
        int(b * 255),
    )