import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    tempfile.gettempdir(), "_mg_test_api.db"
)
_db = os.environ["DATABASE_URL"].replace("sqlite:///", "")
if os.path.exists(_db):
    os.remove(_db)

from fastapi.testclient import TestClient  # noqa: E402
from app.database import Base, engine      # noqa: E402
from app import models                     # noqa: E402,F401
Base.metadata.create_all(bind=engine)
from app.main import app                   # noqa: E402

client = TestClient(app)
P = "/api/v1"


def test_config_default():
    r = client.get(f"{P}/config")
    assert r.status_code == 200
    assert r.json()["seed_krw"] == 500_000_000
    assert r.json()["divisions"] == 40


def test_full_flow():
    # 세션 시작 (환율 수동 → 네트워크 미사용)
    r = client.post(f"{P}/session", json={"usd_krw_rate": 1390})
    assert r.status_code == 200, r.text
    s = r.json()
    assert abs(s["per_turn_usd"] - (500_000_000 / 1390 / 40)) < 1

    # 첫날 계산: 보유0, 현재가 25 → 매수2 / 매도0
    r = client.post(f"{P}/daily/calculate", json={"soxl_price": 25.0, "usd_krw_rate": 1390})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["mode"] == "전반전"
    assert len(d["buy_orders"]) == 2
    assert d["sell_orders"] == []
    assert d["buy_orders"][0]["amount_krw"] is not None

    # 체결 입력 (매수 2건)
    fills = [
        {"action": "buy", "quantity": o["quantity"], "price_usd": o["price_usd"], "order_type": "LOC"}
        for o in d["buy_orders"]
    ]
    r = client.post(f"{P}/daily/execute", json={"fills": fills})
    assert r.status_code == 200, r.text
    pos = r.json()["position"]
    assert pos["holding_qty"] > 0 and pos["avg_price_usd"] > 0

    # 둘째날 계산 → 매도 2건(1/4+3/4) 등장
    r = client.post(f"{P}/daily/calculate", json={"soxl_price": 26.0, "usd_krw_rate": 1390})
    d2 = r.json()
    assert len(d2["sell_orders"]) == 2
    assert d2["evaluation"]["eval_value_krw"] != 0

    # today / current
    assert client.get(f"{P}/daily/today").status_code == 200
    cur = client.get(f"{P}/session/current")
    assert cur.status_code == 200
    assert cur.json()["position"]["holding_qty"] > 0


def test_duplicate_session_blocked():
    r = client.post(f"{P}/session", json={"usd_krw_rate": 1390})
    assert r.status_code == 400


def test_daily_list():
    r = client.get(f"{P}/daily/list")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "points" in body and len(body["points"]) >= 1
    last = body["points"][-1]
    assert last["buy_qty"] > 0           # 체결된 매수 반영됨
    assert last["avg_price_usd"] > 0
    assert last["target_price"] is not None


def test_session_history():
    r = client.get(f"{P}/session/history")
    assert r.status_code == 200, r.text
    sessions = r.json()["sessions"]
    assert len(sessions) >= 1
    assert sessions[0]["status"] == "active"


def test_daily_list_by_session():
    sid = client.get(f"{P}/session/history").json()["sessions"][0]["id"]
    r = client.get(f"{P}/daily/list?session_id={sid}")
    assert r.status_code == 200, r.text
    pts = r.json()["points"]
    assert len(pts) >= 1
    assert "fills" in pts[-1]
    assert len(pts[-1]["fills"]) >= 1     # 체결 내역 포함
    # 없는 사이클
    assert client.get(f"{P}/daily/list?session_id=99999").status_code == 404


def test_stats_before_close():
    r = client.get(f"{P}/stats/summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_cycles"] >= 1
    assert body["current"] is not None         # 활성 사이클 존재
    assert body["closed_cycles"] == 0


def test_close_session():
    sid = client.get(f"{P}/session/history").json()["sessions"][0]["id"]
    r = client.post(f"{P}/session/{sid}/close?status=completed")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    assert "final_profit_pct" in r.json()
    # 종료 후 활성 사이클 없음
    assert client.get(f"{P}/session/current").json()["session"] is None
    # 이미 종료 → 400
    assert client.post(f"{P}/session/{sid}/close").status_code == 400
    # 잘못된 status → 400
    r2 = client.post(f"{P}/session/{sid}/close?status=foo")
    assert r2.status_code == 400


def test_stats_after_close():
    body = client.get(f"{P}/stats/summary").json()
    assert body["closed_cycles"] >= 1
    assert len(body["cycles"]) >= 1
    assert body["current"] is None
    assert body["avg_profit_pct"] is not None


