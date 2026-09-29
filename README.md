# Outspark: grafo histórico de Facebook

Este repositorio contiene el [cuaderno de Google Colab](Outspark_grafo_Facebook_GitHub.ipynb) que construye el grafo completo de amistades de Facebook New Orleans y amplía un subgrafo para leer sus relaciones. El código está también en [`grafo_facebook.py`](grafo_facebook.py).

El cuaderno descarga `facebook-links.txt.gz` y `facebook-wall.txt.gz` directamente del [conjunto WOSN 2009 de MPI-SWS](https://socialnetworks.mpi-sws.org/data-wosn2009.html), verifica sus sumas SHA-256 y reproduce las figuras y estadísticas. Los archivos de datos no se redistribuyen en este repositorio.

Los identificadores son anónimos y los datos históricos. Una amistad representa una conexión, no una interacción ni una cadena observada de republicaciones. Las publicaciones en muros tienen autor, destinatario y fecha, pero no permiten seguir un mismo contenido entre usuarios.

Para actualizar el código, modifica [`grafo_facebook.py`](grafo_facebook.py), ejecuta `python preparar_notebook_github.py` y publica los cambios con `git commit` y `git push`. Si cambió el código, el preparador limpia las salidas anteriores para evitar presentar resultados desactualizados. Puedes regenerar las figuras ejecutando el cuaderno en Colab y guardar una copia nueva en el repositorio. El enlace de GitHub conserva la misma dirección y muestra la versión publicada más reciente.
