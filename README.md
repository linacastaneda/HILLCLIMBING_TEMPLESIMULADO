# HILLCLIMBING / TEMPLE SIMULADO — Puzzle 3x3 (8-puzzle)

Comparación entre **Ascenso de Colinas (HC)** y **Temple Simulado (TS)** para el puzzle 3x3, con funciones en español y gráficas en el código.

Archivo principal: `puzzle_colinas_temple.py`

## 1. Funciones en español

- `obtener_vecinos(estado)` — movimientos válidos (2 esquina, 3 borde, 4 centro)
- `es_solucionable(estado)` — inversiones pares
- `generar_estado_aleatorio(movs)` — mezcla desde la meta (siempre soluble)
- `distancia_manhattan(estado)` — heurística principal `h(n)`
- `fichas_descolocadas(estado)` — heurística secundaria
- `ascenso_colinas(inicio, ...)` — steepest descent + laterales (`sideways_limit=50`)
- `ascenso_colinas_reinicios(...)` — con 20 reinicios aleatorios
- `temple_simulado(inicio, T_inicial=2.0, alpha=0.99, ...)` — acepta peores con `exp(-delta/T)`
- `META / GOAL = (1,2,3,4,5,6,7,8,0)`

Gráficas en el código:
- `dibujar_tablero`, `graficar_camino`, `graficar_convergencia`
- `graficar_comparacion`, `graficar_enfriamiento`
- `estudiar_dificultad`, `graficar_escala_dificultad`, `simulacion_completa`

## 2. Uso

```bash
pip install matplotlib numpy
python puzzle_colinas_temple.py
```

Genera:
- `camino_hill_climbing.png`, `camino_temple_simulado.png`
- `convergencia_hc_vs_sa.png`
- `graficas_hc_vs_sa.png`
- `graficas_HC_TS_dificultad.png`

## 3. Datitos — comparación HC vs TS (30 partidas por nivel, Manhattan)

| Mezcla | HC éxito | HC tiempo | HC nodos | HC pasos* | TS éxito | TS tiempo | TS nodos | TS pasos* |
|---|---|---|---|---|---|---|---|---|
| 8 movs | 83.3% 25/30 | 0.045 ms | 9.9 | 3.3 | 70.0% 21/30 | 13.4 ms | 3029 | 26.9 |
| 12 movs | 93.3% 28/30 | 0.034 ms | 10.4 | 3.6 | 66.7% 20/30 | 16.5 ms | 3368 | 34.0 |
| 20 movs | 73.3% 22/30 | 0.067 ms | 14.2 | 5.7 | 40.0% 12/30 | 24.7 ms | 6015 | 27.0 |
| 30 movs | 46.7% 14/30 | 0.034 ms | 12.8 | 6.1 | 33.3% 10/30 | 24.7 ms | 6684 | 36.2 |

\* pasos solo de éxitos. Heurística `Ch ~1.59 microseg` por evaluación.

### Caminos encontrados

![Camino HC](img/camino_hill_climbing.png)
![Camino TS](img/camino_temple_simulado.png)

### Convergencia h(n)

![Convergencia](img/convergencia_hc_vs_sa.png)

HC baja directo en 2-6 pasos. TS sube y baja (acepta peores) y llega con 5x-8x más pasos.

### Comparación directa (10 partidas, 12 movs)

![Comparación](img/graficas_hc_vs_sa.png)

### Complejidad vs dificultad

![Dificultad](img/graficas_HC_TS_dificultad.png)

## 4. Complejidad computacional

Base: espacio total `9!/2 = 181440` estados. Ramificación `b = 2 a 4, promedio 2.67`.

- **HC:** Tiempo `O(d * b * Ch)` donde `d` = pasos hasta mínimo local, `b~2.67`, `Ch=O(1)`. Peor caso `O(max_iter*b)`. Espacio `O(d)` solo camino actual (4-6 nodos). Incompleto, no óptimo, se clava en mínimo local / meseta.
- **TS:** Tiempo `O(Nmax)` (1 vecino por iteración, `Nmax=10000`). Espacio `O(L)` trayectoria (60-200 nodos) o `O(1)` si solo actual+mejor. Probabilísticamente completo con enfriamiento lento, en la práctica incompleto pero escapa con `P=exp(-delta/T)`.

Empírico: HC ~0.03-0.06 ms, TS ~13-25 ms (300x-700x más lento, 300x-500x más nodos). Con `T0=20` TS daba 20% éxito, con `T0=2.0` sube a 70%.

## 5. Conclusiones

1. HC gana en fácil (12 movs: 93% vs 66%) porque es avaro y directo, rapidísimo y con caminos óptimos cortos.
2. Ambos caen con dificultad (30 movs: 46% vs 33%) — el paisaje Manhattan se llena de mínimos locales.
3. TS paga caro escapar: más tiempo, más nodos, caminos largos y torcidos, pero resuelve casos donde HC se atasca (ej. mínimo local con `h=6` que HC no sale y TS sí).
4. Para 3x3 cerca de la meta: HC. Para lejos o con mesetas: TS + reinicios. `ascenso_colinas_reinicios` da casi 100%.
5. Mejora pendiente: `T0` adaptativo, reheating y `random-restart` sistemático para TS.
