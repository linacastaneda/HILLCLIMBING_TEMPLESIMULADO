import random
import time
import math
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 8-PUZZLE 3x3 - Búsqueda local por costo
# Enfoque de clase: estado, vecindad y
# calidad/aptitud f(s). Sin heurística Manhattan.
# ==========================================
META = (1, 2, 3, 4, 5, 6, 7, 8, 0)
GOAL = META  # compatibilidad


def obtener_vecinos(estado):
    """Vecindad: mover el hueco (0) arriba/abajo/izquierda/derecha."""
    vecinos = []
    idx = estado.index(0)
    fila, col = divmod(idx, 3)
    movimientos = []
    if fila > 0:
        movimientos.append(-3)
    if fila < 2:
        movimientos.append(3)
    if col > 0:
        movimientos.append(-1)
    if col < 2:
        movimientos.append(1)
    for m in movimientos:
        nuevo = list(estado)
        nuevo[idx], nuevo[idx + m] = nuevo[idx + m], nuevo[idx]
        vecinos.append(tuple(nuevo))
    return vecinos


def generar_estado_aleatorio(movs=10):
    """Mezcla desde META con N pasos aleatorios (siempre soluble)."""
    estado = META
    for _ in range(movs):
        estado = random.choice(obtener_vecinos(estado))
    return estado


def costo(estado):
    """Función objetivo f(s): fichas fuera de lugar sin contar el hueco.

    f(s) = 0 es la meta. A menor costo, mejor calidad/aptitud.
    """
    return sum(1 for i, ficha in enumerate(estado) if ficha != 0 and ficha != META[i])


def ascenso_colinas(estado_inicial, max_iter=5000):
    """Ascenso de colinas base (diapositivas).

    Evaluar vecinos, escoger el mejor y detenerse si no hay mejora.
    La meseta es una limitación: no se resuelve con laterales aquí.
    """
    inicio = time.time()
    actual = estado_inicial
    costo_actual = costo(actual)
    camino = [actual]
    historial_costo = [costo_actual]
    nodos_evaluados = 0
    motivo = "max_iter"

    if actual == META:
        return {
            "exito": True,
            "tiempo": time.time() - inicio,
            "nodos": 0,
            "pasos": 0,
            "camino": camino,
            "historial_costo": historial_costo,
            "motivo": "ya_en_meta",
            "costo_final": 0,
        }

    for _ in range(max_iter):
        if actual == META:
            motivo = "meta_alcanzada"
            break
        vecinos = obtener_vecinos(actual)
        nodos_evaluados += len(vecinos)
        mejor = min(vecinos, key=costo)
        if costo(mejor) >= costo_actual:
            motivo = "minimo_local_o_meseta"
            break
        actual = mejor
        costo_actual = costo(actual)
        camino.append(actual)
        historial_costo.append(costo_actual)

    exito = (actual == META)
    if exito:
        motivo = "meta_alcanzada"
    return {
        "exito": exito,
        "tiempo": time.time() - inicio,
        "nodos": nodos_evaluados,
        "pasos": (len(camino) - 1) if exito else None,
        "camino": camino,
        "historial_costo": historial_costo,
        "motivo": motivo,
        "costo_final": costo_actual,
    }


