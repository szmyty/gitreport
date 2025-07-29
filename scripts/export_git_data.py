#!/usr/bin/env python3
"""Export aggregated git data to JSON for the dashboard."""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from git import Repo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export git history as JSON")
    parser.add_argument("--repo", default=".", help="Path to git repo")
    parser.add_argument(
        "--since",
        default="3 months ago",
        help="Look back period (e.g. '90 days ago')",
    )
    parser.add_argument(
        "--out",
        default="dashboard/public/data/git-data.json",
        help="Output JSON file path",
    )
    return parser.parse_args()


def resolve_since(since_string: str) -> str:
    try:
        days = int(since_string.split()[0])
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    except Exception:
        return since_string


def main() -> None:
    args = parse_args()
    repo_path = os.path.abspath(args.repo)
    repo = Repo(repo_path)
    since = resolve_since(args.since)

    commits = []
    for commit in repo.iter_commits("--all", since=since):
        commits.append(
            {
                "hash": commit.hexsha,
                "author": commit.author.name,
                "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
                "files": commit.stats.total["files"],
            }
        )

    df = pd.DataFrame(commits)
    if df.empty:
        print("No commits found for the given time range")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    daily = df.groupby(df["timestamp"].dt.date).size()
    authors = df["author"].value_counts()

    heatmap = (
        df.groupby([df["timestamp"].dt.day_name(), df["timestamp"].dt.hour])
        .size()
        .unstack()
        .fillna(0)
    )
    heatmap = heatmap.reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        fill_value=0,
    )

    churn = (
        df.set_index("timestamp")[["insertions", "deletions"]]
        .resample("D")
        .sum()
        .fillna(0)
        .astype(int)
    )

    out = {
        "commits": commits,
        "daily": {str(k): int(v) for k, v in daily.items()},
        "authors": authors.astype(int).to_dict(),
        "heatmap": {day: heatmap.loc[day].astype(int).to_dict() for day in heatmap.index},
        "churn": {
            k.strftime("%Y-%m-%d"): {"insertions": int(row["insertions"]), "deletions": int(row["deletions"])}
            for k, row in churn.iterrows()
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(out, f, indent=2)
    print(f"JSON data written to {out_path}")


if __name__ == "__main__":
    main()
