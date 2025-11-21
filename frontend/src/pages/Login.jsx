import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'
import { apiCall } from '../api.js' 

function Login() {
  const [eventId, setEventId] = useState('')
  const [isDark, setIsDark] = useState(true)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const eventIdNum = parseInt(eventId)
      if (isNaN(eventIdNum)) {
        setError('Код мероприятия должен быть числом')
        return
      }

      // Проверяем существование мероприятия
      const event = await apiCall(`/event/${eventIdNum}`)
      
      // Создаем талон с правильными параметрами
      const ticketData = {
        event_id: eventIdNum,
        user_identity: `user_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        notes: "Создан через веб-интерфейс"
      }

      console.log('Creating ticket with:', ticketData)
      
      const ticket = await apiCall('/ticket/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ticketData)
      })

      localStorage.setItem('currentTicketId', ticket.id)
      localStorage.setItem('currentEventId', eventIdNum)
      navigate('/user')

    } catch (err) {
      console.error('❌ Full error:', err)
      
      if (err.message.includes('404')) {
        setError('Мероприятие с таким кодом не найдено')
      } else if (err.message.includes('422')) {
        const errorMsg = err.message.replace('HTTP 422: ', '')
        setError(`Ошибка данных: ${errorMsg}`)
      } else {
        setError('Ошибка при создании талона: ' + err.message)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  return (
    <div className={`login-page ${isDark ? 'dark' : 'light'}`}>
      <svg className="background-line1" width="100%" height="100%">
        <path
          d={` M-100,250 
               C150,50 280,450 450,250 
               S600,50 1050,550 
               S1010,450 1800,650 `}
          fill="none" 
          strokeWidth="60" 
        />
      </svg>
      <svg className="background-line2" width="100%" height="100%">
        <path
          d={` M-1800,650 
               C1950,850 200,250 1950,150`}
          fill="none" 
          strokeWidth="90" 
        />
      </svg>
      
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? 'Светлая тема' : 'Тёмная тема'}
      </button>
      
      <div className="login-container">
        <h1>Вход в очередь</h1>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>Код мероприятия (ID):</label>
            <input 
              type="number" 
              value={eventId}
              onChange={(e) => {
                setEventId(e.target.value)
                setError('')
              }}
              placeholder="Введите код мероприятия"
              required
              disabled={isLoading}
              min="1"
            />
          </div>

          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="submit" 
            className="submit-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Создание талона...' : 'Войти в очередь'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
