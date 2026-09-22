import random
import time
import math
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. LÓGICA DEL 8-PUZZLE 
# ==========================================
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
META = GOAL  # alias en español

def obtener_vecinos(state):
    """Genera los movimientos válidos desde un estado dado."""
    neighbors = []
    idx = state.index(0)
    row, col = divmod(idx, 3)

    moves = []
    if row > 0:
        moves.append(-3)  # Arriba
    if row < 2:
        moves.append(3)   # Abajo
    if col > 0:
        moves.append(-1)  # Izquierda
    if col < 2:
        moves.append(1)   # Derecha

    for m in moves:
        new_state = list(state)
        new_state[idx], new_state[idx + m] = new_state[idx + m], new_state[idx]
        neighbors.append(tuple(new_state))
    return neighbors

def es_solucionable(state):
    """Verifica si el puzzle tiene solución (inversiones pares)."""
    inv = 0
    s = [x for x in state if x != 0]
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            if s[i] > s[j]:
                inv += 1
    return inv % 2 == 0

def generar_estado_aleatorio(moves=10):
    """Genera un estado inicial aleatorio con N movimientos desde la meta."""
    state = GOAL
    for _ in range(moves):
        state = random.choice(obtener_vecinos(state))
    return state

# ==========================================
# 2. HEURÍSTICAS
# ==========================================

def distancia_manhattan(state):
    """Distancia Manhattan: suma de distancias de cada ficha a su meta."""
    dist = 0
    for idx, val in enumerate(state):
        if val == 0:
            continue
        goal_idx = val - 1
        r1, c1 = divmod(idx, 3)
        r2, c2 = divmod(goal_idx, 3)
        dist += abs(r1 - r2) + abs(c1 - c2)
    return dist

def fichas_descolocadas(state):
    """Fichas fuera de lugar (sin contar el hueco)."""
    return sum(1 for i, v in enumerate(state) if v != 0 and v != GOAL[i])

# ==========================================
# 3. ASCENSO DE COLINAS (HILL CLIMBING)
# ==========================================

def ascenso_colinas(start_state, heuristic_fn=distancia_manhattan, max_iter=5000, sideways_limit=50):
    """Ascenso de colinas de máximo descenso (steepest descent).

    En cada paso evalúa todos los vecinos y se mueve al mejor.
    Si ningún vecino mejora, se declara mínimo local / meseta.

    Retorna dict con métricas: exito, time, nodes, path, historial_h, motivo.
    """
    start_time = time.time()
    current = start_state
    current_h = heuristic_fn(current)
    path = [current]
    historial_h = [current_h]
    nodos_evaluados = 0
    sideways_usados = 0
    motivo = "max_iter"

    if current == GOAL:
        return {
            "exito": True,
            "time": time.time() - start_time,
            "nodes": 0,
            "path": path,
            "path_len": 0,
            "memory": len(path),
            "historial_h": historial_h,
            "motivo": "ya_en_meta",
            "h_final": 0,
        }

    for _ in range(max_iter):
        if current == GOAL:
            motivo = "meta_alcanzada"
            break
        vecinos = obtener_vecinos(current)
        nodos_evaluados += len(vecinos)
        evaluados = [(heuristic_fn(v), v) for v in vecinos]
        mejor_h = min(h for h, _ in evaluados)
        candidatos = [v for h, v in evaluados if h == mejor_h]
        mejor_estado = random.choice(candidatos)

        if mejor_h < current_h:
            current = mejor_estado
            current_h = mejor_h
            sideways_usados = 0
        elif mejor_h == current_h and sideways_usados < sideways_limit:
            # Movimiento lateral para cruzar mesetas
            current = mejor_estado
            sideways_usados += 1
        else:
            if mejor_h == current_h:
                motivo = "meseta (límite lateral superado)"
            else:
                motivo = "mínimo local"
            break

        path.append(current)
        historial_h.append(current_h)
    else:
        motivo = "max_iter alcanzado"

    exito = (current == GOAL)
    if exito:
        motivo = "meta_alcanzada"

    return {
        "exito": exito,
        "time": time.time() - start_time,
        "nodes": nodos_evaluados,
        "path": path,
        "path_len": (len(path) - 1) if exito else None,
        "memory": len(path),
        "historial_h": historial_h,
        "motivo": motivo,
        "h_final": current_h,
    }

