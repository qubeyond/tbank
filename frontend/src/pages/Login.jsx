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
      // 1. Проверяем что введен числовой ID
      const eventIdNum = parseInt(eventId)
      if (isNaN(eventIdNum)) {
        setError('Код мероприятия должен быть числом')
        return
      }

      // 2. Пытаемся получить мероприятие по ID
      const event = await apiCall(`/event/${eventIdNum}`)
      
      // 3. Получаем очереди для этого мероприятия
      const queues = await apiCall(`/queue/event/${eventIdNum}`)
      
      if (!queues || queues.length === 0) {
        setError('Для этого мероприятия нет активных очередей')
        return
      }

      // 4. Берем первую доступную очередь
      const queue = queues[0]

      // 5. Создаем талон
      const ticket = await apiCall('/ticket/', {
        method: 'POST',
        body: JSON.stringify({
          queue_id: queue.id,
          client_identity: `user_${Date.now()}`
        })
      })

      // 6. Сохраняем данные и переходим
      localStorage.setItem('currentTicketId', ticket.id)
      localStorage.setItem('currentEventId', eventIdNum)
      navigate('/user')

    } catch (err) {
      if (err.message.includes('404')) {
        setError('Мероприятие с таким кодом не найдено')
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
