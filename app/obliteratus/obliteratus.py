#!/usr/bin/env python3
"""
Obliteratus — Redação de Imagens e Metadados para Privacidade de Evidências.

Remove PII (Pessoas, nomes, CPF, placas) de imagens via Gaussian Blur
e sanea metadados automaticamente, mantendo apenas o essencial para análise.
"""

import base64
import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("obliteratus")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

PII_FIELDS: List[str] = ["nome_completo", "placa_raw", "cpf", "rg", "endereco"]
SAFE_FIELDS: List[str] = ["bairro", "tipo_crime", "data", "lat_lon", "cidade", "uf", "cep"]

HAAR_FACE_PATH: str = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
"""Caminho para o classificador Haar Cascade de faces frontais."""


# ---------------------------------------------------------------------------
# Núcleo — Redação de Imagens
# ---------------------------------------------------------------------------


def obliterate_image(
    image_array: np.ndarray,
    cascade_path: str = HAAR_FACE_PATH,
    blur_ksize: Tuple[int, int] = (99, 99),
    blur_sigma: float = 30.0,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Aplica desfoque gaussiano em rostos detectados na imagem.

    Args:
        image_array: Array NumPy (H, W, 3) da imagem BGR (OpenCV).
        cascade_path: Caminho para o XML do Haar Cascade.
        blur_ksize: Tamanho do kernel do desfoque (ímpar).
        blur_sigma: Sigma do desfoque gaussiano.

    Returns:
        (imagem_redigida, audit_entries)
    """
    audit: List[Dict[str, Any]] = []
    img = image_array.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Validação do classificador
    if not os.path.isfile(cascade_path):
        logger.warning("Cascade não encontrado em %s — pulando detecção facial.", cascade_path)
        return img, [{"evento": "face_detection_skipped", "motivo": "cascade_not_found",
                       "cascade_path": cascade_path}]

    face_cascade = cv2.CascadeClassifier(cascade_path)

    # Histogram equalization melhora detecção em iluminação desigual
    gray_eq = cv2.equalizeHist(gray)
    faces = face_cascade.detectMultiScale(gray_eq, scaleFactor=1.1, minNeighbors=4,
                                          minSize=(30, 30))

    logger.info("Detectadas %d face(s) na imagem.", len(faces))

    for i, (x, y, w, h) in enumerate(faces):
        roi = img[y : y + h, x : x + w]
        # Ajuste de kernel para não exceder dimensões do ROI
        ksize = (min(blur_ksize[0], w if w % 2 == 1 else w - 1),
                 min(blur_ksize[1], h if h % 2 == 1 else h - 1))
        ksize = (ksize[0] if ksize[0] > 1 else 3,
                 ksize[1] if ksize[1] > 1 else 3)
        blurred = cv2.GaussianBlur(roi, ksize, blur_sigma)
        img[y : y + h, x : x + w] = blurred
        audit.append({
            "evento": "face_redacted",
            "face_index": i,
            "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
            "kernel": list(ksize),
        })

    if not faces:
        audit.append({"evento": "no_faces_detected"})

    return img, audit


# ---------------------------------------------------------------------------
# Redação de Metadados
# ---------------------------------------------------------------------------


def obliterate_metadata(metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Remove campos de PII dos metadados, mantendo apenas os seguros.

    Args:
        metadata: Dicionário original com dados da ocorrência.

    Returns:
        (metadados_redigidos, audit_entries)
    """
    audit: List[Dict[str, Any]] = []
    safe: Dict[str, Any] = {}
    redacted_fields: List[str] = []

    for key in SAFE_FIELDS:
        if key in metadata:
            safe[key] = metadata[key]

    for key in PII_FIELDS:
        if key in metadata:
            redacted_fields.append(key)

    # Campos não mapeados (explicitamente removidos)
    all_keys = set(metadata.keys())
    safe_set = set(SAFE_FIELDS)
    pii_set = set(PII_FIELDS)
    unknown = all_keys - safe_set - pii_set
    for key in unknown:
        redacted_fields.append(key)

    audit.append({
        "evento": "metadata_redacted",
        "fields_removed": redacted_fields,
        "fields_kept": list(safe.keys()),
    })

    return safe, audit


# ---------------------------------------------------------------------------
# Função Principal — Obliteratus
# ---------------------------------------------------------------------------


def obliteratus(
    image_path: str,
    metadata: Dict[str, Any],
    blur_ksize: Tuple[int, int] = (99, 99),
    blur_sigma: float = 30.0,
) -> Dict[str, Any]:
    """
    Pipeline completo de redação de imagem e metadados.

    Args:
        image_path: Caminho para o arquivo de imagem.
        metadata: Dicionário com metadados da evidência.
        blur_ksize: Kernel do desfoque facial.
        blur_sigma: Sigma do desfoque.

    Returns:
        Dicionário com:
            - redacted_image (str): Imagem em base64 (PNG).
            - redacted_metadata (dict): Metadados sem PII.
            - audit_log (list): Entradas de auditoria.
    """
    start = time.time()
    audit_log: List[Dict[str, Any]] = []

    # 1. Carregar imagem
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Falha ao carregar imagem (formato inválido): {image_path}")

    audit_log.append({
        "evento": "image_loaded",
        "path": os.path.basename(image_path),
        "shape": list(img_bgr.shape),
    })

    # 2. Redação facial
    img_redacted, face_audit = obliterate_image(img_bgr, blur_ksize=blur_ksize, blur_sigma=blur_sigma)
    audit_log.extend(face_audit)

    # 3. Codificar para base64 (PNG)
    success, buffer = cv2.imencode(".png", img_redacted)
    if not success:
        raise RuntimeError("Falha ao codificar imagem redigida para PNG.")
    b64_str = base64.b64encode(buffer).decode("utf-8")

    audit_log.append({
        "evento": "image_encoded",
        "format": "png",
        "base64_length": len(b64_str),
    })

    # 4. Redação de metadados
    meta_redacted, meta_audit = obliterate_metadata(metadata)
    audit_log.extend(meta_audit)

    # 5. Finalizar log
    elapsed = round(time.time() - start, 4)
    audit_log.append({
        "evento": "obliteratus_complete",
        "elapsed_seconds": elapsed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "redacted_image": b64_str,
        "redacted_metadata": meta_redacted,
        "audit_log": audit_log,
    }


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def redacted_image_to_pil(redacted_image_b64: str) -> Image.Image:
    """Converte base64 da imagem redigida para PIL Image (RGB)."""
    buf = io.BytesIO(base64.b64decode(redacted_image_b64))
    return Image.open(buf).convert("RGB")


def save_redacted_image(redacted_image_b64: str, output_path: str) -> None:
    """Salva a imagem redigida (base64) em disco."""
    buf = base64.b64decode(redacted_image_b64)
    with open(output_path, "wb") as f:
        f.write(buf)
    logger.info("Imagem redigida salva em %s", output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Obliteratus — Redação de PII em imagens de evidência."
    )
    parser.add_argument("image", help="Caminho da imagem de entrada")
    parser.add_argument("--metadata", "-m", default="{}",
                        help="Metadados em JSON (string ou arquivo .json)")
    parser.add_argument("--output", "-o", default=None,
                        help="Onde salvar a imagem redigida (opcional)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Log detalhado")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse metadata
    meta: Dict[str, Any] = {}
    md_raw = args.metadata
    if os.path.isfile(md_raw):
        with open(md_raw, "r") as f:
            meta = json.load(f)
    else:
        try:
            meta = json.loads(md_raw)
        except json.JSONDecodeError:
            logger.error("Metadados inválidos: %s", md_raw)
            return

    result = obliteratus(args.image, meta)

    print(json.dumps(result["redacted_metadata"], indent=2, ensure_ascii=False))
    print("---")
    print(json.dumps(result["audit_log"], indent=2, ensure_ascii=False))

    if args.output:
        save_redacted_image(result["redacted_image"], args.output)


if __name__ == "__main__":
    main()
