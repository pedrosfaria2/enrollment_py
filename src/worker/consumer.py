# src/worker/consumer.py
from __future__ import annotations

import json
import os
import re
import time

import pika
from pika.adapters.blocking_connection import BlockingChannel

from domain.enrollment import Enrollment
from infra.enumerators.enrollment import EnrollmentStatus
from infra.repositories.age_group import AgeGroupRepository
from infra.repositories.enrollment import EnrollmentRepository
from settings import cfg

_DIGIT_RE = re.compile(r"\d")


def _digits_only(s: str) -> str:
    return "".join(_DIGIT_RE.findall(s))


def _cpf_valid(cpf: str) -> bool:
    s = _digits_only(cpf)
    if len(s) != 11 or s == s[0] * 11:  # noqa: PLR2004
        return False
    n = [int(c) for c in s]
    sum1 = sum(x * w for x, w in zip(n[:9], range(10, 1, -1), strict=False))
    dv1 = (sum1 * 10) % 11
    if dv1 == 10:  # noqa: PLR2004
        dv1 = 0
    if dv1 != n[9]:
        return False
    sum2 = sum(x * w for x, w in zip(n[:9], range(11, 2, -1), strict=False)) + dv1 * 2
    dv2 = (sum2 * 10) % 11
    if dv2 == 10:  # noqa: PLR2004
        dv2 = 0
    return dv2 == n[10]


def _upsert_final(repo: EnrollmentRepository, age_groups: AgeGroupRepository, payload: dict) -> None:
    name = payload["name"]
    age = int(payload["age"])
    cpf = payload["cpf"]
    requested_at = int(payload.get("requested_at") or 0)
    group_name = payload.get("age_group_name")

    group_exists = bool(group_name) and age_groups.exists(name=group_name)
    cpf_ok = _cpf_valid(cpf)
    final_status = EnrollmentStatus.APPROVED if (group_exists and cpf_ok) else EnrollmentStatus.REJECTED
    enrolled_at = int(time.time()) if final_status == EnrollmentStatus.APPROVED else None

    existing = repo.find_by_cpf(cpf)
    ent = Enrollment.create_final(
        name=name,
        age=age,
        cpf=cpf,
        final_status=final_status,
        existing=existing,
        requested_at=requested_at,
        enrolled_at=enrolled_at,
        age_group_name=group_name if group_exists else None,
    )

    if existing is ent:
        return

    data = {
        "name": ent.name,
        "age": ent.age,
        "cpf": ent.cpf,
        "status": ent.status.value,
        "requested_at": ent.requested_at,
        "enrolled_at": ent.enrolled_at,
        "age_group_name": ent.age_group_name,
    }
    updated = repo.update(data, cpf=cpf)
    if not updated:
        repo.insert(ent)


def _on_message(ch: BlockingChannel, method, _properties, body: bytes) -> None:
    repo = EnrollmentRepository()
    age_groups = AgeGroupRepository()
    try:
        payload = json.loads(body.decode("utf-8"))
        min_secs = max(2, int(os.getenv("ENROLLMENT_WORKER_MIN_SECONDS", "2")))
        time.sleep(min_secs)
        _upsert_final(repo, age_groups, payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main() -> None:
    params = pika.URLParameters(cfg.RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    queue_name = os.getenv("QUEUE_NAME")
    ch.queue_declare(queue=queue_name, durable=True, auto_delete=False)
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue_name, on_message_callback=_on_message, auto_ack=False)
    ch.start_consuming()


if __name__ == "__main__":
    main()
