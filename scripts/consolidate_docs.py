import os
from pathlib import Path

# Directorio base usando Pathlib para evitar líos de backslashes
base_dir = Path(r"\\wsl.localhost\Ubuntu\home\branko007\projects\rag_system\agent")
output_file = base_dir / "CONSOLIDADO_NOTEBOOK.md"

# Archivos a ignorar
ignore_files = ["CONSOLIDADO_NOTEBOOK.md", "README.md"]


def consolidate():
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# PROYECTO RAG ENTERPRISE - DOCUMENTACIÓN CONSOLIDADA\n\n")
        out.write(
            "> Este archivo contiene la totalidad de la documentación"
            " estratégica, técnica y operativa del proyecto.\n\n"
        )

        # 1. Intentar leer instructions.md primero para el árbol de directorios
        instr_path = base_dir / "instructions.md"
        if instr_path.exists():
            with open(instr_path, encoding="utf-8") as f:
                content = f.read()
                out.write("## 🗺️ MAPA DEL PROYECTO (CONTEXTO JERÁRQUICO)\n\n")
                out.write("A continuación se muestra la estructura de archivos definida en el proyecto:\n\n")
                out.write(content)
                out.write("\n\n---\n\n")

        # 2. Recorrer todos los archivos MD
        # Convertimos a lista y ordenamos para consistencia
        all_files = []
        for root, _dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".md") and file not in ignore_files and file != "instructions.md":
                    all_files.append(Path(root) / file)

        all_files.sort()

        for full_path in all_files:
            rel_path = full_path.relative_to(base_dir)

            print(f"Procesando: {rel_path}")

            out.write(f"## 📄 ARCHIVO: agent/{str(rel_path).replace(os.sep, '/')}\n\n")
            out.write("```markdown\n")
            try:
                with open(full_path, encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"Error al leer el archivo: {e!s}")
            out.write("\n```\n\n---\n\n")

    print(f"\n✅ ¡Éxito! Archivo generado en: {output_file}")


if __name__ == "__main__":
    consolidate()
