import React, { useEffect, useState } from "react";

// Todoの型を定義
type Todo = {
  id: number;
  item_name: string;
  user_id: number;
  registration_date: string;
  expire_datetime: string | null;
  finished_date: string | null;
  description: string;
  is_deleted: boolean;
  create_date_time: string;
  update_date_time: string;
  reminder_task_id: string | null;
  is_completed: boolean;
};

export default function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    const response = await fetch(`http://localhost:8000/todo/api/todos/?search=${search}`);
    const data = await response.json();
    setTodos(data);
  };

  const handleComplete = async (id: number) => {
    await fetch(`http://localhost:8000/todo/api/todos/complete/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    fetchTodos();
  };

  const handleDelete = async (id: number) => {
    await fetch(`http://localhost:8000/todo/api/todos/delete/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    fetchTodos();
  };

  return (
    <div className="container">
      {/* 検索フォーム */}
      <form className="d-flex justify-content-end my-2" onSubmit={(e) => { e.preventDefault(); fetchTodos(); }}>
        <input
          className="form-control me-2"
          type="search"
          placeholder="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn btn-outline-dark" type="submit">
          検索
        </button>
      </form>

      {/* Todo一覧テーブル */}
      <table className="table table-striped table-hover table-sm my-2">
        <thead>
          <tr>
            <th>項目名</th>
            <th>担当者</th>
            <th>登録日時</th>
            <th>期限日時</th>
            <th>完了日時</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {todos
            .filter((todo) => !todo.is_deleted)
            .map((todo) => (
              <React.Fragment key={todo.id}>
                <tr
                  className={
                    todo.finished_date
                      ? "table-success"
                      : todo.expire_datetime
                      ? "table-warning"
                      : ""
                  }
                  data-bs-toggle="collapse"
                  data-bs-target={`#desc-${todo.id}`}
                  style={{ cursor: "pointer" }}
                >
                  <td className="align-middle">{todo.item_name}</td>
                  <td className="align-middle">{todo.user_id}</td>
                  <td className="align-middle">{formatDateTime(todo.registration_date)}</td>
                  <td className="align-middle">{formatDateTime(todo.expire_datetime)}</td>
                  <td className="align-middle">{formatDateTime(todo.finished_date)}</td>
                  <td className="align-middle">
                    <button
                      className="btn btn-primary btn-sm me-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleComplete(todo.id);
                      }}
                    >
                      完了
                    </button>
                    <button
                      className="btn btn-success btn-sm me-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.location.href = `/todo/edit/${todo.id}`;
                      }}
                    >
                      編集
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(todo.id);
                      }}
                    >
                      削除
                    </button>
                  </td>
                </tr>
                <tr>
                  <td colSpan={6} className="p-0">
                    <div className="collapse" id={`desc-${todo.id}`}>
                      <div className="card card-body m-2">
                        <p
                          className="mb-0"
                          dangerouslySetInnerHTML={{
                            __html: todo.description.replace(/\n/g, "<br>"),
                          }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              </React.Fragment>
            ))}
        </tbody>
      </table>

      {/* 戻るボタン */}
      {search && (
        <button
          className="btn btn-outline-primary"
          onClick={() => {
            setSearch("");
            fetchTodos();
          }}
        >
          戻る
        </button>
      )}

      {/* ⊕登録ボタン */}
      <a
        className="nav-link"
        href="/todo/new"
        style={{
          fontSize: "2.5rem",
          color: "#6c6c6c",
          textDecoration: "none",
          position: "fixed",
          bottom: "20px",
          right: "20px",
          zIndex: 1000,
        }}
        id="Registration-plus-btn"
      >
        ⊕
      </a>
    </div>
  );
}

// 日時フォーマット関数（例: 2024-04-21T14:00:00 → 2024/04/21 14:00）
function formatDateTime(datetime: string | null): string {
  if (!datetime) return "";
  const date = new Date(datetime);
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}
