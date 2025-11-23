import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import User from './pages/User'
import AdmLogin from './pages/AdmLogin'
import Admin from './pages/Admin'
import AdminQueue from './pages/AdminQueue'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admlogin" element={<AdmLogin />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/queues/:eventId" element={<AdminQueue />} />
        <Route path="/user" element={<User />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Login />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