def temple_simulado(estado_inicial, T_inicial=2.0, alpha=0.99, T_min=0.001,
                     max_iter=10000, semilla=None):
    """Temple simulado con función de costo f(s).

    Delta E = f(s') - f(s). Si mejora se acepta.
    Si empeora se acepta con P = exp(-DeltaE / T).
    Enfría con T = T_inicial * alpha^k.
    """
    if semilla is not None:
        random.seed(semilla)
    inicio = time.time()
    actual = estado_inicial
    costo_actual = costo(actual)
    mejor = actual
    mejor_costo = costo_actual
    trayectoria = [actual]
    historial_costo = [costo_actual]
    historial_T = [T_inicial]
    nodos_evaluados = 0

    if actual == META:
        return {
            "exito": True,
            "tiempo": time.time() - inicio,
            "nodos": 0,
            "pasos": 0,
            "camino": trayectoria,
            "historial_costo": historial_costo,
            "historial_T": historial_T,
            "costo_final": 0,
            "mejor_costo": 0,
        }

    for k in range(max_iter):
        T = max(T_min, T_inicial * (alpha ** k))
        if actual == META:
            break
        vecinos = obtener_vecinos(actual)
        nodos_evaluados += 1
        siguiente = random.choice(vecinos)
        costo_siguiente = costo(siguiente)
        delta_E = costo_siguiente - costo_actual
        acepta = False
        if delta_E < 0:
            acepta = True
        else:
            prob = math.exp(-delta_E / T) if T > 0 else 0.0
            if random.random() < prob:
                acepta = True
        if acepta:
            actual = siguiente
            costo_actual = costo_siguiente
            trayectoria.append(actual)
        if costo_actual < mejor_costo:
            mejor = actual
            mejor_costo = costo_actual
        historial_costo.append(costo_actual)
        historial_T.append(T)
        if mejor_costo == 0:
            break

    exito = (mejor_costo == 0)
    return {
        "exito": exito,
        "tiempo": time.time() - inicio,
        "nodos": nodos_evaluados,
        "pasos": (len(trayectoria) - 1) if exito else None,
        "camino": trayectoria,
        "historial_costo": historial_costo,
        "historial_T": historial_T,
        "costo_final": costo_actual,
        "mejor_costo": mejor_costo,
    }


def experimento(niveles=(8, 12, 20, 30), trials=30, semilla=123):
    """Comparación HC vs TS barriendo dificultad.

    Complejidad empírica: éxito, tiempo, nodos y pasos vs mezcla.
    HC = O(k*b), TS = O(k) con un vecino por iteración.
    """
    print("=" * 70)
    print("EXPERIMENTO HC vs TS (3x3) - función costo f(s)")
    print(f"Niveles={niveles}, trials={trials}")
    print("=" * 70)
    random.seed(semilla)
    estudio = {}
    print(f"{'Nivel':<8}{'HC%':<8}{'HC ms':<10}{'HC nod':<10}{'HC pas':<8}| "
          f"{'TS%':<8}{'TS ms':<10}{'TS nod':<10}{'TS pas':<8}")
    print("-" * 90)
    for sc in niveles:
        pruebas = [generar_estado_aleatorio(sc) for _ in range(trials)]
        hc_m = {"exito": [], "tiempo": [], "nodos": [], "pasos": []}
        ts_m = {"exito": [], "tiempo": [], "nodos": [], "pasos": []}
        for s in pruebas:
            r = ascenso_colinas(s)
            hc_m["exito"].append(1 if r["exito"] else 0)
            hc_m["tiempo"].append(r["tiempo"])
            hc_m["nodos"].append(r["nodos"])
            hc_m["pasos"].append(r["pasos"])
            r2 = temple_simulado(s)
            ts_m["exito"].append(1 if r2["exito"] else 0)
            ts_m["tiempo"].append(r2["tiempo"])
            ts_m["nodos"].append(r2["nodos"])
            ts_m["pasos"].append(r2["pasos"])
        estudio[sc] = {"hc": hc_m, "ts": ts_m}
        hc_p = [x for x in hc_m["pasos"] if x is not None]
        ts_p = [x for x in ts_m["pasos"] if x is not None]
        print(f"{sc:<8}{np.mean(hc_m['exito'])*100:<8.1f}"
              f"{np.mean(hc_m['tiempo'])*1000:<10.3f}{np.mean(hc_m['nodos']):<10.1f}"
              f"{(np.mean(hc_p) if hc_p else 0):<8.1f}| "
              f"{np.mean(ts_m['exito'])*100:<8.1f}"
              f"{np.mean(ts_m['tiempo'])*1000:<10.3f}{np.mean(ts_m['nodos']):<10.1f}"
              f"{(np.mean(ts_p) if ts_p else 0):<8.1f}")
    print("-" * 90)
    print("HC = O(k*b). TS = O(k) con un vecino por iteración.")
    print("b~2.67 (2 esquina, 3 borde, 4 centro). Espacio 9!/2=181440.")
    return estudio


