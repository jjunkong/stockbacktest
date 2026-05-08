"""메타 정보 — 조건식/시장/진입가 옵션."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.backtest import ENTRY_OPTIONS, ENTRY_LABELS
from app.core.conditions import CONDITIONS
from app.schemas.common import ConditionInfo, MarketInfo, EntryInfo
from app.services.data_store import store

router = APIRouter(tags=["meta"])

MARKETS = [
    ("all", "전체 (KOSPI+KOSDAQ)"),
    ("KOSPI", "KOSPI"),
    ("KOSDAQ", "KOSDAQ"),
]


@router.get("/conditions", response_model=list[ConditionInfo])
def list_conditions() -> list[ConditionInfo]:
    """등록된 조건식 목록.

    1) CONDITIONS dict (cond1/cond2 같은 코드 정의 조건)
    2) signals csv 의 unique 조건식 (kiwoom_* 등 외부 수집 조건)
    중복 시 CONDITIONS dict 라벨 우선.
    """
    out: list[ConditionInfo] = [
        ConditionInfo(id=cid, label=name) for cid, (name, _) in CONDITIONS.items()
    ]
    seen = {ci.id for ci in out}

    if store.signals is not None and "조건식" in store.signals.columns:
        df = store.signals[["조건식", "조건식이름"]].drop_duplicates()
        for _, r in df.iterrows():
            cid = str(r["조건식"])
            if cid in seen:
                continue
            label = str(r["조건식이름"]) if r["조건식이름"] else cid
            out.append(ConditionInfo(id=cid, label=label))
            seen.add(cid)
    return out


@router.get("/markets", response_model=list[MarketInfo])
def list_markets() -> list[MarketInfo]:
    return [MarketInfo(id=mid, label=label) for mid, label in MARKETS]


@router.get("/entry-options", response_model=list[EntryInfo])
def list_entry_options() -> list[EntryInfo]:
    return [EntryInfo(id=opt, label=ENTRY_LABELS[opt]) for opt in ENTRY_OPTIONS]