def test_transactions_crud():
    # 이전 테스트에서 사이클이 종료됐을 수 있으니 보장
    if client.get(f"{P}/session/current").json()["session"] is None:
        client.post(f"{P}/session", json={"usd_krw_rate": 1390})
    d = client.post(f"{P}/daily/calculate", json={"soxl_price": 25.0, "usd_krw_rate": 1390}).json()
    fills = [{"action": "buy", "quantity": o["quantity"], "price_usd": o["price_usd"]} for o in d["buy_orders"]]
    client.post(f"{P}/daily/execute", json={"fills": fills})

    lst = client.get(f"{P}/daily/transactions").json()["transactions"]
    assert len(lst) >= 2
    tid = lst[0]["id"]

    # 수정 → total 재계산
    r = client.put(f"{P}/daily/transactions/{tid}", json={"quantity": 10, "price_usd": 30})
    assert r.status_code == 200, r.text
    assert r.json()["transaction"]["quantity"] == 10
    assert r.json()["transaction"]["total_usd"] == 300.0
    assert r.json()["position"]["holding_qty"] > 0

    # 검증 실패들
    assert client.put(f"{P}/daily/transactions/{tid}", json={"quantity": 0}).status_code == 400
    assert client.post(f"{P}/daily/execute", json={"fills": [{"action": "buy", "quantity": -1, "price_usd": 5}]}).status_code == 400
    assert client.post(f"{P}/daily/execute", json={"fills": [{"action": "hold", "quantity": 1, "price_usd": 5}]}).status_code == 400

    # 삭제
    before = len(client.get(f"{P}/daily/transactions").json()["transactions"])
    assert client.delete(f"{P}/daily/transactions/{tid}").status_code == 200
    after = len(client.get(f"{P}/daily/transactions").json()["transactions"])
    assert after == before - 1
    assert client.delete(f"{P}/daily/transactions/999999").status_code == 404


def test_reopen_session():
    if client.get(f"{P}/session/current").json()["session"] is None:
        client.post(f"{P}/session", json={"usd_krw_rate": 1390})
    sid = client.get(f"{P}/session/current").json()["session"]["id"]
    client.post(f"{P}/session/{sid}/close?status=completed")
    assert client.get(f"{P}/session/current").json()["session"] is None

    # 되돌리기 성공
    r = client.post(f"{P}/session/{sid}/reopen")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"
    assert client.get(f"{P}/session/current").json()["session"]["id"] == sid

    # 이미 active → 400
    assert client.post(f"{P}/session/{sid}/reopen").status_code == 400

    # 다른 활성 있을 때 차단
    client.post(f"{P}/session/{sid}/close?status=completed")
    client.post(f"{P}/session", json={"usd_krw_rate": 1390})  # 새 active 생성
    assert client.post(f"{P}/session/{sid}/reopen").status_code == 400

    # 없는 id
    assert client.post(f"{P}/session/99999/reopen").status_code == 404


def test_seed_alert():
    if client.get(f"{P}/session/current").json()["session"] is None:
        client.post(f"{P}/session", json={"usd_krw_rate": 1390})
    # 큰 매수로 T를 분할수 이상으로 끌어올림
    client.post(f"{P}/daily/execute", json={"fills": [{"action": "buy", "quantity": 3000, "price_usd": 200}]})
    d = client.post(f"{P}/daily/calculate", json={"soxl_price": 200.0, "usd_krw_rate": 1390}).json()
    assert d["seed_alert"] is not None
    assert d["seed_alert"]["level"] == "critical"
    assert d["turn_number"] >= d["seed_alert"]["divisions"]


def test_backup_export_import():
    e = client.get(f"{P}/backup/export").json()
    assert "sessions" in e and "transactions" in e and "daily_states" in e
    n_ses = len(e["sessions"]); n_tx = len(e["transactions"])
    assert n_ses >= 1
    # 그대로 다시 import → 개수 보존 (ID 재매핑)
    r = client.post(f"{P}/backup/import", json=e)
    assert r.status_code == 200, r.text
    e2 = client.get(f"{P}/backup/export").json()
    assert len(e2["sessions"]) == n_ses
    assert len(e2["transactions"]) == n_tx
    # 잘못된 파일
    assert client.post(f"{P}/backup/import", json={"foo": 1}).status_code == 400


def test_start_with_tqqq():
    cur = client.get(f"{P}/session/current").json()["session"]
    if cur:
        client.post(f"{P}/session/{cur['id']}/close?status=completed")
    r = client.post(f"{P}/session", json={"ticker": "TQQQ", "usd_krw_rate": 1390})
    assert r.status_code == 200, r.text
    assert r.json()["ticker"] == "TQQQ"
    assert client.get(f"{P}/session/current").json()["session"]["ticker"] == "TQQQ"
