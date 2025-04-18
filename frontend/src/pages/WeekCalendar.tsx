import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

interface Schedule {
  id: number;
  summary: string;
  description: string;
  start_time: string;
  end_time: string;
  date: string;
  created_at: string;
  start_date: string;
  end_date: string;
  user_id: number;
  project_id: number;
  reminder_task_id: string;
  is_completed: boolean;
}

interface Day {
  date: string;
  schedules: Schedule[];
}

export default function WeekCalendar() {
  const { year, month, day } = useParams<{ year: string; month: string; day: string }>();
  const [weekData, setWeekData] = useState<Day[]>([]);
  const [weekFirst, setWeekFirst] = useState<string>('');
  const [weekLast, setWeekLast] = useState<string>('');

  useEffect(() => {
    const fetchWeekData = async () => {
      const res = await fetch(`http://localhost:8000/api/calendar/weekly/?year=${year}&month=${month}&day=${day}`);
      const data = await res.json();
      setWeekData(data.week);
      if (data.week.length > 0) {
        setWeekFirst(data.week[0].date);
        setWeekLast(data.week[data.week.length - 1].date);
      }
    };
    fetchWeekData();
  }, [year, month, day]);

  const getDayLabel = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ja-JP', { weekday: 'short' });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
  };

  const isToday = (dateStr: string) => {
    const today = new Date();
    const date = new Date(dateStr);
    return (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    );
  };

  const getPrevDate = (dateStr: string) => {
    const d = new Date(dateStr);
    d.setDate(d.getDate() - 7);
    return d;
  };

  const getNextDate = (dateStr: string) => {
    const d = new Date(dateStr);
    d.setDate(d.getDate() + 7);
    return d;
  };

  if (weekData.length === 0) return <div>Loading...</div>;

  const prev = getPrevDate(weekFirst);
  const next = getNextDate(weekFirst);

  return (
    <div className="p-4 max-w-6xl mx-auto">
      {/* ナビゲーション */}
      <div className="flex justify-between items-center mb-6">
        <Link to={`/calendar/${year}/${month}`} className="text-blue-600 hover:underline">
          ← 月表示に戻る
        </Link>
        <div className="text-lg font-semibold">
          <Link to={`/calendar/${prev.getFullYear()}/${prev.getMonth() + 1}/${prev.getDate()}`} className="mr-4 text-blue-600 hover:underline">
            ◀ 前週
          </Link>
          {formatDate(weekFirst)} ～ {formatDate(weekLast)}
          <Link to={`/calendar/${next.getFullYear()}/${next.getMonth() + 1}/${next.getDate()}`} className="ml-4 text-blue-600 hover:underline">
            次週 ▶
          </Link>
        </div>
      </div>

      {/* スケジュールカード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {weekData.map((day, i) => {
          const d = new Date(day.date);
          const isCurrent = isToday(day.date);
          return (
            <div
              key={i}
              className={`border rounded-xl p-4 shadow-sm transition ${
                isCurrent ? 'bg-green-50 border-green-400 shadow-md' : 'bg-white'
              }`}
            >
              <div className="mb-2 text-sm text-gray-500">{getDayLabel(day.date)}</div>
              <div className="mb-3 text-lg font-bold text-gray-800">
                <Link
                  to={`/calendar/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`}
                  className="hover:underline text-blue-700"
                >
                  {d.getMonth() + 1}/{d.getDate()}
                </Link>
              </div>
              {day.schedules.length > 0 ? (
                day.schedules.map((s, j) => (
                  <div key={j} className="mb-3 p-2 border-l-4 border-blue-400 bg-blue-50 rounded">
                    <div className="text-xs text-gray-600 mb-1">
                      {s.start_time} - {s.end_time}
                    </div>
                    <Link
                      to={`/calendar/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}/${s.id}`}
                      className="font-semibold text-blue-800 hover:underline"
                    >
                      {s.summary}
                    </Link>
                    {s.description && (
                      <div className="text-sm text-gray-700 mt-1 whitespace-pre-line">{s.description}</div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-gray-400">予定なし</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
