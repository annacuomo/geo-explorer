"""Small geometry helpers shared by the build scripts."""
import numpy as np

def simplify(points, tolerance):
    """Douglas-Peucker line simplification: drops points that change the outline
    by less than `tolerance` (in the same units as the points)."""
    if len(points) < 4:
        return points
    keep = np.zeros(len(points), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q, seg = points[a], points[b], points[a + 1:b]
        d = q - p
        n = np.hypot(*d)
        dist = (np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / n) if n > 0 else np.hypot(*(seg - p).T)
        i = int(np.argmax(dist))
        if dist[i] > tolerance:
            m = a + 1 + i
            keep[m] = True
            stack += [(a, m), (m, b)]
    return points[keep]

def area(xy):
    """Area of a polygon (shoelace formula)."""
    x, y = xy[:, 0], xy[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def clip_north_of(ring, lat):
    """Keeps only the part of a lon/lat polygon north of `lat` (used to draw Morocco without Western Sahara)."""
    out, r = [], [tuple(v[:2]) for v in ring]
    for i in range(len(r)):
        a, b = r[i - 1], r[i]
        a_in, b_in = a[1] >= lat, b[1] >= lat
        if b_in:
            if not a_in:
                t = (lat - a[1]) / (b[1] - a[1]); out.append((a[0] + t * (b[0] - a[0]), lat))
            out.append(b)
        elif a_in:
            t = (lat - a[1]) / (b[1] - a[1]); out.append((a[0] + t * (b[0] - a[0]), lat))
    if out and out[0] != out[-1]:
        out.append(out[0])
    return out

def polygons(geometry):
    """List of polygons (each a list of rings) from a GeoJSON geometry."""
    if not geometry:
        return []
    if geometry['type'] == 'Polygon':
        return [geometry['coordinates']]
    if geometry['type'] == 'MultiPolygon':
        return geometry['coordinates']
    return []
