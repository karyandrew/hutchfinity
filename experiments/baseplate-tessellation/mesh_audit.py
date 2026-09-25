#!/usr/bin/env python3
"""Dependency-free STL audit and bounded mating-surface comparison."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import struct
from collections import Counter
from pathlib import Path

PITCH = 21.0
SAMPLE_SPACING_MM = 0.025
REPETITION_SAMPLE_SPACING_MM = 0.1
MAX_DEVIATION_MM = 0.05
P99_DEVIATION_MM = 0.025
DATUM_TOLERANCE_MM = 0.01
CONTACT_EXTENT_MIN_MM = 7.25
CONTACT_EXTENT_MAX_MM = 10.0
SECTION_Z_MM = (0.4, 1.4, 2.7, 3.5)
ALL_Z_MAX_STEP_MM = 0.1


def triangles(path: Path):
    data = path.read_bytes()
    if len(data) >= 84 and 84 + struct.unpack_from("<I", data, 80)[0] * 50 == len(data):
        count = struct.unpack_from("<I", data, 80)[0]
        for i in range(count):
            vals = struct.unpack_from("<12fH", data, 84 + i * 50)
            yield tuple(vals[3:6]), tuple(vals[6:9]), tuple(vals[9:12])
        return
    verts = []
    for line in data.decode("ascii").splitlines():
        fields = line.split()
        if fields[:1] == ["vertex"]:
            verts.append(tuple(float(v) for v in fields[1:4]))
            if len(verts) == 3:
                yield tuple(verts)
                verts = []
    if verts:
        raise ValueError(f"incomplete ASCII STL facet: {path}")


def qvertex(v):
    return tuple(round(x, 9) for x in v)


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a


def audit(path: Path):
    tris = list(triangles(path))
    if not tris:
        raise ValueError(f"no facets: {path}")
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    edges = Counter()
    directed_edges = Counter()
    vertices = set()
    owners = {}
    uf = UnionFind(len(tris))
    for i, tri in enumerate(tris):
        for v in tri:
            for axis in range(3):
                lo[axis] = min(lo[axis], v[axis])
                hi[axis] = max(hi[axis], v[axis])
        q = [qvertex(v) for v in tri]
        vertices.update(q)
        for a, b in ((q[0], q[1]), (q[1], q[2]), (q[2], q[0])):
            edge = tuple(sorted((a, b)))
            edges[edge] += 1
            directed_edges[edge] += 1 if (a, b) == edge else -1
            if edge in owners:
                uf.union(i, owners[edge])
            else:
                owners[edge] = i
    counts = Counter(edges.values())
    components = len({uf.find(i) for i in range(len(tris))})
    watertight = counts == {2: len(edges)}
    consistently_oriented = watertight and all(value == 0 for value in directed_edges.values())
    euler_characteristic = len(vertices) - len(edges) + len(tris)
    genus = None
    if consistently_oriented:
        candidate_genus = components - euler_characteristic / 2
        if candidate_genus >= 0 and candidate_genus.is_integer():
            genus = int(candidate_genus)
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "facets": len(tris),
        "vertices": len(vertices),
        "edges": len(edges),
        "components": components,
        "manifold_or_watertight": watertight,
        "consistently_oriented": consistently_oriented,
        "euler_characteristic": euler_characteristic,
        "genus": genus,
        "edge_incidence": {str(k): v for k, v in sorted(counts.items())},
        "bounds_mm": [lo, hi],
    }


def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def add(a, b): return tuple(x+y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def norm2(a): return dot(a, a)


def point_segment_distance(p, a, b):
    segment = sub(b, a)
    length2 = norm2(segment)
    if length2 == 0:
        return math.sqrt(norm2(sub(p, a)))
    t = max(0.0, min(1.0, dot(sub(p, a), segment)/length2))
    return math.sqrt(norm2(sub(p, add(a, mul(segment, t)))))


def point_triangle_distance(p, tri):
    # Real-Time Collision Detection, Christer Ericson, closest-point regions.
    a, b, c = tri
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0: return math.sqrt(norm2(ap))
    bp = sub(p, b); d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3: return math.sqrt(norm2(bp))
    vc = d1*d4-d3*d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1/(d1-d3); return math.sqrt(norm2(sub(p, add(a, mul(ab, v)))))
    cp = sub(p, c); d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6: return math.sqrt(norm2(cp))
    vb = d5*d2-d1*d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2/(d2-d6); return math.sqrt(norm2(sub(p, add(a, mul(ac, w)))))
    va = d3*d6-d5*d4
    if va <= 0 and d4-d3 >= 0 and d5-d6 >= 0:
        w = (d4-d3)/((d4-d3)+(d5-d6)); return math.sqrt(norm2(sub(p, add(b, mul(sub(c,b), w)))))
    n = math.sqrt(norm2((ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])))
    if n == 0:
        return min(point_segment_distance(p, a, b), point_segment_distance(p, b, c), point_segment_distance(p, c, a))
    return abs(dot(ap, (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])))/n


def bbox(tri):
    return tuple(min(v[i] for v in tri) for i in range(3)), tuple(max(v[i] for v in tri) for i in range(3))


def bbox_dist2(p, box):
    lo, hi = box
    return sum((lo[i]-p[i])**2 if p[i] < lo[i] else (p[i]-hi[i])**2 if p[i] > hi[i] else 0 for i in range(3))


class Node:
    def __init__(self, tris, leaf=12):
        self.box = (tuple(min(v[i] for t in tris for v in t) for i in range(3)), tuple(max(v[i] for t in tris for v in t) for i in range(3)))
        self.children = None
        self.tris = tris
        if len(tris) > leaf:
            span = [self.box[1][i]-self.box[0][i] for i in range(3)]
            axis = max(range(3), key=span.__getitem__)
            tris.sort(key=lambda t: sum(v[axis] for v in t)/3)
            mid = len(tris)//2
            self.children = Node(tris[:mid]), Node(tris[mid:])
            self.tris = None

    def distance(self, p):
        best = math.inf
        queue = [(bbox_dist2(p, self.box), 0, self)]
        serial = 1
        while queue:
            bound, _, node = heapq.heappop(queue)
            if bound >= best*best: continue
            if node.children:
                for child in node.children:
                    heapq.heappush(queue, (bbox_dist2(p, child.box), serial, child)); serial += 1
            else:
                best = min(best, *(point_triangle_distance(p, t) for t in node.tris))
        return best


def normal(tri):
    a,b,c=tri; u,v=sub(b,a),sub(c,a)
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    length=math.sqrt(norm2(n))
    return tuple(x/length for x in n) if length else (0,0,0)


def cell_geometry(bounds):
    lo, hi = bounds
    return lo, round((hi[0]-lo[0])/PITCH), round((hi[1]-lo[1])/PITCH)


def triangle_cell(tri, bounds):
    lo, cells_x, cells_y = cell_geometry(bounds)
    center = tuple(sum(v[i] for v in tri)/3 for i in range(3))
    cell = (
        min(cells_x-1, max(0, int((center[0]-lo[0])/PITCH))),
        min(cells_y-1, max(0, int((center[1]-lo[1])/PITCH))),
    )
    cell_center = (lo[0] + (cell[0] + .5)*PITCH, lo[1] + (cell[1] + .5)*PITCH)
    return center, cell, cell_center


def contact_cells(tris, bounds):
    lo, hi = bounds
    _, cells_x, cells_y = cell_geometry(bounds)
    result = {(x, y): [] for x in range(cells_x) for y in range(cells_y)}
    for tri in tris:
        c, cell, center = triangle_cell(tri, bounds)
        local_extent = max(abs(c[0]-center[0]), abs(c[1]-center[1]))
        face_normal = normal(tri)
        points_toward_pocket = face_normal[0]*(c[0]-center[0]) + face_normal[1]*(c[1]-center[1]) < 0
        # The active pad_oversize cavity has corner centers at +/-6.5mm and
        # radii from 1.05mm to about 3.25mm over the exported z range. This
        # isolates its sloped/vertical foot-contact wall from the exterior
        # baseplate wall (10.5mm from a cell center) and horizontal faces.
        if (CONTACT_EXTENT_MIN_MM <= local_extent <= CONTACT_EXTENT_MAX_MM
                and lo[2]-1e-6 <= c[2] <= hi[2]+1e-6
                and abs(face_normal[2]) < 0.999
                and points_toward_pocket):
            result[cell].append(tri)
    if any(not value for value in result.values()):
        missing = [list(cell) for cell, value in result.items() if not value]
        raise ValueError(f"no contact triangles for cells: {missing}")
    return result


def horizontal_interface_triangles(tris, center):
    """Horizontal triangles whose XY boxes intersect one pocket-local window."""
    result = []
    for tri in tris:
        if abs(normal(tri)[2]) < 0.999:
            continue
        lo, hi = bbox(tri)
        if all(hi[axis] >= center[axis]-CONTACT_EXTENT_MAX_MM
               and lo[axis] <= center[axis]+CONTACT_EXTENT_MAX_MM
               for axis in range(2)):
            result.append(tri)
    if not result:
        raise ValueError("no horizontal interface triangles")
    return result


def clipped_segment(a, b, center, half_extent=CONTACT_EXTENT_MAX_MM):
    """Clip one XY segment to a square, returning its endpoint parameters."""
    lower, upper = 0.0, 1.0
    for axis in range(2):
        delta = b[axis]-a[axis]
        minimum, maximum = center[axis]-half_extent, center[axis]+half_extent
        if abs(delta) < 1e-15:
            if not minimum <= a[axis] <= maximum:
                return None
            continue
        enter, leave = (minimum-a[axis])/delta, (maximum-a[axis])/delta
        if enter > leave:
            enter, leave = leave, enter
        lower, upper = max(lower, enter), min(upper, leave)
        if lower > upper:
            return None
    return lower, upper


def horizontal_interface_samples(tris, center, spacing=REPETITION_SAMPLE_SPACING_MM):
    """Sample horizontal lands inside the pocket-local annular window."""
    points = set()
    for tri in tris:
        centroid = tuple(sum(v[i] for v in tri)/3 for i in range(3))
        if CONTACT_EXTENT_MIN_MM <= max(abs(centroid[0]-center[0]), abs(centroid[1]-center[1])) <= CONTACT_EXTENT_MAX_MM:
            points.add(qvertex(centroid))
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            clipped = clipped_segment(a, b, center)
            if clipped is None:
                continue
            start, end = clipped
            length = math.hypot(b[0]-a[0], b[1]-a[1])*(end-start)
            steps = max(1, math.ceil(length/spacing))
            for index in range(steps+1):
                t = start+(end-start)*index/steps
                point = add(a, mul(sub(b, a), t))
                extent = max(abs(point[0]-center[0]), abs(point[1]-center[1]))
                if CONTACT_EXTENT_MIN_MM <= extent <= CONTACT_EXTENT_MAX_MM:
                    points.add(qvertex(point))
    if not points:
        raise ValueError("no horizontal interface samples")
    return points


def horizontal_directed(source, target, center):
    tree = Node(list(target))
    distances = [tree.distance(point) for point in horizontal_interface_samples(source, center)]
    return {"samples": len(distances), "max_mm": max(distances), "p99_mm": percentile(distances, .99)}


def local_triangles(tris, cell, bounds):
    lo, _ = bounds
    center = (lo[0] + (cell[0] + .5)*PITCH, lo[1] + (cell[1] + .5)*PITCH, 0)
    return [tuple(sub(vertex, center) for vertex in tri) for tri in tris]


def mesh_key(tris):
    canonical = sorted(tuple(sorted(qvertex(vertex) for vertex in tri)) for tri in tris)
    payload = repr(canonical).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def vertex_centroid_samples(tris):
    points = {qvertex(vertex) for tri in tris for vertex in tri}
    points.update(qvertex(tuple(sum(v[i] for v in tri)/3 for i in range(3))) for tri in tris)
    return points


def symmetric_vertex_centroid_distance(a, b):
    tree_a, tree_b = Node(list(a)), Node(list(b))
    return max(
        max(tree_b.distance(point) for point in vertex_centroid_samples(a)),
        max(tree_a.distance(point) for point in vertex_centroid_samples(b)),
    )


def repetition(cells, bounds, include_sections=True):
    hashes = {cell: mesh_key(local_triangles(tris, cell, bounds)) for cell, tris in cells.items()}
    counts = Counter(hashes.values())
    local = {cell: local_triangles(tris, cell, bounds) for cell, tris in cells.items()}
    representatives = {}
    for cell, digest in hashes.items():
        representatives.setdefault(digest, local[cell])
    reference_mesh = local[sorted(local)[len(local)//2]]
    sampled_maximum = max(
        symmetric_vertex_centroid_distance(reference_mesh, value)
        for value in representatives.values()
    )
    result = {
        "cells": len(cells),
        "unique_contact_triangulations": len(counts),
        "max_repeated_vertex_centroid_delta_mm": sampled_maximum,
        "repeated_vertex_centroids_within_tolerance": sampled_maximum <= DATUM_TOLERANCE_MM,
        "identity_proved": False,
    }
    if include_sections:
        sections = {cell: section_metrics(value) for cell, value in local.items()}
        reference = sections[sorted(sections)[len(sections)//2]]
        maximum = max(max_numeric_delta(reference, value) for value in sections.values())
        result.update({
            "max_cross_section_datum_delta_mm": maximum,
            "cross_section_datums_identical_across_placements": maximum <= DATUM_TOLERANCE_MM,
        })
    return result


def samples(tri, spacing=SAMPLE_SPACING_MM):
    longest=max(math.sqrt(norm2(sub(tri[i],tri[j]))) for i,j in ((0,1),(1,2),(2,0)))
    n=max(1,math.ceil(longest/spacing))
    a,b,c=tri
    for i in range(n+1):
        for j in range(n+1-i):
            yield add(a, add(mul(sub(b,a),i/n),mul(sub(c,a),j/n)))


def percentile(values, q):
    values=sorted(values)
    return values[min(len(values)-1, math.ceil(q*len(values))-1)]


def surface_samples(tris, spacing=SAMPLE_SPACING_MM):
    """Sample every unique contact-mesh edge by XY length plus centroids.

    Adaptive z sections provide the complementary vertical coverage. This
    remains a finite sample, not an exact full-surface Hausdorff oracle.
    """
    points = {qvertex(tuple(sum(v[i] for v in tri)/3 for i in range(3))) for tri in tris}
    edges = set()
    for tri in tris:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges.add(tuple(sorted((qvertex(a), qvertex(b)))))
    for a, b in edges:
        xy_length = math.hypot(b[0]-a[0], b[1]-a[1])
        steps = max(1, math.ceil(xy_length/spacing))
        for index in range(steps+1):
            points.add(qvertex(add(a, mul(sub(b, a), index/steps))))
    return points


def directed(source, target, spacing=SAMPLE_SPACING_MM):
    tree=Node(list(target))
    distances=[tree.distance(p) for p in surface_samples(source, spacing)]
    return {"samples":len(distances),"max_mm":max(distances),"p99_mm":percentile(distances,.99)}


def section_segments(tris, z):
    result = []
    for tri in tris:
        points = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            az, bz = a[2]-z, b[2]-z
            if abs(az) < 1e-9:
                points.append((a[0], a[1]))
            if az*bz < 0:
                t = (z-a[2])/(b[2]-a[2])
                points.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
        unique = []
        for point in points:
            if not any(math.dist(point, old) < 1e-8 for old in unique):
                unique.append(point)
        if len(unique) >= 2:
            result.append((unique[0], unique[1]))
    if not result:
        raise ValueError(f"no contact cross-section at z={z}")
    return result


def section_metrics(tris, z_values=SECTION_Z_MM):
    result = {}
    for z in z_values:
        segments = section_segments(tris, z)
        points = [point for segment in segments for point in segment]
        lo = [min(point[axis] for point in points) for axis in range(2)]
        hi = [max(point[axis] for point in points) for axis in range(2)]
        width = [hi[axis]-lo[axis] for axis in range(2)]
        result[str(z)] = {
            "bounds_xy_mm": [lo, hi],
            "center_xy_mm": [(lo[axis]+hi[axis])/2 for axis in range(2)],
            "opening_xy_mm": width,
            "land_to_next_pocket_xy_mm": [PITCH-value for value in width],
            "segments": len(segments),
        }
    return result


def adaptive_section_levels(a, b, max_step=ALL_Z_MAX_STEP_MM):
    """Sample inside every shared z slab, with no gap larger than max_step."""
    az = [vertex[2] for tri in a for vertex in tri]
    bz = [vertex[2] for tri in b for vertex in tri]
    lower, upper = max(min(az), min(bz)), min(max(az), max(bz))
    if upper <= lower:
        raise ValueError("contact surfaces have no shared z range")
    breaks = sorted({lower, upper, *(z for z in az + bz if lower < z < upper)})
    epsilon = min(1e-6, (upper-lower)/1000)
    levels = set()
    for left, right in zip(breaks, breaks[1:]):
        width = right-left
        steps = max(1, math.ceil(width/max_step))
        for index in range(steps):
            levels.add(left + width*(index+.5)/steps)
        if left > lower:
            levels.add(left+epsilon)
            levels.add(left-epsilon)
    return sorted(z for z in levels if lower < z < upper)


def all_z_section_comparison(a, b):
    levels = adaptive_section_levels(a, b)
    deltas = []
    for z in levels:
        metrics_a = section_metrics(a, (z,))[str(z)]
        metrics_b = section_metrics(b, (z,))[str(z)]
        deltas.append(max_numeric_delta(metrics_a, metrics_b))
    gaps = [right-left for left, right in zip(levels, levels[1:])]
    return {
        "sampled_sections": len(levels),
        "z_range_mm": [levels[0], levels[-1]],
        "max_section_spacing_mm": max(gaps, default=0.0),
        "max_sampled_section_datum_delta_mm": max(deltas),
        "continuous_all_z_bound_proved": False,
    }


def functional_datums(cells, bounds):
    per_cell = {}
    centers = {}
    for cell, tris in cells.items():
        local = local_triangles(tris, cell, bounds)
        per_cell[cell] = section_metrics(local)
        section = per_cell[cell][str(SECTION_Z_MM[1])]
        lo, _ = bounds
        centers[cell] = [
            lo[0] + (cell[0]+.5)*PITCH + section["center_xy_mm"][0],
            lo[1] + (cell[1]+.5)*PITCH + section["center_xy_mm"][1],
        ]
    pitch_errors = []
    for (x, y), center in centers.items():
        if (x+1, y) in centers:
            pitch_errors.append(abs((centers[(x+1, y)][0]-center[0])-PITCH))
        if (x, y+1) in centers:
            pitch_errors.append(abs((centers[(x, y+1)][1]-center[1])-PITCH))
    exemplar = per_cell[sorted(per_cell)[len(per_cell)//2]]
    z_values = [vertex[2] for tris in cells.values() for tri in tris for vertex in tri]
    return {
        "cross_sections": exemplar,
        "contact_depth_range_mm": [min(z_values), max(z_values)],
        "max_pocket_pitch_error_mm": max(pitch_errors, default=0.0),
    }


def max_numeric_delta(a, b):
    if isinstance(a, dict):
        return max((max_numeric_delta(a[key], b[key]) for key in a if key != "segments"), default=0.0)
    if isinstance(a, list):
        return max((max_numeric_delta(x, y) for x, y in zip(a, b)), default=0.0)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a-b)
    return 0.0


def compare(a_path: Path, b_path: Path):
    a, b = list(triangles(a_path)), list(triangles(b_path))
    aa, bb = audit(a_path), audit(b_path)
    cells_a, cells_b = contact_cells(a, aa["bounds_mm"]), contact_cells(b, bb["bounds_mm"])
    representative = sorted(cells_a)[len(cells_a)//2]
    ca = local_triangles(cells_a[representative], representative, aa["bounds_mm"])
    cb = local_triangles(cells_b[representative], representative, bb["bounds_mm"])
    lo = aa["bounds_mm"][0]
    horizontal_center = (lo[0] + (representative[0] + .5)*PITCH, lo[1] + (representative[1] + .5)*PITCH)
    ha = horizontal_interface_triangles(a, horizontal_center)
    hb = horizontal_interface_triangles(b, horizontal_center)
    ab, ba = directed(ca, cb), directed(cb, ca)
    hab, hba = horizontal_directed(ha, hb, horizontal_center), horizontal_directed(hb, ha, horizontal_center)
    sampled_max=max(ab["max_mm"],ba["max_mm"])
    p99=max(ab["p99_mm"],ba["p99_mm"])
    sampled_plus_spacing=sampled_max+SAMPLE_SPACING_MM
    horizontal_sampled_max=max(hab["max_mm"],hba["max_mm"])
    horizontal_p99=max(hab["p99_mm"],hba["p99_mm"])
    datum=max(abs(x-y) for bounds_a,bounds_b in zip(aa["bounds_mm"],bb["bounds_mm"]) for x,y in zip(bounds_a,bounds_b))
    topology=(aa["components"]==bb["components"]
              and aa["manifold_or_watertight"] and bb["manifold_or_watertight"]
              and aa["consistently_oriented"] and bb["consistently_oriented"]
              and aa["euler_characteristic"]==bb["euler_characteristic"]
              and aa["genus"]==bb["genus"])
    repeat_a, repeat_b = repetition(cells_a, aa["bounds_mm"]), repetition(cells_b, bb["bounds_mm"])
    datums_a, datums_b = functional_datums(cells_a, aa["bounds_mm"]), functional_datums(cells_b, bb["bounds_mm"])
    datum_delta = max_numeric_delta(datums_a, datums_b)
    all_z = all_z_section_comparison(ca, cb)
    functional_ok = repeat_a["cross_section_datums_identical_across_placements"] and repeat_b["cross_section_datums_identical_across_placements"] and datum_delta <= DATUM_TOLERANCE_MM
    narrow_ok = topology and sampled_plus_spacing<=MAX_DEVIATION_MM and p99<=P99_DEVIATION_MM and datum<=DATUM_TOLERANCE_MM and functional_ok
    enhanced_ok = (narrow_ok
                   and horizontal_sampled_max <= MAX_DEVIATION_MM
                   and horizontal_p99 <= P99_DEVIATION_MM
                   and all_z["max_sampled_section_datum_delta_mm"] <= DATUM_TOLERANCE_MM
                   and repeat_a["repeated_vertex_centroids_within_tolerance"]
                   and repeat_b["repeated_vertex_centroids_within_tolerance"])
    return {
        "baseline": aa,
        "candidate": bb,
        "surface": "sampled sloped/vertical pad_oversize walls plus separately sampled interface-adjacent horizontal lands",
        "representative_cell": list(representative),
        "contact_extent_filter_mm": [CONTACT_EXTENT_MIN_MM, CONTACT_EXTENT_MAX_MM],
        "sample_spacing_mm": SAMPLE_SPACING_MM,
        "horizontal_and_repetition_sample_spacing_mm": REPETITION_SAMPLE_SPACING_MM,
        "baseline_to_candidate": ab,
        "candidate_to_baseline": ba,
        "sampled_symmetric_max_mm": sampled_max,
        "sampled_max_plus_spacing_diagnostic_mm": sampled_plus_spacing,
        "symmetric_p99_mm": p99,
        "horizontal_baseline_to_candidate": hab,
        "horizontal_candidate_to_baseline": hba,
        "horizontal_sampled_symmetric_max_mm": horizontal_sampled_max,
        "horizontal_symmetric_p99_mm": horizontal_p99,
        "all_z_section_sampling": all_z,
        "max_exterior_bound_delta_mm": datum,
        "baseline_repetition": repeat_a,
        "candidate_repetition": repeat_b,
        "horizontal_repetition": "NOT_ASSESSED: exported horizontal-land triangles span cell boundaries, so per-cell identity is not a valid partition",
        "baseline_functional_datums": datums_a,
        "candidate_functional_datums": datums_b,
        "max_functional_datum_delta_mm": datum_delta,
        "limits_mm": {
            "sampled_max_plus_spacing_diagnostic": MAX_DEVIATION_MM,
            "sampled_p99": P99_DEVIATION_MM,
            "exterior_bound": DATUM_TOLERANCE_MM,
            "functional_datum": DATUM_TOLERANCE_MM,
        },
        "topology_invariants": ["components", "watertight edge incidence", "consistent orientation", "Euler characteristic", "genus"],
        "topology_preserved": topology,
        "narrow_sampled_contact_and_datum_check_pass": narrow_ok,
        "enhanced_sampled_diagnostics_pass": enhanced_ok,
        "bounded_surface_check_pass": False,
        "surface_acceptance": "INCONCLUSIVE: finite wall/horizontal samples and z sections are not an exact full-surface Hausdorff or volumetric oracle",
        "volumetric_acceptance": "UNKNOWN: no volumetric minimum-wall/land oracle was run",
        "functional_datums_accepted": functional_ok,
        "production_fit": False,
    }


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("analyze"); p.add_argument("stl",type=Path)
    p=sub.add_parser("compare"); p.add_argument("baseline",type=Path); p.add_argument("candidate",type=Path)
    args=parser.parse_args()
    result=audit(args.stl) if args.command=="analyze" else compare(args.baseline,args.candidate)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__ == "__main__": main()
