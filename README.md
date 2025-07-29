# gitreport

📊 A lightweight CLI tool to generate visual Git activity reports from any local repo.

## 📦 Features

- Commit graph over time
- Author contribution breakdown
- Commit heatmap (weekday × hour)
- LOC effort trend (insertions vs deletions)
- Output as `.png` files in a chosen folder

## 🚀 Installation

```bash
# Clone and add to your PATH
git clone https://github.com/yourname/gitreport.git
cd gitreport
chmod +x bin/gitreport
echo 'export PATH="$PWD/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
```

## ✅ Dependencies

Ensure the following Python packages are installed:

```bash
pip install matplotlib seaborn pandas gitpython
```

## 🧠 Usage

```bash
gitreport --repo /path/to/repo --since "3 months ago" --out ~/Reports/my-repo
```

- `--repo`: Git repo path (default: current dir)
- `--since`: Look back period (e.g., "90 days ago", "2024-05-01")
- `--out`: Output folder for `.png` files

## 📁 Output

```
your-output-folder/
├── authors.png
├── commits-over-time.png
├── commit-heatmap.png
├── loc-effort.png
```

## 📝 Coming soon

- Markdown + PDF summary
- Optional HTML dashboard
- GitHub Action mode

## 📊 Dashboard

A simple React + Vite dashboard is included in `dashboard/`. It visualizes commit
activity using the JSON data in `dashboard/public/data/git-data.json`.

Generate fresh data from any repository:

```bash
python scripts/export_git_data.py --repo /path/to/repo --since "90 days ago" \
  --out dashboard/public/data/git-data.json
```

Then run the development server:

```bash
cd dashboard
npm install
npm run dev
```

The dashboard will display commits over time, author breakdowns, an activity
heatmap, and code churn trends.

