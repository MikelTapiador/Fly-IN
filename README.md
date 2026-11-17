# Fly-in

Carga de mapas y herramientas de consola para probar los modelos, Dijkstra
y el planificador existentes. Requiere Python 3.10 o posterior; no añade
dependencias externas.

## Uso

Desde la raíz del repositorio:

```sh
python3 main.py maps/easy/01_linear_path.txt
python3 main.py maps/medium/02_circular_loop.txt --simulate
python3 main.py maps/hard/03_ultimate_challenge.txt --info-only --details
python3 main.py maps/challenger/01_the_impossible_dream.txt
python3 main.py --help
```

La operación predeterminada muestra los recuentos del grafo, START, END,
la ruta de Dijkstra para un dron y su tiempo sin congestión.

- `--info-only`: carga e inspecciona el mapa sin buscar rutas.
- `--details`: muestra coordenadas, tipos, colores y capacidades.
- `--simulate`: ejecuta `run_route`, que utiliza `plan_turn` y
  `simulate_turn`, sobre la única ruta obtenida con Dijkstra. Muestra
  posiciones por turno, incluidos los drones en tránsito.

Esta simulación utiliza el planificador voraz actual. No distribuye drones
entre rutas alternativas ni garantiza el menor número de turnos.
No se han sustituido ni ampliado los algoritmos existentes. Dijkstra no
incluye un criterio especial de preferencia por las zonas priority.

Los códigos de salida son 0 para una operación completada, 1 para un mapa
inválido o ilegible, un destino inalcanzable o una simulación detenida, y
2 para argumentos incorrectos. Los fallos de programación inesperados se
propagan para permitir su diagnóstico.

## API del parser

```python
from map_parser import MapParseError, parse_map

graph, nb_drones, start, end = parse_map("maps/easy/01_linear_path.txt")
```

`parse_map(map_path: str | Path) -> tuple[Graph, int, str, str]`
devuelve un `Graph` construido con los modelos existentes, el número de
drones y los nombres de las zonas inicial y final. No cambia los nombres
de las zonas ni añade metadatos al grafo.

Los errores de entrada producen `MapParseError`, una subclase de
`ValueError` con `filename`, `line_number` y `reason`. El mensaje incluye
ruta y línea cuando está disponible. Los datos obligatorios ausentes se
señalan al final del archivo; los errores de apertura no tienen línea.

## Formato admitido

El formato se ha contrastado con [la documentación de mapas](maps/README.md)
y los diez mapas suministrados. No hay un enunciado oficial en el repositorio.

```text
nb_drones: 2
start_hub: origin 0 0 [color=green]
hub: waypoint 1 -1 [zone=restricted color=orange max_drones=2]
end_hub: destination 2 0 [color=red]
connection: origin-waypoint [max_link_capacity=2]
connection: waypoint-destination
```

Se exige una única definición de `nb_drones`, `start_hub` y
`end_hub`. Los roles START y END dependen de estas directivas, no de
que las zonas tengan nombres concretos. Los nombres son tokens sin
espacios ni delimitadores del formato (`-`, `:`, `#`, `[`, `]`, `=`).

Los atributos de zona son `zone`, `color` y `max_drones`; el de conexión
es `max_link_capacity`. Los valores predeterminados son los de los modelos:
zona normal, capacidad de zona y de conexión de uno, y color ausente.
Los cuatro tipos admitidos son normal, restricted, priority y blocked.
El color se conserva como un token, sin imponer una paleta adicional.
Las conexiones son bidireccionales.

Se admiten líneas vacías, espacios y tabuladores, comentarios con `#`
fuera de los corchetes, atributos en cualquier orden, UTF-8 con o sin BOM
y finales de línea de Windows. Las definiciones pueden estar en cualquier
orden: las conexiones se resuelven una vez leídas todas las zonas.

Los modelos validan capacidades, tipos, duplicados y conexiones a uno mismo.
El parser valida la sintaxis, las directivas, los atributos y los roles
obligatorios, y añade el contexto del archivo a los errores.
No descarta líneas ni atributos desconocidos. Los archivos
`:Zone.Identifier` y su variante con separador U+F03A no se cargan como mapas.

Un mapa desconectado o con extremos bloqueados puede cargarse para
inspección. Dijkstra informa de que no existe una ruta transitable.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

La suite comprueba los diez mapas con recuentos, tipos y capacidades
esperados obtenidos directamente de sus archivos; también prueba errores
de formato, referencias, duplicados, codificación, comentarios y la CLI.
Ejecuta procesos reales para las cuatro categorías y comprueba la
integración con Dijkstra, el planificador y el simulador.
Los scripts de tests originales conservan sus aserciones al importarse.
