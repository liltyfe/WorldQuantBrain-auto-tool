import argparse
import base64
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_URL_FILTERS = ["alphas/", "simulations"]
MAX_SAMPLE_LENGTH = 160


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查 WorldQuant Brain 导出的 HAR/JSON 数据包，并生成字段清单。"
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        help="输入文件路径，支持 .har / .json",
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        help="输出目录，默认在输入文件同级生成 inspect_<文件名>",
    )
    parser.add_argument(
        "--url-filter",
        dest="url_filters",
        default=",".join(DEFAULT_URL_FILTERS),
        help="HAR 模式下的 URL 过滤关键字，多个关键字用英文逗号分隔",
    )
    parser.add_argument(
        "--include-non-json",
        action="store_true",
        help="保留匹配到的非 JSON 响应文本",
    )
    return parser


def prompt_if_missing(value: str | None, prompt: str) -> str:
    if value:
        return value
    return input(prompt).strip()


def parse_filters(raw_filters: str) -> list[str]:
    items = [item.strip() for item in raw_filters.split(",")]
    return [item for item in items if item]


def ensure_output_dir(input_path: Path, output_dir_arg: str | None) -> Path:
    if output_dir_arg:
        return Path(output_dir_arg)
    return input_path.parent / f"inspect_{input_path.stem}"


def safe_filename(value: str) -> str:
    cleaned = []
    for char in value:
        if char.isalnum() or char in ("-", "_", "."):
            cleaned.append(char)
        else:
            cleaned.append("_")
    result = "".join(cleaned).strip("._")
    return result or "payload"


def looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


def decode_har_content(content: dict[str, Any]) -> str:
    text = content.get("text", "") or ""
    encoding = content.get("encoding")
    if encoding == "base64":
        try:
            decoded = base64.b64decode(text)
            return decoded.decode("utf-8", errors="replace")
        except Exception:
            return text
    return text


def truncate_sample(value: Any) -> str:
    if isinstance(value, str):
        sample = value
    else:
        sample = json.dumps(value, ensure_ascii=False)
    sample = sample.replace("\r", "\\r").replace("\n", "\\n")
    if len(sample) > MAX_SAMPLE_LENGTH:
        return sample[: MAX_SAMPLE_LENGTH - 3] + "..."
    return sample


def value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def collect_field_rows(
    node: Any,
    field_path: str,
    rows: list[dict[str, Any]],
    source_name: str,
    source_url: str,
    http_status: int | str | None,
    captured_at: str | None,
) -> None:
    rows.append(
        {
            "source_name": source_name,
            "source_url": source_url,
            "http_status": http_status or "",
            "captured_at": captured_at or "",
            "field_path": field_path or "<root>",
            "value_type": value_type(node),
            "sample_value": truncate_sample(node),
        }
    )

    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{field_path}.{key}" if field_path else str(key)
            collect_field_rows(value, next_path, rows, source_name, source_url, http_status, captured_at)
        return

    if isinstance(node, list):
        item_path = f"{field_path}[]" if field_path else "[]"
        for item in node:
            collect_field_rows(item, item_path, rows, source_name, source_url, http_status, captured_at)


