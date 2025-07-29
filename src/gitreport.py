#!/usr/bin/env python3
import os, argparse, subprocess
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from git import Repo

sns.set_theme(style="darkgrid")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Git activity report.")
    parser.add_argument("--repo", default=".", help="Path to Git repo")
    parser.add_argument("--since", default="3 months ago", help="Time range (e.g., '90 days ago')")
    parser.add_argument("--out", default=".gitreport", help="Output directory")
    return parser.parse_args()

def resolve_since(since_string: str) -> str:
    try:
        days = int(since_string.split()[0])
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    except:
        return since_string

def run_git_command(cmd: str, repo_path: str) -> str:
    return subprocess.run(cmd, cwd=repo_path, shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, check=False).stdout.strip()

def save_git_metadata(repo_path: str, since: str, output_dir: Path) -> tuple[Path, Path, Path]:
    log_file = output_dir / "log-graph.txt"
    shortlog_file = output_dir / "shortlog-summary.txt"
    stat_file = output_dir / "commit-stat-summary.txt"

    log_file.write_text(run_git_command(f"git log --all --since='{since}' --graph --decorate --oneline", repo_path))
    shortlog_file.write_text(run_git_command(f"git shortlog -sne --since='{since}' --all", repo_path))
    stat_file.write_text(run_git_command(f"git log --since='{since}' --author='$(git config user.name)' --shortstat", repo_path))

    return log_file, shortlog_file, stat_file

def generate_markdown_summary(output_dir: Path, log_file: Path, shortlog_file: Path, stat_file: Path):
    md_path = Path(output_dir) / "summary.md"
    md_path.write_text(
        "# Git Activity Report\n\n"
        "## Commit Graph\n"
        "```\n"
        f"{log_file.read_text()}\n"
        "```\n\n"
        "## Top Contributors\n"
        "```\n"
        f"{shortlog_file.read_text()}\n"
        "```\n\n"
        "## LOC Stats\n"
        "```\n"
        f"{stat_file.read_text()}\n"
        "```\n\n"
        "## Commits Over Time\n"
        "![Commits](commits-over-time.png)\n\n"
        "## Author Contribution\n"
        "![Authors](authors.png)\n\n"
        "## Commit Heatmap\n"
        "![Heatmap](commit-heatmap.png)\n\n"
        "## Code Churn\n"
        "![LOC Effort](loc-effort.png)\n"
    )
    return md_path

def convert_to_pdf(markdown_path: Path) -> None:
    pdf_path = markdown_path.with_suffix(".pdf")
    try:
        subprocess.run([
            "pandoc", str(markdown_path),
            "-o", str(pdf_path),
            "--resource-path", str(markdown_path.parent),
            "--pdf-engine=xelatex"
        ], check=True)
        print(f"✅ PDF summary created: {pdf_path}")
    except Exception as e:
        print(f"⚠️  Pandoc not available or failed: {e}")

def convert_to_html(markdown_path: Path) -> None:
    html_path = markdown_path.with_suffix(".html")
    try:
        subprocess.run(["pandoc", str(markdown_path), "-o", str(html_path)], check=True)
        print(f"✅ HTML summary created: {html_path}")
    except Exception as e:
        print(f"⚠️  Pandoc not available or failed: {e}")

def generate_visuals(df: DataFrame, output_dir: Path) -> None:
    # Commits over time
    plt.figure(figsize=(14, 6))
    df.groupby("date").size().plot(marker='o')
    plt.title("Commits Per Day")
    plt.ylabel("Commits")
    plt.xlabel("Date")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "commits-over-time.png")
    plt.close()

    # Authors
    plt.figure(figsize=(10, 6))
    df["author"].value_counts().plot(kind="barh", color="steelblue")
    plt.title("Commit Contributions by Author")
    plt.xlabel("Commits")
    plt.tight_layout()
    plt.savefig(output_dir / "authors.png")
    plt.close()

    # Heatmap of activity
    heatmap_data = df.groupby(["dow", "hour"]).size().unstack().fillna(0)
    heatmap_data = heatmap_data.reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    plt.figure(figsize=(14, 5))
    sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.5, cbar_kws={"label": "Commits"})
    plt.title("Commit Frequency Heatmap (Weekday × Hour)")
    plt.xlabel("Hour of Day")
    plt.ylabel("Day of Week")
    plt.tight_layout()
    plt.savefig(output_dir / "commit-heatmap.png")
    plt.close()

    # Insertions/Deletions per day
    df_daily = df.set_index("timestamp").resample("D")[["insertions", "deletions"]].sum()

    plt.figure(figsize=(14, 6))
    df_daily.plot.area(stacked=False, alpha=0.6, ax=plt.gca())
    plt.title("Code Churn Over Time (Insertions vs Deletions)")
    plt.ylabel("Lines of Code")
    plt.xlabel("Date")
    plt.xticks(rotation=45)
    plt.legend(["Insertions", "Deletions"])
    plt.tight_layout()
    plt.savefig(output_dir / "loc-effort.png")
    plt.close()

def main() -> None:
    args = parse_args()
    repo_path = os.path.abspath(args.repo)
    output_dir = Path(args.out).expanduser().resolve()
    os.makedirs(str(output_dir), exist_ok=True)

    repo = Repo(repo_path)
    since = resolve_since(args.since)

    commits = []
    for commit in repo.iter_commits('--all', since=since):
        commits.append({
            "hash": commit.hexsha,
            "author": commit.author.name,
            "timestamp": datetime.fromtimestamp(commit.committed_date),
            "insertions": commit.stats.total["insertions"],
            "deletions": commit.stats.total["deletions"],
            "files": commit.stats.total["files"],
        })

    df = pd.DataFrame(commits)
    if df.empty:
        print("⚠️ No commits found for the given time range.")
        return

    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["dow"] = df["timestamp"].dt.day_name()

    generate_visuals(df, output_dir)
    log_file, shortlog_file, stat_file = save_git_metadata(repo_path, since, output_dir)
    md_path = generate_markdown_summary(output_dir, log_file, shortlog_file, stat_file)
    convert_to_pdf(md_path)
    convert_to_html(md_path)
    print(f"✅ All output saved to: {output_dir}")

if __name__ == "__main__":
    main()
