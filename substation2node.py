#!/usr/bin/env python3
import osmium
import shapely.geometry as geom


# --------------------------------------------------------------
# Pass 1 — Extract:
#   - All existing substation nodes
#   - All substation polygons (ways + areas)
# --------------------------------------------------------------
class SubstationExtractor(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.existing_nodes = []   # (id, lon, lat, tags dict)
        self.polygons = []         # shapely geometries
        self.poly_tags = []        # corresponding tags

    def node(self, n):
        if n.tags.get("power") == "substation":
            self.existing_nodes.append(
                (n.id, n.location.lon, n.location.lat, dict(n.tags))
            )

    def way(self, w):
        if w.tags.get("power") == "substation":
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
                if len(coords) >= 3:
                    poly = geom.Polygon(coords)
                    if poly.is_valid:
                        self.polygons.append(poly)
                        self.poly_tags.append(dict(w.tags))
            except Exception:
                pass

    def area(self, a):
        if a.tags.get("power") == "substation":
            try:
                poly = osmium.geom.create_shapely(a)
                if poly.is_valid:
                    self.polygons.append(poly)
                    self.poly_tags.append(dict(a.tags))
            except Exception:
                pass


# --------------------------------------------------------------
# Pass 2 — Write ONLY:
#   - existing substation nodes
#   - centroid nodes
# --------------------------------------------------------------
class SubstationNodeWriter:
    def __init__(self, outfile):
        self.writer = osmium.SimpleWriter(outfile)

    def write_node(self, node_id, lon, lat, tags):
        node = osmium.osm.mutable.Node(
            id=node_id,
            version=1,
            visible=True,
            location=osmium.osm.Location(lon, lat),
            tags=[(k, v) for k, v in tags.items()]
        )
        self.writer.add_node(node)

    def close(self):
        self.writer.close()


# --------------------------------------------------------------
# Main
# --------------------------------------------------------------
def main(infile, outfile):
    print("Extracting substations...")
    extractor = SubstationExtractor()
    extractor.apply_file(infile, locations=True)

    print(f"✔ Found existing substation nodes: {len(extractor.existing_nodes)}")
    print(f"✔ Found substation polygons: {len(extractor.polygons)}")

    writer = SubstationNodeWriter(outfile)

    # Write existing substation nodes
    for nid, lon, lat, tags in extractor.existing_nodes:
        writer.write_node(nid, lon, lat, tags)

    # Add centroid nodes
    new_id = -1
    for poly, tags in zip(extractor.polygons, extractor.poly_tags):
        c = poly.centroid
        writer.write_node(new_id, c.x, c.y, tags)
        new_id -= 1

    writer.close()

    print(f"✔ Output written to {outfile}")
    print(f"✔ Total substation nodes in output: {len(extractor.existing_nodes) + len(extractor.polygons)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python output_substation_nodes_only.py input.osm output.osm")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
