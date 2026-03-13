#!/usr/bin/env python3
"""
天大吃什么 - 腾讯地图 POI 采集脚本

用途:
1. 先解析“天津大学北洋园校区”中心坐标
2. 再按关键词做 nearby POI 搜索
3. 对商户去重
4. 输出到 CSV + SQLite

运行方式:
    # 先在 .env 或系统环境变量中配置：
    # TENCENT_MAP_API_KEY=你的腾讯地图Key
    python scripts/collect_tencent_poi.py

输出文件:
    outputs/beiyangyuan_restaurants_raw.csv
    outputs/beiyangyuan_restaurants_raw.db
"""

from __future__ import annotations

import csv
import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# Config (easy to edit)
# =========================
CAMPUS_NAME = "天津大学北洋园校区"
DEFAULT_RADIUS = 2500
MAX_PAGES_PER_KEYWORD = 5
PAGE_SIZE = 20
TIMEOUT_SECONDS = 12

KEYWORDS = [
    "餐饮",
    "美食",
    "小吃",
    "面馆",
    "盖饭",
    "川菜",
    "火锅",
    "烧烤",
    "奶茶",
    "米线",
    "冒菜",
    "饺子",
    "快餐",
    "轻食",
]

BASE_URL = "https://apis.map.qq.com/ws/place/v1/search"
SOURCE_NAME = "tencent_map"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
CSV_PATH = OUTPUT_DIR / "beiyangyuan_restaurants_raw.csv"
DB_PATH = OUTPUT_DIR / "beiyangyuan_restaurants_raw.db"
DB_TABLE = "restaurants_raw"
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [ROOT_DIR / ".env", ROOT_DIR / "backend" / ".env"]

# 腾讯地图 Key 从环境变量读取，禁止硬编码。
# 支持：
# 1) 系统环境变量 TENCENT_MAP_API_KEY
# 2) 自动读取 .env / backend/.env 里的 TENCENT_MAP_API_KEY
API_KEY = os.getenv("TENCENT_MAP_API_KEY", "").strip()

# normalized schema
SCHEMA_FIELDS = [
    "source_id",
    "name",
    "address",
    "category",
    "lat",
    "lng",
    "distance",
    "province",
    "city",
    "district",
    "adcode",
    "source_keyword",
    "source",
]


@dataclass
class POIRecord:
    source_id: str
    name: str
    address: str
    category: str
    lat: Optional[float]
    lng: Optional[float]
    distance: Optional[float]
    province: str
    city: str
    district: str
    adcode: str
    source_keyword: str
    source: str = SOURCE_NAME

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "address": self.address,
            "category": self.category,
            "lat": self.lat,
            "lng": self.lng,
            "distance": self.distance,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "adcode": self.adcode,
            "source_keyword": self.source_keyword,
            "source": self.source,
        }


def build_http_session() -> requests.Session:
    """Create requests session with retry."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'").strip()
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_api_key_loaded() -> str:
    api_key = API_KEY
    if api_key:
        return api_key

    for env_path in ENV_CANDIDATES:
        _load_env_file(env_path)
        api_key = os.getenv("TENCENT_MAP_API_KEY", "").strip()
        if api_key:
            logging.info("Loaded TENCENT_MAP_API_KEY from %s", env_path)
            return api_key

    raise RuntimeError(
        "TENCENT_MAP_API_KEY 未配置。请在系统环境变量或 .env 文件中设置该值。"
    )


def request_place_search(session: requests.Session, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call Tencent place search API and validate response format."""
    try:
        resp = session.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"HTTP request failed: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError as exc:
        raise RuntimeError("API response is not valid JSON") from exc

    status = payload.get("status")
    if status != 0:
        msg = payload.get("message", "unknown error")
        raise RuntimeError(f"Tencent API returned status={status}, message={msg}")

    return payload


