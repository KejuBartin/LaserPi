import math

def generateCornerShape(center, size, sides, sizeMode, angleOffset=0, pixelSnap=True):
    # 1) Build unit polygon
    angle_step = 360 / sides
    points = []
    for i in range(sides):
        a = math.radians(i * angle_step + angleOffset)
        points.append((math.cos(a), math.sin(a)))

    unit_center_x = 0.0
    unit_center_y = 0.0

    if sizeMode == "radius":
        sx = sy = size
    elif sizeMode == "diameter":
        sx = sy = size / 2
    elif sizeMode == "bbox":
        # size can be number (square box) or (width, height)
        if isinstance(size, (tuple, list)):
            target_w, target_h = size
        else:
            target_w = target_h = size

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        # Keep the resulting bbox centered on the provided center point.
        unit_center_x = (min_x + max_x) / 2
        unit_center_y = (min_y + max_y) / 2

        sx = target_w / (max_x - min_x)
        sy = target_h / (max_y - min_y)
    else:
        raise ValueError("sizeMode must be 'radius', 'diameter', or 'bbox'")

    # 2) Scale + translate
    shape = [
        (
            center[0] + (x - unit_center_x) * sx,
            center[1] + (y - unit_center_y) * sy,
        )
        for x, y in points
    ]

    # Snap to integer pixel positions to reduce subtle rasterization bias.
    if pixelSnap:
        shape = [(round(x), round(y)) for x, y in shape]

    return shape