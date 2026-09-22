import random
import time
import math
from pathlib import Path
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
    inicio = time.perf_counter()
    actual = estado_inicial
    costo_actual = costo(actual)
    camino = [actual]
    historial_costo = [costo_actual]
    soluciones_evaluadas = 0
    motivo = "max_iter"

    if actual == META:
        return {
            "exito": True,
            "tiempo": time.perf_counter() - inicio,
            "evaluaciones": 0,
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
        soluciones_evaluadas += len(vecinos)
        costo_mejor, mejor = min(
            ((costo(vecino), vecino) for vecino in vecinos),
            key=lambda candidato: candidato[0],
        )
        if costo_mejor >= costo_actual:
            motivo = "minimo_local_o_meseta"
            break
        actual = mejor
        costo_actual = costo_mejor
        camino.append(actual)
        historial_costo.append(costo_actual)

    exito = (actual == META)
    if exito:
        motivo = "meta_alcanzada"
    return {
        "exito": exito,
        "tiempo": time.perf_counter() - inicio,
        "evaluaciones": soluciones_evaluadas,
        "pasos": (len(camino) - 1) if exito else None,
        "camino": camino,
        "historial_costo": historial_costo,
        "motivo": motivo,
        "costo_final": costo_actual,
    }


def temple_simulado(estado_inicial, T_inicial=2.0, alpha=0.99, T_min=0.001,
                     max_iter=10000, semilla=None):
    """Temple simulado con función de costo f(s).

    Delta E = f(s') - f(s). Si mejora o empata se acepta.
    Si empeora se acepta con P = exp(-DeltaE / T).
    Enfría con T = T_inicial * alpha^k.
    """
    if semilla is not None:
        random.seed(semilla)
    inicio = time.perf_counter()
    actual = estado_inicial
    costo_actual = costo(actual)
    mejor = actual
    mejor_costo = costo_actual
    trayectoria = [actual]
    historial_costo = [costo_actual]
    historial_T = [T_inicial]
    soluciones_evaluadas = 0

    if actual == META:
        return {
            "exito": True,
            "tiempo": time.perf_counter() - inicio,
            "evaluaciones": 0,
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
        soluciones_evaluadas += 1
        siguiente = random.choice(vecinos)
        costo_siguiente = costo(siguiente)
        delta_E = costo_siguiente - costo_actual
        acepta = False
        if delta_E <= 0:
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
        "tiempo": time.perf_counter() - inicio,
        "evaluaciones": soluciones_evaluadas,
        "pasos": (len(trayectoria) - 1) if exito else None,
        "camino": trayectoria,
        "historial_costo": historial_costo,
        "historial_T": historial_T,
        "costo_final": costo_actual,
        "mejor_costo": mejor_costo,
    }


def experimento(trials=30, max_iter=5000, semilla=123):
    """Compara HC y TS sobre los mismos estados iniciales solucionables."""
    random.seed(semilla)
    estados = []
    vistos = set()
    while len(estados) < trials:
        estado = generar_estado_aleatorio(20)
        if estado != META and estado not in vistos:
            vistos.add(estado)
            estados.append(estado)

    resultados = {}
    for nombre, algoritmo in (("hc", ascenso_colinas), ("ts", temple_simulado)):
        ejecuciones = [algoritmo(estado, max_iter=max_iter) for estado in estados]
        resultados[nombre] = {
            "exito": np.mean([r["exito"] for r in ejecuciones]) * 100,
            "evaluaciones": np.mean([r["evaluaciones"] for r in ejecuciones]),
            "tiempo": np.mean([r["tiempo"] for r in ejecuciones]) * 1000,
        }

    print("Comparación experimental: Ascenso de Colinas vs Temple Simulado")
    print(f"Puzle 3x3 | {trials} estados iniciales distintos y compartidos | máximo {max_iter} iteraciones")
    print(f"{'Algoritmo':<22}{'Éxito (%)':>12}{'Evaluaciones promedio':>24}{'Tiempo promedio (ms)':>23}")
    for nombre, etiqueta in (("hc", "Ascenso de Colinas"), ("ts", "Temple Simulado")):
        r = resultados[nombre]
        print(f"{etiqueta:<22}{r['exito']:>12.1f}{r['evaluaciones']:>24.1f}{r['tiempo']:>23.3f}")
    return resultados


def graficar_comparacion(estudio):
    """Tres gráficas de barras con las métricas agregadas de HC y TS."""
    etiquetas = ['Ascenso de\nColinas', 'Temple\nSimulado']
    colores = ['tab:blue', 'tab:orange']
    metricas = (
        ('exito', 'Tasa de éxito de los algoritmos', 'Éxito (%)', '{:.1f}%'),
        ('evaluaciones', 'Soluciones evaluadas promedio', 'Soluciones evaluadas', '{:.1f}'),
        ('tiempo', 'Tiempo promedio de ejecución', 'Tiempo (ms)', '{:.3f}'),
    )

    fig, axs = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Comparación experimental: Ascenso de Colinas vs Temple Simulado', fontsize=15)
    for ax, (clave, titulo, eje_y, formato) in zip(axs, metricas):
        valores = [estudio['hc'][clave], estudio['ts'][clave]]
        barras = ax.bar(etiquetas, valores, color=colores, width=0.55)
        ax.set_title(titulo)
        ax.set_ylabel(eje_y)
        limite = 100 if clave == 'exito' else max(valores) * 1.15
        ax.set_ylim(0, limite)
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        for barra, valor in zip(barras, valores):
            ax.text(barra.get_x() + barra.get_width() / 2,
                    max(valor, limite * 0.02) + limite * 0.01,
                    formato.format(valor), ha='center', va='bottom')

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    ruta_grafica = Path(__file__).resolve().parent / 'img' / 'comparacion_HC_TS.png'
    ruta_grafica.parent.mkdir(exist_ok=True)
    fig.savefig(ruta_grafica, dpi=300)
    print(f"Gráfica guardada como '{ruta_grafica}'")
    plt.show()


def main():
    """Punto de entrada: experimento + gráfica."""
    estudio = experimento()
    graficar_comparacion(estudio)
    print("Listo: ver img/comparacion_HC_TS.png")


if __name__ == "__main__":
    main()
