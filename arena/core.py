"""Núcleo mínimo de Arena: sin red, callbacks, IA obligatoria ni Modelica obligatoria.

La Arena registra investigación y discriminación, NO valida causalidad por sí sola.
Los datos reservados se entregan únicamente al evaluador, nunca a constructores.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
from typing import Any

SCHEMA = "cei.arena.v0.1"
KINDS = {"OBSERVADO", "INFERENCIA", "HIPOTESIS", "SIMULACION", "DESCONOCIDO"}
LANES = ("A_CONVENCIONAL", "B_SD_DETERMINISTA", "C_IGC")
GATES = ("G1", "G2", "G3")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_intake(case: dict) -> None:
    require(case.get("schema_version") == SCHEMA, "schema_version incorrecto")
    require(bool(case.get("case_id")), "case_id obligatorio")
    require(bool(case.get("question")), "pregunta obligatoria")
    require(isinstance(case.get("agent"), dict), "agente focal obligatorio")
    for key in ("controls", "influences", "observes"):
        require(isinstance(case["agent"].get(key), list), f"agent.{key} debe ser lista")
    require(isinstance(case.get("evidence"), list), "evidence debe ser lista")
    ids = set()
    for obs in case["evidence"]:
        require(isinstance(obs, dict), "evidencia inválida")
        require(obs.get("id") and obs["id"] not in ids, "IDs de evidencia vacíos/duplicados")
        ids.add(obs["id"])
        require(obs.get("kind") in KINDS, "clase epistemológica inválida")
        require(bool(obs.get("source")) and bool(obs.get("as_known_at")), "falta procedencia o fecha")
    require("holdout" not in case and "gold" not in case, "no incluir reserva/gold en intake visible")


def view_for_lane(case: dict, lane: str) -> dict:
    check_intake(case)
    require(lane in LANES, "vía desconocida")
    visible = {key: case[key] for key in ("schema_version", "case_id", "question", "agent", "evidence")}
    visible["lane"] = lane
    visible["snapshot_sha256"] = digest(visible)
    return visible


def validate_submission(submission: dict, visible: dict) -> None:
    require(submission.get("schema_version") == SCHEMA, "schema de respuesta inválido")
    require(submission.get("case_id") == visible["case_id"], "caso no coincide")
    require(submission.get("lane") == visible["lane"], "vía no coincide")
    require(submission.get("snapshot_sha256") == visible["snapshot_sha256"], "snapshot alterado")
    require(isinstance(submission.get("hypotheses"), list), "faltan hipótesis")
    require(isinstance(submission.get("unknowns"), list), "faltan incertidumbres")
    require(isinstance(submission.get("next_tests"), list), "faltan siguientes pruebas")
    require(isinstance(submission.get("cost"), dict), "falta costo de investigación")
    require(submission.get("modelica_executed") in (True, False), "declarar uso de Modelica")
    ids = set()
    evidence_ids = {e["id"] for e in visible["evidence"]}
    for hypothesis in submission["hypotheses"]:
        require(hypothesis.get("id") and hypothesis["id"] not in ids, "hipótesis sin ID único")
        ids.add(hypothesis["id"])
        require(bool(hypothesis.get("mechanism")), "falta mecanismo")
        require(bool(hypothesis.get("falsifier")), "falta refutador")
        require(set(hypothesis.get("evidence_ids", [])) <= evidence_ids, "evidencia no visible citada")
    for test in submission["next_tests"]:
        require(bool(test.get("question")) and bool(test.get("discriminates")), "prueba no discriminante")
        require(isinstance(test.get("estimated_cost"), (int, float)) and
                test["estimated_cost"] >= 0, "costo de prueba inválido")
    # Las compuertas NO se autoaprueban por un constructor.
    require("gates" not in submission and "gold" not in submission and
            "holdout" not in submission, "el constructor no puede adjudicar ni leer reserva")


def seal_submission(submission: dict, visible: dict) -> dict:
    validate_submission(submission, visible)
    return {"submission_sha256": digest(submission),
            "snapshot_sha256": visible["snapshot_sha256"], "submission": submission}


def adjudicate(visible: dict, sealed: dict, *, holdout: dict | None = None) -> dict:
    """Solo evalúa custodia y estructura; verdad empírica exige evaluador independiente."""
    submission = sealed["submission"]
    validate_submission(submission, visible)
    require(sealed["submission_sha256"] == digest(submission), "respuesta fue modificada")
    result = {
        "schema_version": SCHEMA, "case_id": visible["case_id"],
        "lane": visible["lane"], "snapshot_sha256": visible["snapshot_sha256"],
        "submission_sha256": sealed["submission_sha256"],
        "engineering": "PASS", "gates": {gate: "NOT_ADJUDICATED" for gate in GATES},
        "empirical": "NOT_EVALUATED", "holdout_used": False,
        "note": "Contrato válido ≠ mecanismo verdadero; requiere evaluación externa."
    }
    # Una reserva no debe convertirse en un PASS automático ni incluirse en salida.
    if holdout is not None:
        require(holdout.get("case_id") == visible["case_id"], "reserva de otro caso")
        result["holdout_available_to_evaluator"] = True
    return result


def save_json(path: str | Path, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical(data) + b"\n")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
