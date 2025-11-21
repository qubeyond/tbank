import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

function Login() {
  const [eventCode, setEventCode] = useState('')
  const [isDark, setIsDark] = useState(true)
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Код мероприятия:', eventCode)
    navigate('/user')
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  return (
    <div className={`login-page ${isDark ? 'dark' : 'light'}`}>

        <svg className="background-line2" width="100%" height="100%">
        <path
          d={` M-1800,650 
               C1950,850 200,250 1950,150`}
          fill="none" 
          strokeWidth="90" 
        />
      </svg>
      <svg className="background-line1" width="100%" height="100%">
        <path
          d={` M-100,250 
               C150,50 280,450 450,250 
               S600,80 950,550 
               S1010,450 1800,650 `}
          fill="none" 
          strokeWidth="60" 
        />
      </svg>
        
      
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? 'Светлая тема' : 'Тёмная тема'}
      </button>
      
      <div className="login-container">
        <h1>Вход в очередь</h1>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>Код мероприятия:</label>
            <input 
              type="text" 
              value={eventCode}
              onChange={(e) => setEventCode(e.target.value)}
              placeholder="Введите код"
              required
            />
          </div>
          
          <button type="submit" className="submit-btn">
            Войти в очередь
          </button>
        </form>

        <div className="qr-placeholder">
          <div className="qr-code">
            <span>QR Code Placeholder</span>
          </div>
          <p>Или отсканируйте QR-код</p>
        </div>
      </div>
    </div>
  )
}

export default Login