def ascenso_colinas_reinicios(start_state, heuristic_fn=distancia_manhattan, restarts=20,
                           max_iter=500, sideways_limit=30):
    """Hill Climbing con reinicios aleatorios.

    Si se atasca, genera un estado aleatorio nuevo y reintenta.
    Útil porque el 8-puzzle está lleno de mínimos locales.
    """
    start_time = time.time()
    mejor_global = None
    nodos_total = 0
    intentos = 0

    # Intento 1: desde el estado dado
    res = ascenso_colinas(start_state, heuristic_fn, max_iter, sideways_limit)
    nodos_total += res["nodes"]
    intentos += 1
    if res["exito"]:
        res["restarts_usados"] = 0
        res["time"] = time.time() - start_time
        return res
    mejor_global = res

    for r in range(1, restarts + 1):
        aleatorio = generar_estado_aleatorio(moves=random.randint(10, 25))
        res2 = ascenso_colinas(aleatorio, heuristic_fn, max_iter, sideways_limit)
        nodos_total += res2["nodes"]
        intentos += 1
        if res2["exito"]:
            res2["restarts_usados"] = r
            res2["time"] = time.time() - start_time
            res2["nodes"] = nodos_total
            return res2
        if res2["h_final"] < mejor_global["h_final"]:
            mejor_global = res2

    mejor_global["restarts_usados"] = restarts
    mejor_global["time"] = time.time() - start_time
    mejor_global["nodes"] = nodos_total
    mejor_global["intentos"] = intentos
    return mejor_global

# ==========================================
# 4. TEMPLE SIMULADO (SIMULATED ANNEALING)
# ==========================================

def temple_simulado(start_state, heuristic_fn=distancia_manhattan,
                        T_inicial=2.0, alpha=0.99, T_min=0.001,
                        max_iter=10000, semilla=None):
    """Temple simulado para 8-puzzle.

    - Elige un vecino al azar en cada iteración.
    - Si mejora (delta < 0), lo acepta siempre.
    - Si empeora, lo acepta con prob exp(-delta / T).
    - Enfría con T = T_inicial * alpha^iter.

    Retorna dict con métricas + historial_h e historial_T.
    """
    if semilla is not None:
        random.seed(semilla)
    start_time = time.time()

    current = start_state
    current_h = heuristic_fn(current)
    mejor = current
    mejor_h = current_h

    trayectoria = [current]
    historial_h = [current_h]
    historial_T = [T_inicial]
    nodos_evaluados = 0

    if current == GOAL:
        return {
            "exito": True,
            "time": time.time() - start_time,
            "nodes": 0,
            "path": trayectoria,
            "path_len": 0,
            "memory": len(trayectoria),
            "historial_h": historial_h,
            "historial_T": historial_T,
            "h_final": 0,
            "mejor_h": 0,
        }

    for k in range(max_iter):
        T = max(T_min, T_inicial * (alpha ** k))
        if current == GOAL:
            break
        vecinos = obtener_vecinos(current)
        nodos_evaluados += 1  # solo se evalúa 1 vecino por iteración
        siguiente = random.choice(vecinos)
        siguiente_h = heuristic_fn(siguiente)
        delta = siguiente_h - current_h

        acepta = False
        if delta < 0:
            acepta = True
        else:
            prob = math.exp(-delta / T) if T > 0 else 0.0
            if random.random() < prob:
                acepta = True

        if acepta:
            current = siguiente
            current_h = siguiente_h
            trayectoria.append(current)

        if current_h < mejor_h:
            mejor = current
            mejor_h = current_h

        historial_h.append(current_h)
        historial_T.append(T)

        if mejor_h == 0:
            current = mejor
            current_h = 0
            break

    exito = (mejor_h == 0)
    # Si tuvo éxito, la trayectoria real termina en la meta (mejor)
    # Para visualizar el camino que llevó al éxito usamos la trayectoria.
    return {
        "exito": exito,
        "time": time.time() - start_time,
        "nodes": nodos_evaluados,
        "path": trayectoria if exito else trayectoria,
        "path_len": (len(trayectoria) - 1) if exito else None,
        "memory": len(trayectoria),
        "historial_h": historial_h,
        "historial_T": historial_T,
        "h_final": current_h,
        "mejor_h": mejor_h,
    }

# ==========================================
# 5. VISUALIZACIÓN DE TABLEROS
# ==========================================

