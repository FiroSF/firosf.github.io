#!/usr/bin/env python3
import os
import sys
import re
import csv
import argparse
from datetime import datetime, timezone, timedelta

# KST Timezone (+09:00)
KST = timezone(timedelta(hours=9))


def format_contest_time(time_str):
    """Convert time string like '0:01:28.963' or '1:07:44.530' into 'HH:MM' or 'HH:MM:SS'"""
    if not time_str:
        return "-"
    time_str = time_str.strip()
    if "." in time_str:
        time_str = time_str.split(".")[0]
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return f"{int(h):02d}:{int(m):02d}"
    elif len(parts) == 2:
        m, s = parts
        return f"{int(m):02d}:{int(s):02d}"
    return time_str


def get_verdict_html(verdict):
    """Format verdict string to colored HTML span"""
    v_upper = verdict.strip().upper()
    if v_upper == "AC" or v_upper == "ACCEPTED":
        return '<span style="color:#33cc33; font-weight:bold;">AC</span>'
    elif v_upper in ["WA", "WRONG ANSWER"]:
        return '<span style="color:#ff2222; font-weight:bold;">WA</span>'
    elif v_upper in ["TLE", "TIME LIMIT EXCEEDED"]:
        return '<span style="color:#ff2222; font-weight:bold;">TLE</span>'
    elif v_upper in ["MLE", "MEMORY LIMIT EXCEEDED"]:
        return '<span style="color:#ff2222; font-weight:bold;">MLE</span>'
    elif v_upper in ["RTE", "RUNTIME ERROR"]:
        return '<span style="color:#ff2222; font-weight:bold;">RTE</span>'
    elif v_upper in ["CE", "COMPILATION ERROR"]:
        return '<span style="color:#999999; font-weight:bold;">CE</span>'
    return f'<span style="font-weight:bold;">{verdict}</span>'


def slugify(text):
    """Convert title string to filename-safe slug"""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text or "contest"


