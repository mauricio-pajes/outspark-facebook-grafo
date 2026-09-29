"""Audita y visualiza el grafo Facebook New Orleans de MPI-SWS.

Entrada: facebook-links.txt.gz y facebook-wall.txt.gz originales.
Las amistades se convierten en aristas no dirigidas; cada publicación de muro
mantiene el sentido autor -> dueño del muro y su marca temporal.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx


def lines(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as stream:
        for number, raw in enumerate(stream, start=1):
            row = raw.rstrip("\r\n").split("\t")
            if len(row) != 3:
                raise ValueError(f"{path.name}:{number}: se esperaban 3 columnas")
            try:
                first, second = int(row[0]), int(row[1])
                stamp = None if row[2] == r"\N" else int(row[2])
            except ValueError as exc:
                raise ValueError(f"{path.name}:{number}: valor inválido") from exc
            yield first, second, stamp


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def date_utc(stamp: int | None) -> str | None:
    if stamp is None:
        return None
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d")


def load_friendships(path: Path):
    # NetworkX lee el .gz, toma las dos primeras columnas y reúne duplicados.
    graph = nx.read_edgelist(path, delimiter="\t", nodetype=int, data=False)
    rows = loops = timestamps = 0
    first_time = last_time = None
    for owner, friend, stamp in lines(path):
        rows += 1
        if owner == friend:
            loops += 1
        if stamp is not None:
            timestamps += 1
            first_time = stamp if first_time is None else min(first_time, stamp)
            last_time = stamp if last_time is None else max(last_time, stamp)
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph, {
        "filas_amistad_dirigidas": rows,
        "aristas_amistad_no_dirigidas_unicas": graph.number_of_edges(),
        "filas_lazo": loops,
        "filas_con_fecha_amistad": timestamps,
        "primera_amistad_utc": date_utc(first_time),
        "ultima_amistad_utc": date_utc(last_time),
    }


def load_wall_posts(path: Path):
    owners: set[int] = set()
    authors: set[int] = set()
    self_posts = rows = 0
    first_time = last_time = None
    for owner, author, stamp in lines(path):
        if stamp is None:
            raise ValueError("Una publicación de muro carece de fecha")
        rows += 1
        owners.add(owner)
        authors.add(author)
        self_posts += owner == author
        first_time = stamp if first_time is None else min(first_time, stamp)
        last_time = stamp if last_time is None else max(last_time, stamp)
    return authors, {
        "filas_publicaciones_muro": rows,
        "autores_distintos": len(authors),
        "duenos_muro_distintos": len(owners),
        "usuarios_muro_distintos": len(authors | owners),
        "publicaciones_muro_propio": self_posts,
        "primera_publicacion_utc": date_utc(first_time),
        "ultima_publicacion_utc": date_utc(last_time),
        "direccion": "segunda columna (autor) -> primera columna (dueño del muro)",
    }, owners | authors


def components(graph: nx.Graph):
    unseen = set(graph)
    sizes = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        size = 0
        while queue:
            current = queue.popleft()
            size += 1
            for neighbor in graph[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def reach_by_hops(graph: nx.Graph, seed: int, max_hops: int = 3):
    if seed not in graph:
        raise ValueError(f"El usuario {seed} no aparece en las amistades")
    seen = {seed}
    frontier = {seed}
    rounds = []
    for hop in range(1, max_hops + 1):
        following = set()
        for user in frontier:
            following.update(set(graph[user]) - seen)
        seen.update(following)
        rounds.append({"saltos": hop, "nuevos": len(following), "acumulados_sin_semilla": len(seen) - 1})
        frontier = following
    return rounds


def draw_subgraph(graph: nx.Graph, authors: set[int], seed: int, output: Path, limit: int):
    # La figura es un subgrafo inducido, no una muestra que sustituya la red completa.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    neighbors = sorted(graph[seed], key=lambda user: (-graph.degree(user), user))[: limit - 1]
    selected = [seed, *neighbors]
    subgraph = graph.subgraph(selected).copy()
    positions = nx.spring_layout(subgraph, seed=7, iterations=120)
    colors = ["#C62828" if user == seed else "#2679A8" if user in authors else "#AAB8C2" for user in subgraph]
    sizes = [260 if user == seed else 55 + min(graph.degree(user), 400) * 0.32 for user in subgraph]
    fig, ax = plt.subplots(figsize=(9, 5.3), dpi=170)
    fig.patch.set_facecolor("white")
    nx.draw_networkx_edges(subgraph, positions, ax=ax, width=0.65, edge_color="#B8C2CC", alpha=0.60)
    nx.draw_networkx_nodes(subgraph, positions, ax=ax, node_color=colors, node_size=sizes, linewidths=0.5, edgecolors="white")
    labels = {user: str(user) for user in selected[:7]}
    nx.draw_networkx_labels(subgraph, positions, labels, ax=ax, font_size=7, font_color="#1C2730")
    ax.set_title(f"Subgrafo de amistades de Facebook: {subgraph.number_of_nodes()} usuarios y {subgraph.number_of_edges()} relaciones", fontsize=11)
    ax.text(0.5, -0.03, "Rojo: usuario de referencia  ·  Azul: autor de publicaciones en muros  ·  Gris: sin autoría registrada", transform=ax.transAxes, ha="center", fontsize=7)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return {"nodos": subgraph.number_of_nodes(), "aristas": subgraph.number_of_edges(), "semilla": seed, "criterio": f"semilla y {len(neighbors)} vecinos con mayor grado"}


def draw_full_graph(graph: nx.Graph, output: Path):
    """Graphviz dibuja el grafo completo a partir de sus nodos y aristas."""
    executable = shutil.which("sfdp")
    if executable is None:
        raise RuntimeError("Se requiere Graphviz sfdp para dibujar el grafo completo")
    main_component = max(nx.connected_components(graph), key=len)
    dot = output.with_suffix(".dot")
    with dot.open("w", encoding="ascii") as stream:
        stream.write('graph Facebook {\n  graph [layout=sfdp, overlap=true, outputorder=edgesfirst, bgcolor="white", dpi=160, size="12,8!", margin=0.02, start=7];\n')
        stream.write('  node [shape=point, width=0.012, label="", color="#B94D2DE8"];\n')
        stream.write('  edge [color="#B94D2D1C", penwidth=0.18];\n')
        for user in sorted(graph):
            style = '' if user in main_component else ' [color="#9AAAB7B0"]'
            stream.write(f"  {user}{style};\n")
        for user in sorted(graph):
            for friend in sorted(graph[user]):
                if user < friend:
                    style = '' if user in main_component else ' [color="#AAB5BE88", penwidth=0.18]'
                    stream.write(f"  {user} -- {friend}{style};\n")
        stream.write("}\n")
    subprocess.run([executable, "-Tpng", str(dot), "-o", str(output)], check=True, timeout=600)
    return {"tipo": "grafo de nodos y aristas", "nodos": len(graph), "aristas_dibujadas": graph.number_of_edges(), "layout": "Graphviz sfdp", "sin_muestreo": True, "componente_resaltada_nodos": len(main_component), "archivo_dot": dot.name}


def export_full_edge_list(graph: nx.Graph, output: Path):
    """Escribe el grafo íntegro en formato CSV comprimido para reproducirlo."""
    with gzip.open(output, "wt", encoding="ascii") as stream:
        stream.write("usuario_1,usuario_2\n")
        for user in sorted(graph):
            for friend in sorted(graph[user]):
                if user < friend:
                    stream.write(f"{user},{friend}\n")


def analyze(links: Path, wall: Path, output: Path, seed: int, figure_nodes: int):
    output.mkdir(parents=True, exist_ok=True)
    graph, link_stats = load_friendships(links)
    authors, wall_stats, wall_users = load_wall_posts(wall)
    sizes = components(graph)
    degrees = sorted(((graph.degree(user), user) for user in graph), reverse=True)
    full_figure = draw_full_graph(graph, output / "grafo_completo_facebook.png")
    export_full_edge_list(graph, output / "aristas_amistad_completa.csv.gz")
    figure = draw_subgraph(graph, authors, seed, output / "subgrafo_facebook.png", figure_nodes)
    result = {
        "fuente": "MPI-SWS, Facebook New Orleans, WOSN 2009",
        "archivos": {links.name: sha256(links), wall.name: sha256(wall)},
        "amistades": {
            **link_stats,
            "usuarios_nodos": len(graph),
            "componentes_conexas": len(sizes),
            "componente_mayor": sizes[0],
            "cinco_componentes_mayores": sizes[:5],
            "grado_maximo": degrees[0][0],
            "usuario_grado_maximo": degrees[0][1],
            "usuarios_sin_aristas_en_archivo": sum(graph.degree(user) == 0 for user in graph),
            "observacion": "La lista de enlaces no enumera usuarios sin aparición en una arista.",
        },
        "muro": {**wall_stats, "usuarios_muro_presentes_en_amistades": len(wall_users & set(graph))},
        "bfs": {"semilla": seed, "rondas": reach_by_hops(graph, seed)},
        "figura_completa": full_figure,
        "figura": figure,
        "limite_interpretacion": "No hay ID de publicación, contenido ni trazas de republicación: no se pueden reconstruir cadenas históricas de compartidos.",
    }
    destination = output / "estadisticas_facebook.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"nodos": len(graph), "aristas": link_stats["aristas_amistad_no_dirigidas_unicas"], "publicaciones_muro": wall_stats["filas_publicaciones_muro"], "estadisticas": str(destination), "grafo_completo": str(output / "grafo_completo_facebook.png"), "subgrafo": str(output / "subgrafo_facebook.png")}, ensure_ascii=False))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--links", type=Path, default=Path("facebook-links.txt.gz"))
    parser.add_argument("--wall", type=Path, default=Path("facebook-wall.txt.gz"))
    parser.add_argument("--out", type=Path, default=Path("salida_facebook"))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--figure-nodes", type=int, default=45)
    args = parser.parse_args(argv)
    if args.figure_nodes < 2:
        parser.error("--figure-nodes debe ser al menos 2")
    return analyze(args.links, args.wall, args.out, args.seed, args.figure_nodes)


if __name__ == "__main__":
    main()
