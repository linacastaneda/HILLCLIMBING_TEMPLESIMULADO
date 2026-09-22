# Comparación experimental: Ascenso de Colinas vs Temple Simulado

Comparación de **Ascenso de Colinas (HC)** y **Temple Simulado (TS)** para el puzle 3 × 3. Se usa búsqueda local con estado, vecindad y función de costo `f(s)`.

Archivo principal: `puzzle_colinas_temple.py` · Requiere `Python 3.10+`, `numpy`, `matplotlib`.

Piezas del repo: `META`, `obtener_vecinos()`, `generar_estado_aleatorio()`, `costo()`, `ascenso_colinas()`, `temple_simulado()`, `experimento()`, `graficar_comparacion()`, `main`.

## 1. Modelo de clase

Estado: tupla de 9 `(1,2,3,4,5,6,7,8,0)`, `0` es el hueco. Meta `META = (1,2,3,4,5,6,7,8,0)`. Vecindad `obtener_vecinos(s)`: mover el hueco si es legal. Ramificación `b = 2 esquina, 3 borde, 4 centro, promedio 2.67`. Espacio soluble `9!/2 = 181440`. `generar_estado_aleatorio(movs)` mezcla desde `META`, siempre soluble.

Función objetivo:

```python
def costo(estado):
    return sum(
        1 for i, ficha in enumerate(estado)
        if ficha != 0 and ficha != META[i]
    )
```

`f(s) = 0` es meta. A menor costo, mejor aptitud. Es conteo directo de desajuste, sin heurística Manhattan, sin admisibilidad ni consistencia: solo calidad de solución como piden las diapositivas.

## 2. Algoritmos

**`ascenso_colinas(estado_inicial, max_iter=5000)` base:**

```python
costo_mejor, mejor = min(
    ((costo(vecino), vecino) for vecino in vecinos),
    key=lambda candidato: candidato[0],
)
if costo_mejor >= costo_actual:
    break
```

Evalúa vecinos, escoge el mejor y se detiene si no hay mejora. La meseta se deja como limitación, sin `sideways_limit`: si todos empatan o empeoran, retorna `minimo_local_o_meseta`. Sin reinicios en la comparación principal.

**`temple_simulado(estado_inicial, T_inicial=2.0, alpha=0.99, T_min=0.001, max_iter=10000)`:**

```
Delta E = f(s') - f(s)
si Delta E <= 0: aceptar
si no: P = exp(-DeltaE / T), T = T_inicial * alpha^k
```

Un vecino por iteración. Nombres de costo: `costo_actual`, `costo_siguiente`, `mejor_costo`, `historial_costo`. La regla coincide con clase.

## 3. Experimento

`experimento(niveles=(8,12,20,30), trials=30, semilla=123)` mide éxito, tiempo, soluciones evaluadas y pasos según los movimientos de mezcla. Los resultados de cada algoritmo usan la clave `"evaluaciones"`. `graficar_comparacion(estudio)` genera `img/graficas_HC_TS_dificultad.png`. `main()` corre ambos.

```bash
pip install matplotlib numpy
python puzzle_colinas_temple.py
```

## 4. Resultados con función costo (30 partidas por nivel)

| Movimientos de mezcla | HC éxito | HC tiempo | HC evaluaciones | HC pasos* | TS éxito | TS tiempo | TS evaluaciones | TS pasos* |
|---|---|---|---|---|---|---|---|---|
| 8 | 70.0% | 0.023 ms | 8.2 | 3.0 | 60.0% | 12.1 ms | 4016.4 | 19.4 |
| 12 | 60.0% | 0.027 ms | 8.6 | 3.8 | 50.0% | 17.6 ms | 5018.4 | 27.9 |
| 20 | 60.0% | 0.022 ms | 7.9 | 3.6 | 66.7% | 11.0 ms | 3359.6 | 31.6 |
| 30 | 20.0% | 0.033 ms | 6.7 | 5.0 | 33.3% | 28.5 ms | 6680.8 | 34.2 |

\* Pasos solo en éxitos. Los tiempos son una ejecución de ejemplo y dependen del equipo; las demás cifras se reproducen con la semilla indicada.

![Comparación](img/graficas_HC_TS_dificultad.png)

Con esta función de costo, que produce muchos empates, HC obtiene más éxitos en 8 y 12 movimientos de mezcla; TS obtiene más en 20 y 30. TS evalúa miles de soluciones donde HC evalúa menos de diez en promedio. Estos niveles indican cuántos movimientos aleatorios se aplicaron desde la meta; un movimiento puede deshacer el anterior, así que no representan la distancia mínima a la solución.

## 5. Complejidad

En número de evaluaciones de la función de costo:

```
HC = O(k*b)
TS = O(k)
```

`k` es el número de iteraciones de cada algoritmo y `b` el número de vecinos de un estado. HC evalúa hasta `b` vecinos por iteración; TS evalúa uno. En el puzle 3 × 3, `b` está entre 2 y 4 y evaluar `costo()` cuesta `O(1)` respecto a `k`, por lo que ambos son `O(k)` si el tamaño del tablero se mantiene fijo. La implementación de TS construye la lista completa de vecinos antes de elegir uno; su costo de generación es `O(k*b)`. Los valores de `k` pueden ser muy distintos entre HC y TS, como muestran las evaluaciones medidas. Ambos conservan un historial de hasta `k` estados, por lo que su espacio registrado es `O(k)`.

## 6. Conclusiones

1. Con `f(s)` simple, ninguno domina la tasa de éxito en todos los niveles. HC requiere muchas menos evaluaciones y tiempo en esta ejecución.
2. La meseta es una limitación de HC base: sin movimientos laterales, se detiene cuando `costo_mejor >= costo_actual` aunque no haya alcanzado la meta.
3. TS acepta siempre las mejoras y empates; puede aceptar empeoramientos con `P=exp(-DeltaE/T)`. Esto le permite salir de algunas mesetas, aunque sus trayectorias aceptadas son más largas.
4. En esta muestra, ambos pierden éxito al pasar de 20 a 30 movimientos de mezcla. Conviene comparar más semillas antes de sacar una conclusión general.
5. Siguiente paso según diapositivas: variante con reinicios separada, no dentro del base, y `T0` adaptativo a `f` inicial.