def pick_campus_center(candidates: List[Dict[str, Any]], campus_name: str) -> Tuple[float, float]:
    """Pick best campus result from candidates and return (lat, lng)."""
    if not candidates:
        raise RuntimeError("No campus candidates found from Tencent API")

    best = candidates[0]
    for item in candidates:
        title = str(item.get("title", ""))
        if campus_name in title:
            best = item
            break

    location = best.get("location") or {}
    lat = location.get("lat")
    lng = location.get("lng")

    if lat is None or lng is None:
        raise RuntimeError("Campus result does not contain valid location coordinates")

    return float(lat), float(lng)


def resolve_campus_coordinate(session: requests.Session, campus_name: str, api_key: str) -> Tuple[float, float]:
    """Resolve campus center using region search in Tianjin."""
    params = {
        "key": api_key,
        "keyword": campus_name,
        "boundary": "region(天津,0)",
        "page_size": 5,
        "page_index": 1,
    }
    payload = request_place_search(session, params)
    candidates = payload.get("data") or []
    lat, lng = pick_campus_center(candidates, campus_name)
    logging.info("Resolved campus center: %s -> (%.6f, %.6f)", campus_name, lat, lng)
    return lat, lng


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_text(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"\s+", "", value)
    return value


def normalize_category(raw_item: Dict[str, Any]) -> str:
    category = raw_item.get("category")
    if isinstance(category, list):
        return ",".join(str(x) for x in category)
    if isinstance(category, dict):
        return ",".join(f"{k}:{v}" for k, v in category.items())
    if category:
        return str(category)

    # some place APIs may place category in ad_info
    ad_info = raw_item.get("ad_info") or {}
    if ad_info.get("city_code"):
        return ""
    return ""


def map_poi_record(raw_item: Dict[str, Any], source_keyword: str) -> POIRecord:
    location = raw_item.get("location") or {}
    ad_info = raw_item.get("ad_info") or {}

    record = POIRecord(
        source_id=str(raw_item.get("id") or "").strip(),
        name=str(raw_item.get("title") or raw_item.get("name") or "").strip(),
        address=str(raw_item.get("address") or "").strip(),
        category=normalize_category(raw_item),
        lat=to_float(location.get("lat")),
        lng=to_float(location.get("lng")),
        distance=to_float(raw_item.get("_distance") or raw_item.get("distance")),
        province=str(ad_info.get("province") or "").strip(),
        city=str(ad_info.get("city") or "").strip(),
        district=str(ad_info.get("district") or "").strip(),
        adcode=str(ad_info.get("adcode") or raw_item.get("adcode") or "").strip(),
        source_keyword=source_keyword,
        source=SOURCE_NAME,
    )
    return record


def build_dedup_key(record: POIRecord) -> str:
    """
    Preferred dedup strategy:
    1) source_id
    2) normalized(name + address)
    """
    if record.source_id:
        return f"id::{record.source_id}"

    name = normalize_text(record.name)
    address = normalize_text(record.address)
    return f"name_addr::{name}::{address}"


def collect_for_keyword(
    session: requests.Session,
    api_key: str,
    keyword: str,
    center_lat: float,
    center_lng: float,
    radius: int,
    max_pages: int,
    page_size: int,
) -> List[POIRecord]:
    """Collect nearby records for one keyword with pagination."""
    all_records: List[POIRecord] = []

    for page_index in range(1, max_pages + 1):
        params = {
            "key": api_key,
            "keyword": keyword,
            "boundary": f"nearby({center_lat},{center_lng},{radius})",
            "orderby": "_distance",
            "page_size": page_size,
            "page_index": page_index,
        }

        try:
            payload = request_place_search(session, params)
        except Exception as exc:  # noqa: BLE001
            logging.error("Keyword=%s page=%s failed: %s", keyword, page_index, exc)
            break

        items = payload.get("data") or []
        if not items:
            logging.info("Keyword=%s page=%s returned empty. stop.", keyword, page_index)
            break

        page_records = [map_poi_record(item, keyword) for item in items]
        all_records.extend(page_records)
        logging.info(
            "Keyword=%s page=%s fetched=%s total_for_keyword=%s",
            keyword,
            page_index,
            len(page_records),
            len(all_records),
        )

        if len(items) < page_size:
            break

    return all_records