def dibujar_tablero(ax, state, title=""):
    """Dibuja un tablero 3x3 en un eje de matplotlib."""
    if state is None:
        ax.axis('off')
        ax.text(0.5, 0.5, '...', fontsize=30, ha='center', va='center')
        return

    grid = np.array(state).reshape(3, 3)
    ax.matshow(np.zeros((3, 3)), cmap='Blues', alpha=0.1)

    for i in range(3):
        for j in range(3):
            val = grid[i, j]
            if val != 0:
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                     facecolor='lightgray', edgecolor='black', linewidth=2)
                ax.add_patch(rect)
                ax.text(j, i, str(val), va='center', ha='center',
                        fontsize=20, fontweight='bold', color='black')
            else:
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                     facecolor='white', edgecolor='gray', linewidth=1)
                ax.add_patch(rect)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, pad=10, fontsize=12)

def graficar_camino(path, algo_name, max_displays=8):
    """Dibuja la secuencia de movimientos. Si es muy larga, inicio + final."""
    if path is None or len(path) == 0:
        print(f"No hay camino para mostrar con {algo_name}")
        return

    if len(path) > max_displays:
        display_path = path[:4] + [None] + path[-3:]
        indices = list(range(4)) + [None] + list(range(len(path) - 3, len(path)))
    else:
        display_path = path
        indices = list(range(len(path)))

    fig, axes = plt.subplots(1, len(display_path), figsize=(3.5 * len(display_path), 4))
    if len(display_path) == 1:
        axes = [axes]

    total = len(path) - 1
    fig.suptitle(f'Solución usando {algo_name} (Total: {total} pasos)',
                 fontsize=14, y=1.12)

    for ax, state, step_idx in zip(axes, display_path, indices):
        if state is None:
            dibujar_tablero(ax, None)
        else:
            if step_idx == 0:
                title = "Estado Inicial"
            elif step_idx == len(path) - 1:
                title = "¡META!"
            else:
                title = f"Paso {step_idx}"
            dibujar_tablero(ax, state, title)

    plt.tight_layout()
    plt.savefig(f'camino_{algo_name.replace(" ", "_").lower()}.png', dpi=200, bbox_inches='tight')
    print(f"Camino guardado como 'camino_{algo_name.replace(' ', '_').lower()}.png'")
    plt.show()

