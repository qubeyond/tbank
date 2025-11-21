import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import User from './pages/User'
// import Admin from './pages/Admin'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {<Route path="/login" element={<Login />} />}
        <Route path="/user" element={<User />} />
        {/* <Route path="/admin" element={<Admin />} /> */}
        {/* <Route path="/" element={<Login />} /> */}
        <Route path="/" element={<Login />} />  {/* Временно на юзера */}
      </Routes>
    </BrowserRouter>
  )
}

export default App
