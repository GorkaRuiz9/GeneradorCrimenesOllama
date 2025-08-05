import subprocess
import random
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def exportar_a_pdf(texto, nombre_archivo):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(nombre_archivo, pagesize=letter)
    ancho, alto = letter
    y = alto - 50
    max_chars = 90  # máximo caracteres por línea aproximado

    for parrafo in texto.split("\n"):
        lineas = []
        texto_restante = parrafo.strip()

        while texto_restante:
            if len(texto_restante) <= max_chars:
                lineas.append(texto_restante)
                break
            else:
                # Buscar el último espacio dentro del límite max_chars
                corte = texto_restante.rfind(" ", 0, max_chars)
                if corte == -1:
                    # No hay espacio, cortar en max_chars para evitar loop infinito
                    corte = max_chars
                linea = texto_restante[:corte].rstrip()
                lineas.append(linea)
                texto_restante = texto_restante[corte:].lstrip()

        for linea in lineas:
            c.drawString(50, y, linea)
            y -= 15
            if y < 50:
                c.showPage()
                y = alto - 50

    c.save()


def generar_texto_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", "gemma2:9b"],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout.strip()

def generar_crimen(jugadores):
    victima = random.choice(jugadores)
    asesino = random.choice([j for j in jugadores if j != victima])

    nombre_caso = f"Caso_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
    os.makedirs(nombre_caso, exist_ok=True)

    # 1️⃣ Contexto (solo información pública)
    prompt_contexto = f"""
    Eres un narrador de historias en español.
    Crea un caso de asesinato, dando un contexto de este y quien ha muerto, de manera que leyendo tú respuesta los jugadores deban encontrar al asesino del caso.
    Trás dar el contexto debes dejar claro quien ha muerto, y como se ha encontrado el cadaver.
    Personajes: {", ".join(jugadores)}.
    La víctima (quien muere) es {victima}.
    El asesino es {asesino}.
    Describe lugar, época, ambiente y una breve descripción de cada personaje.
    Además, explica las relaciones entre los personajes: quiénes se llevan bien, quiénes tienen conflictos, alianzas o tensiones.
    El contexto debe dejar claro quién es la víctima.
    NO reveles quién es el asesino ni el motivo del asesinato.
    """

    contexto = generar_texto_ollama(prompt_contexto)
    exportar_a_pdf(contexto, os.path.join(nombre_caso, "contexto_crimen.pdf"))

    # 2️⃣ Pistas públicas
    carpeta_pistas = os.path.join(nombre_caso, "pistas")
    os.makedirs(carpeta_pistas, exist_ok=True)

    prompt_pistas = f"""
    Genera exactamente 10 pistas en español sobre un caso de asesinato ficticio.
    Los personajes son: {", ".join(jugadores)}.
    La víctima es {victima}.
    El asesino es {asesino}.
    Cada pista debe ser breve (1-3 frases), útil para la investigación y no debe revelar directamente al asesino.
    Enuméralas del 1 al 10.
    """
    pistas_texto = generar_texto_ollama(prompt_pistas)

    # Procesar pistas (eliminar línea introductoria)
    lineas = pistas_texto.strip().split("\n")
    if len(lineas) > 0:
        lineas = lineas[1:]  # eliminar primera línea

    pistas_lista = []
    for linea in lineas:
        if linea.strip():
            pista_limpia = linea.strip().lstrip("0123456789.-) ")
            pistas_lista.append(pista_limpia)

    for i, pista in enumerate(pistas_lista, start=1):
        with open(os.path.join(carpeta_pistas, f"pista_{i}.txt"), "w", encoding="utf-8") as f:
            f.write(pista)

    # 3️⃣ Información privada para el modelo
    prompt_solucion = f"""
    Eres un creador de historias para un juego de misterio en español.
    Basándote en el contexto y las pistas de un caso de asesinato ficticio, inventa:
    - El motivo real del asesinato.
    - Cómo lo cometió el asesino.
    - Detalles importantes que explican cada pista.
    Debes dar una narración clara para que un modelo pueda responder preguntas de los jugadores.
    Personajes: {", ".join(jugadores)}.
    Víctima: {victima}.
    Asesino: {asesino}.
    """
    solucion = generar_texto_ollama(prompt_solucion)

    archivo_modelo = f"""
    ===== INFORMACIÓN DEL CASO =====
    CONTEXTO:
    {contexto}

    PISTAS:
    {pistas_texto}

    ===== SOLUCIÓN (Privada para el modelo) =====
    Asesino: {asesino}
    Víctima: {victima}

    DETALLES REALES DEL CASO:
    {solucion}
    """
    with open(os.path.join(nombre_caso, "caso_para_modelo.txt"), "w", encoding="utf-8") as f:
        f.write(archivo_modelo)

    print(f"[✅] Caso generado en carpeta '{nombre_caso}'")
    print(f"    - contexto_crimen.pdf (público)")
    print(f"    - pistas/ (público)")
    print(f"    - caso_para_modelo.txt (privado para el modelo)")

if __name__ == "__main__":
    jugadores = ["Alejandro","Julia","Gorka","Xian","Inés","Lara","Lucía","Esther"]
    generar_crimen(jugadores)
