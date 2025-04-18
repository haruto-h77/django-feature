import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';  // useParams を使うためにインポート

// スケジュールの型を定義
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

// 週の型を定義
interface Week {
  date: string;
  schedules: Schedule[];
}

// 月間カレンダーの型を定義
interface CalendarData {
  year: number;
  month: number;
  weeks: Week[][];
}

export default function MonthCalendar() {
  const { year, month } = useParams<{ year: string; month: string }>();  // URLパラメータを取得
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null);

  useEffect(() => {
    // 月間カレンダーAPIからデータを取得
    const fetchData = async () => {
      const response = await fetch(`http://localhost:8000/api/calendar/monthly/?year=${year}&month=${month}`);
      const data = await response.json();
      setCalendarData(data);
    };
    fetchData();
  }, [year, month]);

  // データがロードされるまでロード中を表示
  if (!calendarData) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <style>
        {`
          table {
            table-layout: fixed;
            width: 100%;
            border-collapse: collapse;
          }

          th, td {
            border: 1px solid #ccc;
            text-align: left;
            vertical-align: top;
          }

          td > a > div {
            height: 100px;
            overflow: hidden;
            white-space: nowrap;
            padding: 4px;
          }

          .month_link {
            float: right;
          }

          th:first-child, td:first-child {
            color: red;
          }

          th:last-child, td:last-child {
            color: blue;
          }

          #Registration-plus-btn {
            font-size: 2.5rem;
            color: #6c6c6c;
            text-decoration: none;
            display: inline-block;
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
          }
          #Registration-plus-btn:hover {
            color: #242424;
          }
        `}
      </style>
  
      <a href={`/calendar/${year}/${month}/1`}>週表示に切り替え</a>
  
      <div>
        <span>
          <a href={`/calendar/${Number(year) - 1}/${month}`}>前年</a>
          {`${year}年${month}月`}
          <a href={`/calendar/${Number(year) + 1}/${month}`}>来年</a>
        </span>
  
        <span className="month_link">
          {[...Array(12)].map((_, i) => {
            const monthNum = i + 1;
            return (
              <span key={monthNum}>
                <a
                  href={`/calendar/${year}/${monthNum}`}
                  style={{ fontWeight: Number(month) === monthNum ? 'bold' : 'normal' }}
                >
                  {monthNum}月
                </a>
                {monthNum !== 12 && ' | '}
              </span>
            );
          })}
        </span>
      </div>
  
      <table className="table">
        <thead>
          <tr>
            {['日', '月', '火', '水', '木', '金', '土'].map((w, i) => (
              <th key={i}>{w}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {calendarData.weeks.map((week, weekIndex) => (
            <tr key={weekIndex}>
              {week.map((day, dayIndex) => (
                <td key={dayIndex}>
                  <a
                    href={`/calendar/${new Date(day.date).getFullYear()}/${new Date(day.date).getMonth() + 1}/${new Date(day.date).getDate()}`}
                    style={{
                      textDecoration: 'none',
                      color: 'inherit',
                      display: 'block',
                      height: '100%',
                    }}
                  >
                    <div>
                      {new Date(day.date).getMonth() + 1 !== Number(month)
                        ? new Date(day.date).toLocaleDateString('ja-JP', { month: '2-digit', day: '2-digit' })
                        : new Date(day.date).getDate()}
                      {day.schedules.map((schedule, i) => (
                        <p key={i}>
                          <a
                            href={`/calendar/${new Date(schedule.date).getFullYear()}/${new Date(schedule.date).getMonth() + 1}/${new Date(schedule.date).getDate()}/${schedule.id}`}
                          >
                            {schedule.summary}
                          </a>
                        </p>
                      ))}
                    </div>
                  </a>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
  
      <a
        href={`/calendar/${year}/${month}/1`}
        className="fab"
        id="Registration-plus-btn"
      >
        ⊕
      </a>
    </>
  );
}
