#!/usr/bin/env python3
"""
Economic Calendar Fetcher
从 investing.com 抓取经济日历数据
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("缺少依赖，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://cn.investing.com/economic-calendar/",
}

COUNTRY_MAP = {
    "CN": "36",   # 中国
    "US": "5",    # 美国
    "EU": "72",   # 欧元区
    "JP": "35",   # 日本
    "GB": "4",    # 英国
}

IMPORTANCE_MAP = {
    "high": [3],
    "medium": [2, 3],
    "all": [1, 2, 3],
}

IMPORTANCE_EMOJI = {1: "🟢", 2: "🟡", 3: "🔴"}
IMPORTANCE_LABEL = {1: "低", 2: "中", 3: "高"}


def fetch_calendar(days=7, country="ALL", importance="high"):
    today = datetime.now()
    end_date = today + timedelta(days=days)

    date_from = today.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

    # 构建请求参数
    data = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "timeZone": "8",  # UTC+8
        "timeFilter": "timeRemain",
        "currentTab": "custom",
        "limit_from": "0",
    }

    if country != "ALL" and country in COUNTRY_MAP:
        data["countries[]"] = COUNTRY_MAP[country]

    importance_levels = IMPORTANCE_MAP.get(importance, [3])
    for level in importance_levels:
        data[f"importance[{level}]"] = "on"

    try:
        resp = requests.post(
            "https://cn.investing.com/economic-calendar/Service/getCalendarFilteredData",
            headers=HEADERS,
            data=data,
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("data", ""), date_from, date_to
    except Exception as e:
        return None, date_from, date_to


def parse_html_to_events(html_data):
    """简单解析 HTML 表格，提取事件"""
    if not html_data:
        return []

    try:
        from html.parser import HTMLParser

        class CalendarParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.events = []
                self.current_row = {}
                self.in_row = False
                self.current_cell = None
                self.cell_index = 0
                self.current_text = ""

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "tr":
                    cls = attrs_dict.get("class", "")
                    if "js-event-item" in cls:
                        self.in_row = True
                        self.current_row = {}
                        self.cell_index = 0
                        # 获取重要性
                        imp = attrs_dict.get("data-importance", "1")
                        self.current_row["importance"] = int(imp) if imp else 1
                        self.current_row["event_id"] = attrs_dict.get("event_attr_id", "")
                elif tag == "td" and self.in_row:
                    self.current_cell = attrs_dict.get("class", "")
                    self.current_text = ""

            def handle_endtag(self, tag):
                if tag == "tr" and self.in_row:
                    if self.current_row:
                        self.events.append(self.current_row.copy())
                    self.in_row = False
                elif tag == "td" and self.in_row:
                    text = self.current_text.strip()
                    cls = self.current_cell or ""
                    if "time" in cls:
                        self.current_row["time"] = text
                    elif "flagCur" in cls:
                        self.current_row["currency"] = text
                    elif "event" in cls:
                        self.current_row["event"] = text
                    elif "actual" in cls:
                        self.current_row["actual"] = text
                    elif "forecast" in cls:
                        self.current_row["forecast"] = text
                    elif "prev" in cls:
                        self.current_row["prev"] = text
                    self.cell_index += 1
                    self.current_cell = None

            def handle_data(self, data):
                if self.in_row and self.current_cell is not None:
                    self.current_text += data

        parser = CalendarParser()
        parser.feed(html_data)
        return parser.events
    except Exception:
        return []


def format_output(events, date_from, date_to, importance_filter):
    importance_levels = IMPORTANCE_MAP.get(importance_filter, [3])

    print(f"\n📅 经济日历 {date_from} ~ {date_to}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    filtered = [e for e in events if e.get("importance", 1) in importance_levels]

    if not filtered:
        print("  暂无符合条件的事件数据")
        print("\n💡 建议使用 Tavily 搜索获取最新经济日历")
        return

    for e in filtered:
        imp = e.get("importance", 1)
        emoji = IMPORTANCE_EMOJI.get(imp, "🟢")
        label = IMPORTANCE_LABEL.get(imp, "低")
        time = e.get("time", "--:--")
        currency = e.get("currency", "")
        event = e.get("event", "未知事件")
        forecast = e.get("forecast", "-")
        prev = e.get("prev", "-")
        actual = e.get("actual", "")

        actual_str = f" | 实际：{actual}" if actual else ""
        print(f"{emoji} {label}影响 | {time} | {currency} | {event}")
        print(f"   预期：{forecast} | 前值：{prev}{actual_str}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"共 {len(filtered)} 条事件")


def main():
    parser = argparse.ArgumentParser(description="经济日历获取器")
    parser.add_argument("--days", type=int, default=7, help="未来天数（默认7）")
    parser.add_argument("--country", default="ALL", help="国家代码：CN/US/EU/JP/GB/ALL（默认ALL）")
    parser.add_argument("--importance", default="high", choices=["high", "medium", "all"], help="重要程度（默认high）")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    args = parser.parse_args()

    print(f"🔍 正在获取经济日历（未来{args.days}天，国家：{args.country}，重要程度：{args.importance}）...")

    html_data, date_from, date_to = fetch_calendar(args.days, args.country, args.importance)

    if html_data is None:
        print("⚠️  直接抓取失败，切换到 Tavily 搜索备用方案...\n")
        import subprocess, shlex
        today_str = datetime.now().strftime("%Y-%m-%d")
        query = f"本周经济日历 重要财经数据 中国美国 {today_str}"
        tavily_script = "~/.openclaw/skills/tavily-search/scripts/search.sh"
        cmd = f'bash {tavily_script} "{query}" 8'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"📅 经济日历搜索结果 {date_from} ~ {date_to}")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for item in data.get("results", []):
                    print(f"📌 {item['title']}")
                    print(f"   {item['content'][:200]}...")
                    print()
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            except Exception:
                print(result.stdout)
        else:
            print("❌ 备用搜索也失败，请检查网络连接")
            sys.exit(1)
        return

    events = parse_html_to_events(html_data)

    if args.json:
        print(json.dumps(events, ensure_ascii=False, indent=2))
    else:
        format_output(events, date_from, date_to, args.importance)


if __name__ == "__main__":
    main()
