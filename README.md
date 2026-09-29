# Outspark: grafo histórico de Facebook

Este repositorio contiene el [cuaderno de Google Colab](Outspark_grafo_Facebook_GitHub.ipynb) que construye el grafo completo de amistades de Facebook New Orleans y amplía un subgrafo para leer sus relaciones. [Abrir el cuaderno en Colab](https://colab.research.google.com/github/outspark-app/outspark-facebook-grafo/blob/main/Outspark_grafo_Facebook_GitHub.ipynb). El código está también en [`grafo_facebook.py`](grafo_facebook.py).

El grafo de amistades se carga con `nx.read_edgelist("facebook-links.txt.gz", delimiter="\t", nodetype=int, data=False)`. NetworkX reúne las filas repetidas en 63 731 nodos y 817 090 aristas. La BFS usada para componentes y alcance está implementada en Python en el mismo archivo. Graphviz `sfdp` calcula las posiciones; las componentes pequeñas se compactan alrededor de la mayor y `neato` dibuja todos los nodos y aristas. NetworkX y Matplotlib dibujan el subgrafo de apoyo. La longitud visual de una arista no mide distancia social.

El cuaderno descarga `facebook-links.txt.gz` y `facebook-wall.txt.gz` directamente del [conjunto WOSN 2009 de MPI-SWS](https://socialnetworks.mpi-sws.org/data-wosn2009.html), verifica sus sumas SHA-256 y reproduce las figuras y estadísticas. Los archivos de datos no se redistribuyen en este repositorio.

Los identificadores son anónimos y los datos históricos. Una amistad representa una conexión, no una interacción ni una cadena observada de republicaciones. Las publicaciones en muros tienen autor, destinatario y fecha, pero no permiten seguir un mismo contenido entre usuarios.

El cuaderno muestra la carga del grafo en una celda breve y obtiene el código detallado de [`grafo_facebook.py`](grafo_facebook.py) desde este repositorio, comprobando su SHA-256. Para actualizarlo, modifica ese archivo, ejecuta `python preparar_notebook_github.py` y publica ambos archivos con `git commit` y `git push`. El preparador limpia las salidas guardadas; vuelve a ejecutar el cuaderno y guarda sus figuras antes de publicarlo. El enlace de Colab conserva la misma dirección y abre la versión publicada más reciente.
