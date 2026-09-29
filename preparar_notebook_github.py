"""Prepara el cuaderno de Colab que se publicará en GitHub."""

import json
from pathlib import Path


folder = Path(__file__).resolve().parent
destination = folder / "Outspark_grafo_Facebook_GitHub.ipynb"
source = folder / "Outspark_grafo_Facebook_output.ipynb"
if not source.exists():
    source = destination
notebook = json.loads(source.read_text(encoding="utf-8"))
code = (folder / "grafo_facebook.py").read_text(encoding="utf-8")
code = code.split('\nif __name__ == "__main__":\n', 1)[0] + "\n"
if "".join(notebook["cells"][1]["source"]) != code:
    for cell in notebook["cells"][1:]:
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
notebook["cells"][1]["source"] = code.splitlines(keepends=True)

notebook["cells"][0]["source"] = [
    "# Outspark: grafo histórico de Facebook\n",
    "\n",
    "Este cuaderno reproduce el grafo completo de amistades y un subgrafo de la red Facebook ",
    "New Orleans. Los datos proceden del [conjunto WOSN 2009 de MPI-SWS]",
    "(https://socialnetworks.mpi-sws.org/data-wosn2009.html).\n",
    "\n",
    "Al ejecutar las celdas en Google Colab, los dos archivos originales se descargan de ",
    "MPI-SWS y se comprueban mediante SHA-256. Las amistades describen conexiones históricas; ",
    "las publicaciones en muros no identifican cadenas de republicación. Las figuras que aparecen ",
    "guardadas en esta copia corresponden a una ejecución anterior y pueden regenerarse.\n",
]

notebook["cells"][2]["source"] = [
    "from pathlib import Path\n",
    "from urllib.request import urlopen\n",
    "import hashlib\n",
    "\n",
    "archivos = {\n",
    "    'facebook-links.txt.gz': '32d149f76c3421a08b03bfc629a9de6ce65b6fa56272cd9d5424e3de5b1acff2',\n",
    "    'facebook-wall.txt.gz': 'c4449336e346061068b8278d09176b195b3f132f6d6fe50adbc5730938496dca',\n",
    "}\n",
    "base = 'https://socialnetworks.mpi-sws.org/data/'\n",
    "for nombre, sha_esperado in archivos.items():\n",
    "    ruta = Path(nombre)\n",
    "    if not ruta.is_file() or hashlib.sha256(ruta.read_bytes()).hexdigest() != sha_esperado:\n",
    "        temporal = ruta.with_suffix(ruta.suffix + '.descarga')\n",
    "        with urlopen(base + nombre, timeout=120) as origen, temporal.open('wb') as destino:\n",
    "            while bloque := origen.read(1024 * 1024):\n",
    "                destino.write(bloque)\n",
    "        if hashlib.sha256(temporal.read_bytes()).hexdigest() != sha_esperado:\n",
    "            temporal.unlink(missing_ok=True)\n",
    "            raise ValueError(f'La descarga de {nombre} no coincide con el archivo analizado')\n",
    "        temporal.replace(ruta)\n",
    "    print(f'Datos verificados: {nombre}')\n",
    "\n",
    "resultado = main([\n",
    "    '--links', 'facebook-links.txt.gz',\n",
    "    '--wall', 'facebook-wall.txt.gz',\n",
    "    '--out', 'salida_facebook',\n",
    "])\n",
]

destination.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(destination)