def read_source_code(csv_base_dir, folder_rel_path):
    """Try to read cpp/py code from submission folder"""
    if not folder_rel_path:
        return ""
    full_folder = os.path.join(csv_base_dir, folder_rel_path)
    if not os.path.isdir(full_folder):
        return ""
    
    code_files = [f for f in os.listdir(full_folder) if f.endswith((".cpp", ".cc", ".cxx", ".py", ".c", ".java"))]
    if not code_files:
        return ""
    
    code_file_path = os.path.join(full_folder, sorted(code_files)[0])
    try:
        with open(code_file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Generate Centroid Cup / Onsite Contest Post from Submissions CSV")
    parser.add_argument("csv_path", nargs="?", help="Path to submissions.csv file")
    parser.add_argument("post_name", nargs="?", help="Title or name of the post")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing post file without asking")
    args = parser.parse_args()

    # Fixed output directory: _posts/Contest
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "_posts", "Contest")

    # Prompt for csv_path if not provided
    csv_path = args.csv_path
    if not csv_path:
        default_csv = os.path.join(base_dir, "submissions.csv")
        prompt = f"Enter CSV file path [{default_csv}]: " if os.path.exists(default_csv) else "Enter CSV file path: "
        user_input = input(prompt).strip()
        csv_path = user_input if user_input else default_csv

    if not os.path.exists(csv_path):
        print(f"[Error] CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    csv_base_dir = os.path.dirname(os.path.abspath(csv_path))

    # Prompt for post_name if not provided
    post_name = args.post_name
    if not post_name:
        post_name = input("Enter post title (e.g. Centroid Cup 2026 후기): ").strip()
        if not post_name:
            post_name = "Centroid Cup 2026 후기"

    print(f"[*] Reading submissions from: {csv_path}")
    print(f"[*] Post Title: {post_name}")

    # Parse CSV
    submissions = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            submissions.append(row)

    if not submissions:
        print("[Error] No submissions found in CSV file.", file=sys.stderr)
        sys.exit(1)

    # Group problems and map problem letter
    problems_dict = {}
    problem_order = []

    for sub in submissions:
        p_id = sub.get("problem_id", "").strip()
        p_label = sub.get("problem_label", "").strip()
        p_name = sub.get("problem_name", "").strip()

        key = p_id or p_label or p_name
        if key not in problems_dict:
            letter = chr(ord("A") + len(problem_order))
            problems_dict[key] = {
                "letter": letter,
                "id": p_id,
                "label": p_label,
                "name": p_name,
                "submissions": [],
                "solved": False,
                "ac_time": None,
                "ac_attempt": None,
                "last_code": "",
            }
            problem_order.append(key)

        p_info = problems_dict[key]
        attempt_num = len(p_info["submissions"]) + 1
        verdict = sub.get("verdict", "").strip()
        c_time = format_contest_time(sub.get("contest_time", ""))
        folder = sub.get("folder", "").strip()

        # Try to read source code
        code = read_source_code(csv_base_dir, folder)
        if code:
            p_info["last_code"] = code

        sub_info = {
            "sub_id": sub.get("submission_id", ""),
            "contest_time": c_time,
            "verdict": verdict,
            "verdict_html": get_verdict_html(verdict),
            "attempt": attempt_num,
            "problem_letter": p_info["letter"],
            "problem_label": p_label,
            "problem_name": p_name,
        }
        p_info["submissions"].append(sub_info)

        if verdict.upper() in ["AC", "ACCEPTED"] and not p_info["solved"]:
            p_info["solved"] = True
            p_info["ac_time"] = c_time
            p_info["ac_attempt"] = attempt_num

    # Chronological timeline rows
    timeline_rows = []
    problem_attempt_counter = {}
    for sub in submissions:
        p_id = sub.get("problem_id", "").strip()
        p_label = sub.get("problem_label", "").strip()
        p_name = sub.get("problem_name", "").strip()
        key = p_id or p_label or p_name

        p_info = problems_dict[key]
        problem_attempt_counter[key] = problem_attempt_counter.get(key, 0) + 1
        attempt_num = problem_attempt_counter[key]

        c_time = format_contest_time(sub.get("contest_time", ""))
        verdict = sub.get("verdict", "").strip()
        v_html = get_verdict_html(verdict)

        label_display = f"**{p_info['letter']} ({p_label})**" if p_label else f"**{p_info['letter']}**"
        timeline_rows.append(
            f"| `{c_time}` | {label_display} | {v_html} | {attempt_num}트 | 대회 중 |"
        )

    # Build Markdown Content
    now = datetime.now(KST)
    date_str = now.strftime("%Y-%m-%d %H:%M:%S +0900")
    file_date = now.strftime("%Y-%m-%d")

    slug = slugify(post_name)
    folder_slug = re.sub(r"[^\w]", "", slug.lower())
    img_relative_path = f"/assets/img/posts/contest/{folder_slug}"
    img_dir = os.path.join(base_dir, "assets", "img", "posts", "contest", folder_slug)
    os.makedirs(img_dir, exist_ok=True)

    md_lines = []
    # Frontmatter
    md_lines.append("---")
    md_lines.append(f'title: "{post_name}"')
    md_lines.append(f"date: {date_str}")
    md_lines.append("last_modified_at:")
    md_lines.append("categories: [온사이트]")
    md_lines.append("tags: [PS, CP, CentroidCup, onsite]")
    md_lines.append(f'description: "{post_name}와 해설"')
    md_lines.append("math: true")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("<!-- #999999 #33cc33 #44ddaa #2222ff #aa00ff #ff9900 #ff2222 -->")
    md_lines.append("")
    md_lines.append("## 개요")
    md_lines.append("")
    md_lines.append(f"{post_name}에 참여했다.")
    md_lines.append("")
    md_lines.append(f"* **일시**: {now.strftime('%Y-%m-%d %H:%M')} (KST)")
    md_lines.append("* **진행 시간**: 4시간")
    md_lines.append("")
    md_lines.append("| 제출 시간 | 문제 | 결과 | 시도 | 구분 |")
    md_lines.append("| :-------: | :---: | :---------------------------------------------------------------: | :---: | :------------------------------------------------------------: |")
    md_lines.extend(timeline_rows)
    md_lines.append("")
    md_lines.append("## 팀 구성")
    md_lines.append("")
    md_lines.append("팀원은 다음과 같다.")
    md_lines.append("")
    md_lines.append("* <a href=\"https://codeforces.com/profile/dongggle\" style=\"color: #ff9900; font-weight: bold;\">dongggle</a>")
    md_lines.append("* <a href=\"https://codeforces.com/profile/lapinism\" style=\"color: #00aaff; font-weight: bold;\">lapinism</a>")
    md_lines.append("* <a href=\"https://codeforces.com/profile/Firo_SF\" style=\"color: #aa00ff; font-weight: bold;\">Firo_SF</a> - 본인이다.")
    md_lines.append("")
    md_lines.append("## 대회 전")
    md_lines.append("")
    md_lines.append("")
    md_lines.append("## 대회 당일")
    md_lines.append("")
    md_lines.append("")
    md_lines.append("## 대회 중")
    md_lines.append("")
    md_lines.append("")
    md_lines.append("## 대회 후")
    md_lines.append("")
    md_lines.append("")
    md_lines.append("## 문제 풀이 및 복기")
    md_lines.append("")
    md_lines.append("### Overall")
    md_lines.append("")
    md_lines.append("문제 목록은 [여기](https://doj.kr/ko/categories/school/centroid/2026)에서 볼 수 있다.")
    md_lines.append("")

    # Problems
    for key in problem_order:
        p = problems_dict[key]
        letter = p["letter"]
        label = p["label"]
        name = p["name"]
        p_id = p["id"]

        title_display = f"{letter}번 {label} {name}".strip() if label else f"{letter}번 - {name}"
        p_url = f"https://doj.kr/ko/problems/{p_id}" if p_id else "https://doj.kr/ko/categories/school/centroid/2026"

        if p["solved"]:
            result_badge = f'<span style="color:#33cc33; font-weight:bold;">{p["ac_time"]} AC</span> ({p["ac_attempt"]}트)'
        elif p["submissions"]:
            result_badge = f'<span style="color:#ff2222; font-weight:bold;">WA</span> ({len(p["submissions"])}트)'
        else:
            result_badge = "-"

        md_lines.append(f"### [{title_display}]({p_url})")
        md_lines.append("")
        md_lines.append("|       풀이        |   코딩   |          체감 난이도           |          실제 난이도           | 대회 결과 |")
        md_lines.append("| :---------------: | :------: | :----------------------------: | :----------------------------: | :-------: |")
        md_lines.append(f'| - | - | {{% include tier.html t="??" %}} | {{% include tier.html t="??" %}} | {result_badge} |')
        md_lines.append("")
        md_lines.append("* 설명")
        md_lines.append("* **분류**: 해 구성하기")
        md_lines.append("")
        md_lines.append("#### 복기")
        md_lines.append("")
        md_lines.append("* ")
        md_lines.append("")
        md_lines.append("<details>")
        md_lines.append("<summary>코드</summary>")
        md_lines.append('<div markdown="1">')
        md_lines.append("")
        md_lines.append("{% raw %}")
        md_lines.append("```cpp")
        if p["last_code"]:
            md_lines.append(p["last_code"])
        else:
            md_lines.append("")
        md_lines.append("```")
        md_lines.append("{% endraw %}")
        md_lines.append("")
        md_lines.append("</div>")
        md_lines.append("</details>")
        md_lines.append("")
        md_lines.append("")

    md_lines.append("## 후기")
    md_lines.append("")
    md_lines.append(f"![score]({img_relative_path}/score.png)")
    md_lines.append(f"![rating]({img_relative_path}/rating.png)")
    md_lines.append("")
    md_lines.append("* ")
    md_lines.append("")

    # Save to _posts/Contest
    os.makedirs(target_dir, exist_ok=True)
    filename = f"{file_date}-{slug}.md"
    file_path = os.path.join(target_dir, filename)

    if os.path.exists(file_path) and not args.force:
        print(f"[!] File already exists: {file_path}")
        answer = input("Overwrite? [y/N]: ").strip().lower()
        if answer not in ["y", "yes"]:
            print("[x] Cancelled.")
            sys.exit(0)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\n[🎉 Success] Centroid Cup post generated successfully!")
    print(f"📝 Post File : {file_path}")
    print(f"🖼️  Image Dir : {img_dir} ({img_relative_path})")


if __name__ == "__main__":
    main()
