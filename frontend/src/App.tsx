import { BrowserRouter, Routes, Route } from "react-router-dom"
import MonthCalendar from "@/pages/MonthCalendar"
import WeekCalendar from "@/pages/WeekCalendar"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/calendar/:year/:month" element={<MonthCalendar />} />
        <Route path="/calendar/:year/:month/:day" element={<WeekCalendar />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
