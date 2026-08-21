import re
from typing import List, Dict, Any

class LegalChunk:
    def __init__(self, doc_id: str, norma_nombre: str, seccion_jerarquica: str, articulo_num: str, contenido: str, url_boe: str, materia: str):
        self.doc_id = doc_id
        self.norma_nombre = norma_nombre
        self.seccion_jerarquica = seccion_jerarquica
        self.articulo_num = articulo_num
        self.contenido = contenido.strip()
        self.url_boe = url_boe
        self.materia = materia

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "norma_nombre": self.norma_nombre,
            "seccion_jerarquica": self.seccion_jerarquica,
            "articulo_num": self.articulo_num,
            "contenido": self.contenido,
            "url_boe": self.url_boe,
            "materia": self.materia
        }

    def format_citation(self) -> str:
        if self.articulo_num:
            return f"[{self.norma_nombre} - {self.articulo_num}]({self.url_boe})"
        return f"[{self.norma_nombre}]({self.url_boe})"


def chunk_texto_legal(texto: str, norma_nombre: str, url_boe: str, materia: str = "General") -> List[LegalChunk]:
    """
    Trocea un texto legislativo respetando la estructura de Artículos y Disposiciones del derecho español.
    """
    chunks: List[LegalChunk] = []
    
    # Patrón para detectar Artículos (ej: "Artículo 1.", "Art. 138", "Artículo 234 bis.")
    patron_articulo = re.compile(r'(?:^|\n)(Art[íi]culo\s+\d+(?:\s*(?:bis|ter|qu[aá]ter))?\.?|Disposici[óo]n\s+(?:adicional|transitoria|derogatoria|final)\s+\w+\.?)', re.IGNORECASE)
    
    posiciones = [m.start() for m in patron_articulo.finditer(texto)]
    titulos = [m.group(1).strip() for m in patron_articulo.finditer(texto)]

    if not posiciones:
        # Si no tiene artículos numerados, guardar como un bloque único
        chunks.append(LegalChunk(
            doc_id=f"{norma_nombre}_full",
            norma_nombre=norma_nombre,
            seccion_jerarquica="Cuerpo General",
            articulo_num="",
            contenido=texto[:3000],
            url_boe=url_boe,
            materia=materia
        ))
        return chunks

    for i in range(len(posiciones)):
        inicio = posiciones[i]
        fin = posiciones[i + 1] if i + 1 < len(posiciones) else len(texto)
        bloque = texto[inicio:fin].strip()
        art_titulo = titulos[i]

        chunk_id = f"{norma_nombre}_{art_titulo}".replace(" ", "_").replace(".", "")

        chunks.append(LegalChunk(
            doc_id=chunk_id,
            norma_nombre=norma_nombre,
            seccion_jerarquica=f"{norma_nombre} -> {art_titulo}",
            articulo_num=art_titulo,
            contenido=bloque,
            url_boe=url_boe,
            materia=materia
        ))

    return chunks