def graficar_convergencia(hist_hc, hist_sa):
    """Compara la caída de la heurística h(n) en ambos algoritmos."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hist_hc, label='Hill Climbing (h)', linewidth=2)
    ax.plot(hist_sa, label='Temple Simulado (h)', linewidth=2, alpha=0.85)
    ax.set_xlabel('Iteración')
    ax.set_ylabel('Heurística Manhattan h(n)')
    ax.set_title('Convergencia: h(n) vs iteración')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('convergencia_hc_vs_sa.png', dpi=300)
    print("Gráfica guardada como 'convergencia_hc_vs_sa.png'")
    plt.show()

def graficar_comparacion(hc_metrics, sa_metrics):
    """Genera gráficas de comparación HC vs SA."""
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Comparación Hill Climbing vs Temple Simulado', fontsize=16)
    labels = ['Hill Climbing', 'Temple Sim.']

    def plot_bar(ax, data_hc, data_sa, title, ylabel, color1='skyblue', color2='salmon'):
        means = [np.mean(data_hc) if len(data_hc) > 0 else 0,
                 np.mean(data_sa) if len(data_sa) > 0 else 0]
        ax.bar(labels, means, color=[color1, color2])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        for i, v in enumerate(means):
            ax.text(i, v + (max(means) * 0.02 + 1e-9), str(round(float(v), 2)),
                    ha='center', va='bottom', fontweight='bold')

    # Tasa de éxito (%) — métrica clave en búsqueda local
    plot_bar(axs[0, 0], hc_metrics["exito"], sa_metrics["exito"],
             'Tasa de Éxito (llegó a la meta)', '% (1=éxito, 0=fallo)')
    plot_bar(axs[0, 1], hc_metrics["time"], sa_metrics["time"],
             'Costo Temporal Real (Tiempo CPU)', 'Segundos')
    # Pasos solo de los éxitos para no mezclar con None
    hc_pasos = [x for x in hc_metrics["path_len"] if x is not None]
    sa_pasos = [x for x in sa_metrics["path_len"] if x is not None]
    if not hc_pasos:
        hc_pasos = [0]
    if not sa_pasos:
        sa_pasos = [0]
    plot_bar(axs[1, 0], hc_pasos, sa_pasos,
             'Calidad de la Solución (Pasos, solo éxitos)', 'Movimientos')
    plot_bar(axs[1, 1], hc_metrics["nodes"], sa_metrics["nodes"],
             'Nodos Evaluados', 'Cantidad')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('graficas_hc_vs_sa.png', dpi=300)
    print("Gráfica guardada exitosamente como 'graficas_hc_vs_sa.png'")
    plt.show()

def graficar_enfriamiento(historial_T, historial_h):
    """Gráfica dual: temperatura T(k) + heurística h(n) del Temple Simulado."""
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(historial_T, color='red', linewidth=2, label='Temperatura T(k)')
    ax1.set_xlabel('Iteración k')
    ax1.set_ylabel('Temperatura T', color='red')
    ax1.tick_params(axis='y', labelcolor='red')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(historial_h, color='blue', linewidth=1.5, alpha=0.8, label='h Manhattan')
    ax2.set_ylabel('h(n) Manhattan', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')

    plt.title('Temple Simulado: Enfriamiento T(k)=T0*alpha^k vs h(n)')
    fig.tight_layout()
    plt.savefig('temple_enfriamiento.png', dpi=300)
    print("Gráfica guardada como 'temple_enfriamiento.png'")
    plt.show()

# ==========================================
# 6. ESTUDIO POR DIFICULTAD Y COMPLEJIDAD
# ==========================================

def estudiar_dificultad(levels=(8, 12, 20, 30), trials=30, semilla=123):
    """Comparación HC vs TS barriendo dificultad (movs de mezcla).

    Complejidad empírica: mide éxito, tiempo, nodos y pasos vs dificultad.
    Retorna dict {nivel: {'hc': metrics, 'sa': metrics}} e imprime tabla.
    """
    print("=" * 70)
    print("ESTUDIO DE DIFICULTAD + COMPLEJIDAD: HC vs TS (3x3)")
    print(f"Niveles={levels}, trials={trials} por nivel, heurística=Manhattan")
    print("=" * 70)
    random.seed(semilla)
    estudio = {}
    print(f"{'Nivel':<8}{'HC%':<8}{'HC ms':<10}{'HC nod':<10}{'HC pas':<8}| "
          f"{'TS%':<8}{'TS ms':<10}{'TS nod':<10}{'TS pas':<8}")
    print("-" * 90)
    for sc in levels:
        tests = [generar_estado_aleatorio(sc) for _ in range(trials)]
        hc_m = {"exito": [], "time": [], "nodes": [], "path_len": []}
        sa_m = {"exito": [], "time": [], "nodes": [], "path_len": []}
        for s in tests:
            r = ascenso_colinas(s, heuristic_fn=distancia_manhattan)
            hc_m["exito"].append(1 if r["exito"] else 0)
            hc_m["time"].append(r["time"])
            hc_m["nodes"].append(r["nodes"])
            hc_m["path_len"].append(r["path_len"])
            r2 = temple_simulado(s, heuristic_fn=distancia_manhattan)
            sa_m["exito"].append(1 if r2["exito"] else 0)
            sa_m["time"].append(r2["time"])
            sa_m["nodes"].append(r2["nodes"])
            sa_m["path_len"].append(r2["path_len"])
        estudio[sc] = {"hc": hc_m, "sa": sa_m}
        hc_p = [x for x in hc_m["path_len"] if x is not None]
        sa_p = [x for x in sa_m["path_len"] if x is not None]
        print(f"{sc:<8}{np.mean(hc_m['exito'])*100:<8.1f}"
              f"{np.mean(hc_m['time'])*1000:<10.3f}{np.mean(hc_m['nodes']):<10.1f}"
              f"{(np.mean(hc_p) if hc_p else 0):<8.1f}| "
              f"{np.mean(sa_m['exito'])*100:<8.1f}"
              f"{np.mean(sa_m['time'])*1000:<10.3f}{np.mean(sa_m['nodes']):<10.1f}"
              f"{(np.mean(sa_p) if sa_p else 0):<8.1f}")
    print("-" * 90)
    print("Teórica: HC O(d*b) tiempo, O(d) espacio. TS O(Nmax) tiempo, O(L) espacio.")
    print("b~2.67 (2 esquina, 3 borde, 4 centro). Espacio total 9!/2=181440.")
    return estudio

def graficar_escala_dificultad(estudio):
    """4 gráficas de complejidad empírica vs dificultad. Guarda PNG."""
    niveles = sorted(estudio.keys())
    hc_ok = [np.mean(estudio[n]["hc"]["exito"]) * 100 for n in niveles]
    sa_ok = [np.mean(estudio[n]["sa"]["exito"]) * 100 for n in niveles]
    hc_t = [np.mean(estudio[n]["hc"]["time"]) * 1000 for n in niveles]
    sa_t = [np.mean(estudio[n]["sa"]["time"]) * 1000 for n in niveles]
    hc_n = [np.mean(estudio[n]["hc"]["nodes"]) for n in niveles]
    sa_n = [np.mean(estudio[n]["sa"]["nodes"]) for n in niveles]
    hc_p = []
    sa_p = []
    for n in niveles:
        a = [x for x in estudio[n]["hc"]["path_len"] if x is not None]
        b = [x for x in estudio[n]["sa"]["path_len"] if x is not None]
        hc_p.append(np.mean(a) if a else 0)
        sa_p.append(np.mean(b) if b else 0)

    fig, axs = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle('HC vs TS 3x3: Complejidad vs Dificultad (movs de mezcla)', fontsize=15)

    axs[0, 0].plot(niveles, hc_ok, 'o-', label='Hill Climbing', linewidth=2)
    axs[0, 0].plot(niveles, sa_ok, 's-', label='Temple Simulado', linewidth=2)
    axs[0, 0].set_title('Tasa de éxito (%) vs dificultad')
    axs[0, 0].set_xlabel('Movs de mezcla (dificultad)')
    axs[0, 0].set_ylabel('% éxito')
    axs[0, 0].legend()
    axs[0, 0].grid(True, alpha=0.3)

    axs[0, 1].plot(niveles, hc_t, 'o-', label='HC', linewidth=2)
    axs[0, 1].plot(niveles, sa_t, 's-', label='TS', linewidth=2)
    axs[0, 1].set_title('Tiempo medio (ms, log) vs dificultad')
    axs[0, 1].set_xlabel('Movs de mezcla')
    axs[0, 1].set_ylabel('ms (log)')
    axs[0, 1].set_yscale('log')
    axs[0, 1].legend()
    axs[0, 1].grid(True, which='both', alpha=0.3)

    axs[1, 0].plot(niveles, hc_n, 'o-', label='HC O(d*b)', linewidth=2)
    axs[1, 0].plot(niveles, sa_n, 's-', label='TS O(Nmax)', linewidth=2)
    axs[1, 0].set_title('Nodos evaluados (log) vs dificultad')
    axs[1, 0].set_xlabel('Movs de mezcla')
    axs[1, 0].set_ylabel('nodos (log)')
    axs[1, 0].set_yscale('log')
    axs[1, 0].legend()
    axs[1, 0].grid(True, which='both', alpha=0.3)

    axs[1, 1].plot(niveles, hc_p, 'o-', label='HC pasos', linewidth=2)
    axs[1, 1].plot(niveles, sa_p, 's-', label='TS pasos', linewidth=2)
    axs[1, 1].set_title('Calidad solución (pasos, solo éxitos) vs dificultad')
    axs[1, 1].set_xlabel('Movs de mezcla')
    axs[1, 1].set_ylabel('pasos')
    axs[1, 1].legend()
    axs[1, 1].grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('graficas_HC_TS_dificultad.png', dpi=300)
    print("Gráfica guardada como 'graficas_HC_TS_dificultad.png'")
    plt.show()

# ==========================================
# 7. EJECUCIÓN PRINCIPAL
# ==========================================

def simulacion_completa(trials=10, scramble_demo=8, scramble_trials=12):
    """Ejecuta demo visual + análisis de complejidad HC vs SA."""
    print("=" * 60)
    print("SIMULACIÓN 8-PUZZLE: ASCENSO DE COLINAS vs TEMPLE SIMULADO")
    print(f"(Heurística: Manhattan. Demo={scramble_demo} movs, trials={scramble_trials} movs)")
    print("=" * 60)

    # --- 1. Demo visual con un estado aleatorio ---
    print("\n1. VISUALIZACIÓN DE CAMINOS (estado aleatorio)")
    print("-" * 40)
    estado_prueba = generar_estado_aleatorio(moves=scramble_demo)
    print(f"Estado inicial: {estado_prueba}")
    print(f"h(Manhattan) inicial = {distancia_manhattan(estado_prueba)}, "
          f"h(fichas_descolocadas) = {fichas_descolocadas(estado_prueba)}")

    print("\nCalculando con Hill Climbing...")
    hc_demo = ascenso_colinas(estado_prueba, heuristic_fn=distancia_manhattan)
    print(f"  HC: exito={hc_demo['exito']}, motivo={hc_demo['motivo']}, "
          f"pasos={hc_demo['path_len']}, nodos={hc_demo['nodes']}, "
          f"tiempo={hc_demo['time']:.4f}s, h_final={hc_demo['h_final']}")
    graficar_camino(hc_demo["path"][:9] if not hc_demo["exito"] else hc_demo["path"],
                   "Hill Climbing")

    print("\nCalculando con Temple Simulado...")
    sa_demo = temple_simulado(estado_prueba, heuristic_fn=distancia_manhattan)
    print(f"  SA: exito={sa_demo['exito']}, pasos={sa_demo['path_len']}, "
          f"nodos={sa_demo['nodes']}, tiempo={sa_demo['time']:.4f}s, "
          f"mejor_h={sa_demo['mejor_h']}")
    graficar_camino(sa_demo["path"], "Temple Simulado")

    print("\nGraficando convergencia del demo...")
    graficar_convergencia(hc_demo["historial_h"], sa_demo["historial_h"])

    # --- 2. Análisis de complejidad ---
    print("\n2. ANÁLISIS DE COMPLEJIDAD")
    print("-" * 40)
    hc_metrics = {"exito": [], "time": [], "nodes": [], "path_len": [], "memory": []}
    sa_metrics = {"exito": [], "time": [], "nodes": [], "path_len": [], "memory": []}

    for i in range(trials):
        initial = generar_estado_aleatorio(moves=scramble_trials)
        print(f"\nPartida {i+1}: inicial = {initial} (h={distancia_manhattan(initial)})")

        r_hc = ascenso_colinas(initial, heuristic_fn=distancia_manhattan)
        hc_metrics["exito"].append(1 if r_hc["exito"] else 0)
        hc_metrics["time"].append(r_hc["time"])
        hc_metrics["nodes"].append(r_hc["nodes"])
        hc_metrics["path_len"].append(r_hc["path_len"])
        hc_metrics["memory"].append(r_hc["memory"])
        print(f"  HC: exito={r_hc['exito']} ({r_hc['motivo']}), "
              f"pasos={r_hc['path_len']}, nodos={r_hc['nodes']}, t={r_hc['time']:.4f}s")

        r_sa = temple_simulado(initial, heuristic_fn=distancia_manhattan)
        sa_metrics["exito"].append(1 if r_sa["exito"] else 0)
        sa_metrics["time"].append(r_sa["time"])
        sa_metrics["nodes"].append(r_sa["nodes"])
        sa_metrics["path_len"].append(r_sa["path_len"])
        sa_metrics["memory"].append(r_sa["memory"])
        print(f"  SA: exito={r_sa['exito']}, pasos={r_sa['path_len']}, "
              f"nodos={r_sa['nodes']}, t={r_sa['time']:.4f}s")

    print("\n" + "=" * 40)
    print("RESUMEN DE RESULTADOS")
    print("=" * 40)
    print(f"HC - Éxito: {np.mean(hc_metrics['exito'])*100:.1f}%, "
          f"Tiempo: {np.mean(hc_metrics['time']):.4f}s, "
          f"Nodos: {np.mean(hc_metrics['nodes']):.1f}, "
          f"Memoria: {np.mean(hc_metrics['memory']):.1f}")
    print(f"SA - Éxito: {np.mean(sa_metrics['exito'])*100:.1f}%, "
          f"Tiempo: {np.mean(sa_metrics['time']):.4f}s, "
          f"Nodos: {np.mean(sa_metrics['nodes']):.1f}, "
          f"Memoria: {np.mean(sa_metrics['memory']):.1f}")

    print("\n3. GENERANDO GRÁFICAS DE COMPARACIÓN")
    print("-" * 40)
    graficar_comparacion(hc_metrics, sa_metrics)

    print("\n" + "=" * 60)
    print("SIMULACIÓN COMPLETADA")
    print("HC es rápido pero se atasca en mínimos locales; "
          "SA escapa con movimientos peores y suele tener mayor éxito.")
    print("=" * 60)


if __name__ == "__main__":
    random.seed(42)
    simulacion_completa()
