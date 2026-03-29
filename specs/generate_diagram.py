import os
import re

specs_dir = "/home/lautaro/Escritorio/DataOilers/enterprise-ai-platform-1/specs"

# ID regex
id_regex = re.compile(r"(T\d-S\d-\d{2})")

nodes = set()
edges = set()

for root, _, files in os.walk(specs_dir):
    for f in files:
        if not f.endswith(".md"):
            continue
        filepath = os.path.join(root, f)

        self_match = id_regex.search(f)
        if not self_match:
            continue
        self_id = self_match.group(1)
        nodes.add(self_id)

        with open(filepath, encoding="utf-8") as file:
            content = file.read()

            lines = content.split("\n")
            for line in lines:
                if "Depende de" in line or "Pendiente de" in line:
                    deps = id_regex.findall(line)
                    for dep in deps:
                        if dep != self_id:
                            nodes.add(dep)
                            edges.add((dep, self_id))  # dep -> self_id

                if "Bloqueante" in line or "Bloquea" in line:
                    blocks = id_regex.findall(line)
                    for block in blocks:
                        if block != self_id:
                            nodes.add(block)
                            edges.add((self_id, block))  # self_id -> block

with open("/home/lautaro/Escritorio/DataOilers/enterprise-ai-platform-1/specs/diagram.md", "w") as out:
    out.write("```mermaid\n")
    out.write("graph TD;\n")
    for node in sorted(nodes):
        out.write(f"    {node};\n")
    for edge in sorted(edges):
        out.write(f"    {edge[0]} --> {edge[1]};\n")
    out.write("```\n")

print("Done")  # noqa: T201
