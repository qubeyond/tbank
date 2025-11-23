import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'
import { apiCall } from '../api.js'

function Login() {
  const [eventCode, setEventCode] = useState('')
  const [notes, setNotes] = useState('')
  const [isDark, setIsDark] = useState(true)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [deviceFingerprint, setDeviceFingerprint] = useState('')
  const navigate = useNavigate()

  const generateDeviceFingerprint = async () => {
    try {
      const components = []
      components.push(navigator.userAgent)
      components.push(navigator.language)
      components.push(Intl.DateTimeFormat().resolvedOptions().timeZone)
      components.push(`${screen.width}x${screen.height}`)
      components.push(screen.colorDepth)
      components.push(navigator.hardwareConcurrency || 'unknown')
      components.push(navigator.platform)
      
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      ctx.textBaseline = 'top'
      ctx.font = '14px Arial'
      ctx.fillText('DeviceFingerprint', 2, 2)
      const canvasData = canvas.toDataURL()
      components.push(canvasData.substring(canvasData.length - 100))
      
      const fingerprintString = components.join('|')
      let hash = 0
      for (let i = 0; i < fingerprintString.length; i++) {
        const char = fingerprintString.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash
      }
      
      return `device_${Math.abs(hash).toString(36)}`
    } catch (err) {
      let storedFingerprint = localStorage.getItem('deviceFingerprint')
      if (!storedFingerprint) {
        storedFingerprint = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        localStorage.setItem('deviceFingerprint', storedFingerprint)
      }
      return storedFingerprint
    }
  }

  useEffect(() => {
    generateDeviceFingerprint().then(setDeviceFingerprint)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!deviceFingerprint) {
      setError('Инициализация устройства...')
      return
    }
    
    setError('')
    setIsLoading(true)

    try {
      const response = await apiCall('/ticket/', {
        method: 'POST',
        body: JSON.stringify({
          event_code: eventCode.trim(),
          session_id: deviceFingerprint,
          notes: notes.trim() || ''
        })
      })

      console.log('Full response:', response)

      let ticketId;

      // Если это новый талон
      if (response && response.id) {
        ticketId = response.id;
      }
      // Если талон уже существует
      else if (response && response.ticket && response.ticket.id) {
        ticketId = response.ticket.id;
      }
      // Если структура неожиданная
      else {
        console.error('Unexpected response structure:', response)
        throw new Error('Неожиданный ответ от сервера')
      }

      localStorage.setItem('currentTicketId', ticketId.toString())
      localStorage.setItem('sessionId', deviceFingerprint)
      localStorage.setItem('currentEventCode', eventCode.trim())
      
      // Немедленно переходим на страницу пользователя в любом случае
      navigate('/user')

    } catch (err) {
      console.error('Ticket creation error:', err)
      
      if (err.message.includes('404')) {
        setError(`Мероприятие с кодом "${eventCode}" не найдено`)
      } else if (err.message.includes('400')) {
        setError('Неверные данные для создания талона')
      } else if (err.message.includes('422')) {
        setError('Проверьте правильность введенных данных')
      } else if (err.message.includes('Неожиданный ответ')) {
        setError('Ошибка сервера. Попробуйте позже.')
      } else {
        setError('Ошибка при создании талона')
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
          d="M-100,250 C150,50 280,450 450,250 S600,50 1050,550 S1010,450 2400,650"
          fill="none" 
          strokeWidth="60" 
        />
      </svg>
      <svg className="background-line2" width="100%" height="100%">
        <path
          d="M-1800,650 C1950,850 200,250 2350,150"
          fill="none" 
          strokeWidth="90" 
        />
      </svg>
      
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? '☼' : '☾'}
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
              disabled={isLoading || !deviceFingerprint}
              title="Только буквы и цифры"
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
          
          <button 
            type="submit" 
            className="submit-btn"
            disabled={isLoading || !deviceFingerprint}
          >
            {!deviceFingerprint ? 'Инициализация...' : 
             isLoading ? 'Создание талона...' : 'Войти в очередь'}
          </button>
        </form>

        {error && (
          <div className="error-toast">
            <div className="error-toast-content">
              <span className="error-icon">⚠</span>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Login