def graficar_comparacion(estudio):
    """4 gráficas costo/complejidad vs dificultad. Guarda PNG."""
    niveles = sorted(estudio.keys())
    hc_ok = [np.mean(estudio[n]["hc"]["exito"]) * 100 for n in niveles]
    ts_ok = [np.mean(estudio[n]["ts"]["exito"]) * 100 for n in niveles]
    hc_t = [np.mean(estudio[n]["hc"]["tiempo"]) * 1000 for n in niveles]
    ts_t = [np.mean(estudio[n]["ts"]["tiempo"]) * 1000 for n in niveles]
    hc_n = [np.mean(estudio[n]["hc"]["nodos"]) for n in niveles]
    ts_n = [np.mean(estudio[n]["ts"]["nodos"]) for n in niveles]
    hc_p = []
    ts_p = []
    for n in niveles:
        a = [x for x in estudio[n]["hc"]["pasos"] if x is not None]
        b = [x for x in estudio[n]["ts"]["pasos"] if x is not None]
        hc_p.append(np.mean(a) if a else 0)
        ts_p.append(np.mean(b) if b else 0)

    fig, axs = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle('HC vs TS 3x3: costo f(s) vs dificultad', fontsize=15)

    axs[0, 0].plot(niveles, hc_ok, 'o-', label='Ascenso colinas', linewidth=2)
    axs[0, 0].plot(niveles, ts_ok, 's-', label='Temple simulado', linewidth=2)
    axs[0, 0].set_title('Tasa de éxito (%) vs dificultad')
    axs[0, 0].set_xlabel('Movs de mezcla')
    axs[0, 0].set_ylabel('% éxito')
    axs[0, 0].legend()
    axs[0, 0].grid(True, alpha=0.3)

    axs[0, 1].plot(niveles, hc_t, 'o-', label='HC O(k*b)', linewidth=2)
    axs[0, 1].plot(niveles, ts_t, 's-', label='TS O(k)', linewidth=2)
    axs[0, 1].set_title('Tiempo medio (ms, log) vs dificultad')
    axs[0, 1].set_xlabel('Movs de mezcla')
    axs[0, 1].set_ylabel('ms (log)')
    axs[0, 1].set_yscale('log')
    axs[0, 1].legend()
    axs[0, 1].grid(True, which='both', alpha=0.3)

    axs[1, 0].plot(niveles, hc_n, 'o-', label='HC O(k*b)', linewidth=2)
    axs[1, 0].plot(niveles, ts_n, 's-', label='TS O(k)', linewidth=2)
    axs[1, 0].set_title('Nodos evaluados (log) vs dificultad')
    axs[1, 0].set_xlabel('Movs de mezcla')
    axs[1, 0].set_ylabel('nodos (log)')
    axs[1, 0].set_yscale('log')
    axs[1, 0].legend()
    axs[1, 0].grid(True, which='both', alpha=0.3)

    axs[1, 1].plot(niveles, hc_p, 'o-', label='HC pasos', linewidth=2)
    axs[1, 1].plot(niveles, ts_p, 's-', label='TS pasos', linewidth=2)
    axs[1, 1].set_title('Pasos (solo éxitos) vs dificultad')
    axs[1, 1].set_xlabel('Movs de mezcla')
    axs[1, 1].set_ylabel('pasos')
    axs[1, 1].legend()
    axs[1, 1].grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('graficas_HC_TS_dificultad.png', dpi=300)
    print("Gráfica guardada como 'graficas_HC_TS_dificultad.png'")
    plt.show()


def main():
    """Punto de entrada: experimento + gráfica."""
    estudio = experimento()
    graficar_comparacion(estudio)
    print("Listo: ver graficas_HC_TS_dificultad.png")


if __name__ == "__main__":
    main()
