import { useEffect, useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
  MatrixController,
  MatrixElement
);

interface GitData {
  commits: {
    hash: string;
    author: string;
    timestamp: string;
    insertions: number;
    deletions: number;
    files: number;
  }[];
  daily: Record<string, number>;
  authors: Record<string, number>;
  heatmap: Record<string, Record<string, number>>;
  churn: Record<string, { insertions: number; deletions: number }>;
}

export default function App() {
  const [data, setData] = useState<GitData>();

  useEffect(() => {
    fetch('data/git-data.json')
      .then((res) => res.json())
      .then(setData)
      .catch((e) => console.error(e));
  }, []);

  if (!data) return <p>Loading...</p>;

  const dailyLabels = Object.keys(data.daily).sort();
  const dailyCounts = dailyLabels.map((d) => data.daily[d]);

  const authorLabels = Object.keys(data.authors);
  const authorCounts = authorLabels.map((a) => data.authors[a]);

  const heatDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  const heatHours = Array.from({length:24},(_,i)=>i);

  const churnLabels = Object.keys(data.churn).sort();
  const churnInsert = churnLabels.map((d)=>data.churn[d].insertions);
  const churnDelete = churnLabels.map((d)=>data.churn[d].deletions);

  return (
    <div>
      <h1>Git Report Dashboard</h1>
      <section>
        <h2>Commits Over Time</h2>
        <Line
          data={{
            labels: dailyLabels,
            datasets: [
              {
                label: 'Commits',
                data: dailyCounts,
                borderColor: 'steelblue',
                backgroundColor: 'rgba(70,130,180,0.5)',
                fill: true,
              },
            ],
          }}
          options={{ responsive: true, scales: { x: { ticks: { maxRotation: 90, minRotation: 45 } } } }}
        />
      </section>
      <section>
        <h2>Author Contributions</h2>
        <Bar
          data={{
            labels: authorLabels,
            datasets: [
              {
                label: 'Commits',
                data: authorCounts,
                backgroundColor: 'rgba(54,162,235,0.5)',
              },
            ],
          }}
          options={{ responsive: true, indexAxis: 'y' }}
        />
      </section>
      <section>
        <h2>Commit Frequency Heatmap</h2>
        <Bar
          data={{
            labels: heatHours,
            datasets: heatDays.map((day, idx) => ({
              label: day,
              data: heatHours.map((h) => data.heatmap[day]?.[h] || 0),
              backgroundColor: `hsl(${(idx * 50) % 360},70%,60%)`,
              stack: 'stack',
            })),
          }}
          options={{ responsive: true, scales: { x: { stacked: true }, y: { stacked: true } } }}
        />
      </section>
      <section>
        <h2>Code Churn Over Time</h2>
        <Line
          data={{
            labels: churnLabels,
            datasets: [
              {
                label: 'Insertions',
                data: churnInsert,
                borderColor: 'green',
                backgroundColor: 'rgba(0,128,0,0.4)',
                fill: true,
              },
              {
                label: 'Deletions',
                data: churnDelete,
                borderColor: 'red',
                backgroundColor: 'rgba(255,0,0,0.4)',
                fill: true,
              },
            ],
          }}
          options={{ responsive: true, scales: { x: { ticks: { maxRotation: 90, minRotation: 45 } } } }}
        />
      </section>
    </div>
  );
}