def deduplicate_records(records: List[POIRecord]) -> List[POIRecord]:
    """Deduplicate records and merge source keywords for same merchant."""
    merged: Dict[str, Dict[str, Any]] = {}

    for record in records:
        key = build_dedup_key(record)
        row = record.as_dict()

        if key not in merged:
            row["_keyword_set"] = {record.source_keyword}
            merged[key] = row
            continue

        old = merged[key]
        old["_keyword_set"].add(record.source_keyword)

        # fill missing info if old is empty
        for field in ["source_id", "address", "category", "province", "city", "district", "adcode"]:
            if not old.get(field) and row.get(field):
                old[field] = row[field]

        # keep nearest distance when multiple keyword hits exist
        old_dist = to_float(old.get("distance"))
        new_dist = to_float(row.get("distance"))
        if old_dist is None or (new_dist is not None and new_dist < old_dist):
            old["distance"] = new_dist

        # keep coordinates if missing
        if old.get("lat") is None and row.get("lat") is not None:
            old["lat"] = row["lat"]
        if old.get("lng") is None and row.get("lng") is not None:
            old["lng"] = row["lng"]

    final_rows: List[POIRecord] = []
    for row in merged.values():
        keyword_set = row.pop("_keyword_set", set())
        row["source_keyword"] = ",".join(sorted(keyword_set))
        final_rows.append(POIRecord(**row))

    return final_rows


def save_to_csv(records: List[POIRecord], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.as_dict())
    logging.info("CSV saved: %s (rows=%s)", csv_path, len(records))


def create_table_if_needed(conn: sqlite3.Connection, table_name: str) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            source_id TEXT,
            name TEXT,
            address TEXT,
            category TEXT,
            lat REAL,
            lng REAL,
            distance REAL,
            province TEXT,
            city TEXT,
            district TEXT,
            adcode TEXT,
            source_keyword TEXT,
            source TEXT
        )
        """
    )
    conn.commit()


def save_to_sqlite(records: List[POIRecord], db_path: Path, table_name: str) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        create_table_if_needed(conn, table_name)
        conn.execute(f"DELETE FROM {table_name}")

        insert_sql = f"""
        INSERT INTO {table_name} (
            source_id, name, address, category, lat, lng, distance,
            province, city, district, adcode, source_keyword, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        rows = [
            (
                r.source_id,
                r.name,
                r.address,
                r.category,
                r.lat,
                r.lng,
                r.distance,
                r.province,
                r.city,
                r.district,
                r.adcode,
                r.source_keyword,
                r.source,
            )
            for r in records
        ]

        conn.executemany(insert_sql, rows)
        conn.commit()
        logging.info("SQLite saved: %s table=%s (rows=%s)", db_path, table_name, len(records))
    finally:
        conn.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    api_key = ensure_api_key_loaded()

    session = build_http_session()

    center_lat, center_lng = resolve_campus_coordinate(session, CAMPUS_NAME, api_key)

    all_raw_records: List[POIRecord] = []
    for kw in KEYWORDS:
        records = collect_for_keyword(
            session=session,
            api_key=api_key,
            keyword=kw,
            center_lat=center_lat,
            center_lng=center_lng,
            radius=DEFAULT_RADIUS,
            max_pages=MAX_PAGES_PER_KEYWORD,
            page_size=PAGE_SIZE,
        )
        all_raw_records.extend(records)

    logging.info("Raw records collected (before dedup): %s", len(all_raw_records))
    deduped_records = deduplicate_records(all_raw_records)
    logging.info("Records after dedup: %s", len(deduped_records))

    # sort for consistent output
    deduped_records.sort(key=lambda x: (x.distance if x.distance is not None else 10**9, x.name))

    save_to_csv(deduped_records, CSV_PATH)
    save_to_sqlite(deduped_records, DB_PATH, DB_TABLE)

    logging.info("Done. Outputs:")
    logging.info("- %s", CSV_PATH)
    logging.info("- %s", DB_PATH)


if __name__ == "__main__":
    main()
