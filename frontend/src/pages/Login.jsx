import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'
import { apiCall } from '../api'

function Login() {
  const [eventCode, setEventCode] = useState('')
  const [userIdentity, setUserIdentity] = useState('')
  const [notes, setNotes] = useState('')
  const [isDark, setIsDark] = useState(true)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      // Создаем талон напрямую по новому API
      const ticket = await apiCall('/ticket/', {
        method: 'POST',
        body: JSON.stringify({
          event_code: eventCode.trim(),       // ← изменилось на event_code
          user_identity: userIdentity || `user_${Date.now()}`, // ← изменилось на user_identity
          notes: notes || ''                  // ← новое поле
        })
      })

      // Сохраняем данные и переходим
      localStorage.setItem('currentTicketId', ticket.id)
      localStorage.setItem('currentEventId', ticket.event_id) // ← берем из ответа
      localStorage.setItem('currentQueueId', ticket.queue_id) // ← берем из ответа
      
      navigate('/user')

    } catch (err) {
      if (err.message.includes('404') || err.message.includes('не найдено')) {
        setError('Мероприятие с таким кодом не найдено')
      } else if (err.message.includes('400')) {
        setError('Неверные данные для создания талона')
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
            <label>Код мероприятия:</label>
            <input 
              type="text"
              value={eventCode}
              onChange={(e) => {
                setEventCode(e.target.value.toUpperCase())
                setError('')
              }}
              placeholder="Введите код мероприятия"
              required
              disabled={isLoading}
              pattern="[A-Z0-9]{1,20}"
              title="Только буквы и цифры"
            />
          </div>

          <div className="input-group">
            <label>Ваше имя (опционально):</label>
            <input 
              type="text"
              value={userIdentity}
              onChange={(e) => setUserIdentity(e.target.value)}
              placeholder="Введите ваше имя"
              disabled={isLoading}
            />
          </div>

          <div className="input-group">
            <label>Примечания (опционально):</label>
            <textarea 
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Дополнительная информация"
              disabled={isLoading}
              rows="3"
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