def save_json(path: Path, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def load_json_file(input_path: Path) -> Any:
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_payloads_from_har(
    har_data: dict[str, Any],
    url_filters: list[str],
    include_non_json: bool,
) -> list[dict[str, Any]]:
    entries = har_data.get("log", {}).get("entries", [])
    payloads = []

    for index, entry in enumerate(entries, start=1):
        request = entry.get("request", {})
        response = entry.get("response", {})
        content = response.get("content", {})
        url = request.get("url", "")
        method = request.get("method", "")

        if url_filters and not any(keyword in url for keyword in url_filters):
            continue

        body_text = decode_har_content(content)
        mime_type = content.get("mimeType", "")
        is_json = "json" in mime_type.lower() or looks_like_json(body_text)
        parsed_body = None
        if is_json and body_text:
            try:
                parsed_body = json.loads(body_text)
            except json.JSONDecodeError:
                parsed_body = None

        if parsed_body is None and not include_non_json:
            continue

        url_stub = safe_filename(url.split("://", 1)[-1])
        source_name = f"{index:03d}_{method}_{url_stub}"
        payloads.append(
            {
                "source_name": source_name,
                "source_url": url,
                "http_status": response.get("status"),
                "captured_at": entry.get("startedDateTime"),
                "request_method": method,
                "mime_type": mime_type,
                "body": parsed_body if parsed_body is not None else body_text,
                "body_is_json": parsed_body is not None,
            }
        )

    return payloads


def extract_payloads_from_json(input_path: Path, data: Any) -> list[dict[str, Any]]:
    return [
        {
            "source_name": safe_filename(input_path.stem),
            "source_url": str(input_path),
            "http_status": "",
            "captured_at": "",
            "request_method": "",
            "mime_type": "application/json",
            "body": data,
            "body_is_json": True,
        }
    ]


def write_payload_files(output_dir: Path, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_dir = output_dir / "raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)

    response_index = []
    for payload in payloads:
        suffix = ".json" if payload["body_is_json"] else ".txt"
        file_name = payload["source_name"] + suffix
        file_path = raw_dir / file_name

        if payload["body_is_json"]:
            save_json(file_path, payload["body"])
        else:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(str(payload["body"]))

        response_index.append(
            {
                "source_name": payload["source_name"],
                "source_url": payload["source_url"],
                "http_status": payload["http_status"],
                "captured_at": payload["captured_at"],
                "request_method": payload["request_method"],
                "mime_type": payload["mime_type"],
                "saved_file": str(file_path),
                "body_is_json": payload["body_is_json"],
                "top_level_keys": list(payload["body"].keys()) if isinstance(payload["body"], dict) else [],
            }
        )

    return response_index


def build_field_inventory(payloads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows = []
    per_response_summary = []

    for payload in payloads:
        body = payload["body"]
        if not payload["body_is_json"]:
            continue

        response_rows: list[dict[str, Any]] = []
        collect_field_rows(
            node=body,
            field_path="",
            rows=response_rows,
            source_name=payload["source_name"],
            source_url=payload["source_url"],
            http_status=payload["http_status"],
            captured_at=payload["captured_at"],
        )
        all_rows.extend(response_rows)
        per_response_summary.append(
            {
                "source_name": payload["source_name"],
                "source_url": payload["source_url"],
                "http_status": payload["http_status"],
                "captured_at": payload["captured_at"],
                "top_level_keys": list(body.keys()) if isinstance(body, dict) else [],
                "field_count": len(response_rows),
            }
        )

    return all_rows, per_response_summary


def build_field_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["field_path"]
        if key not in grouped:
            grouped[key] = {
                "field_path": key,
                "value_types": set(),
                "occurrences": 0,
                "sample_value": row["sample_value"],
                "sample_source": row["source_name"],
            }
        grouped[key]["value_types"].add(row["value_type"])
        grouped[key]["occurrences"] += 1

    summary = []
    for item in sorted(grouped.values(), key=lambda current: current["field_path"]):
        summary.append(
            {
                "field_path": item["field_path"],
                "value_types": ",".join(sorted(item["value_types"])),
                "occurrences": item["occurrences"],
                "sample_source": item["sample_source"],
                "sample_value": item["sample_value"],
            }
        )
    return summary


def build_field_inventory_json(
    response_summaries: list[dict[str, Any]],
    field_rows: list[dict[str, Any]],
    field_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for row in field_rows:
        source_name = row["source_name"]
        rows_by_source.setdefault(source_name, []).append(
            {
                "field_path": row["field_path"],
                "value_type": row["value_type"],
                "sample_value": row["sample_value"],
            }
        )

    responses = []
    for summary in response_summaries:
        responses.append(
            {
                **summary,
                "fields": rows_by_source.get(summary["source_name"], []),
            }
        )

    return {
        "responses": responses,
        "field_summary": field_summary,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def run_inspection(input_path: Path, output_dir: Path, url_filters: list[str], include_non_json: bool) -> dict[str, Any]:
    data = load_json_file(input_path)

    if input_path.suffix.lower() == ".har":
        payloads = extract_payloads_from_har(data, url_filters, include_non_json)
    else:
        payloads = extract_payloads_from_json(input_path, data)

    output_dir.mkdir(parents=True, exist_ok=True)
    response_index = write_payload_files(output_dir, payloads)
    field_rows, response_summaries = build_field_inventory(payloads)
    field_summary = build_field_summary(field_rows)

    save_json(output_dir / "response_index.json", response_index)
    save_json(
        output_dir / "field_inventory.json",
        build_field_inventory_json(response_summaries, field_rows, field_summary),
    )
    write_csv(
        output_dir / "field_inventory.csv",
        field_rows,
        [
            "source_name",
            "source_url",
            "http_status",
            "captured_at",
            "field_path",
            "value_type",
            "sample_value",
        ],
    )
    write_csv(
        output_dir / "field_summary.csv",
        field_summary,
        [
            "field_path",
            "value_types",
            "occurrences",
            "sample_source",
            "sample_value",
        ],
    )

    return {
        "payload_count": len(payloads),
        "json_payload_count": sum(1 for payload in payloads if payload["body_is_json"]),
        "field_row_count": len(field_rows),
        "output_dir": str(output_dir),
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_value = prompt_if_missing(args.input_path, "请输入导出的 HAR/JSON 文件路径: ")
    if not input_value:
        print("[错误] 输入文件路径不能为空")
        return

    input_path = Path(input_value)
    if not input_path.exists():
        print(f"[错误] 输入文件不存在: {input_path}")
        return

    output_value = args.output_dir
    if not output_value:
        print("\n请输入输出目录 [默认: 输入文件同级 inspect_<文件名>]:")
        output_value = input("输出目录: ").strip()

    output_dir = ensure_output_dir(input_path, output_value or None)
    url_filters = parse_filters(args.url_filters)

    print("\n" + "=" * 60)
    print("WorldQuant Brain 数据包检查工具")
    print("=" * 60)
    print(f"输入文件: {input_path}")
    print(f"输出目录: {output_dir}")
    print(f"URL 过滤: {url_filters if input_path.suffix.lower() == '.har' else 'JSON 模式下不使用'}")
    print("-" * 60)

    result = run_inspection(
        input_path=input_path,
        output_dir=output_dir,
        url_filters=url_filters,
        include_non_json=args.include_non_json,
    )

    print(f"[完成] 共提取响应 {result['payload_count']} 个")
    print(f"[完成] 其中 JSON 响应 {result['json_payload_count']} 个")
    print(f"[完成] 共发现字段记录 {result['field_row_count']} 行")
    print(f"[输出] 原始响应目录: {output_dir / 'raw_responses'}")
    print(f"[输出] 字段清单: {output_dir / 'field_inventory.csv'}")
    print(f"[输出] 字段汇总: {output_dir / 'field_summary.csv'}")
    print(f"[输出] 响应索引: {output_dir / 'response_index.json'}")


if __name__ == "__main__":
    main()
