import { BrowserRouter, Routes, Route } from "react-router-dom"
import MonthCalendar from "@/pages/MonthCalendar"
import WeekCalendar from "@/pages/WeekCalendar"
import TodoList from "./pages/TodoList"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/calendar/:year/:month" element={<MonthCalendar />} />
        <Route path="/calendar/:year/:month/:day" element={<WeekCalendar />} />
        <Route path="/todo" element={<TodoList />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
