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

  // Генерация фингерпринта устройства
  const generateDeviceFingerprint = async () => {
    try {
      // Пробуем получить более стабильный идентификатор
      const components = []
      
      // User agent
      components.push(navigator.userAgent)
      
      // Language
      components.push(navigator.language)
      
      // Timezone
      components.push(Intl.DateTimeFormat().resolvedOptions().timeZone)
      
      // Screen properties
      components.push(`${screen.width}x${screen.height}`)
      components.push(screen.colorDepth)
      
      // Hardware concurrency
      components.push(navigator.hardwareConcurrency || 'unknown')
      
      // Platform
      components.push(navigator.platform)
      
      // Canvas fingerprint (упрощенный)
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      ctx.textBaseline = 'top'
      ctx.font = '14px Arial'
      ctx.fillText('DeviceFingerprint', 2, 2)
      const canvasData = canvas.toDataURL()
      components.push(canvasData.substring(canvasData.length - 100)) // берем часть данных
      
      // Создаем хэш из всех компонентов
      const fingerprintString = components.join('|')
      let hash = 0
      for (let i = 0; i < fingerprintString.length; i++) {
        const char = fingerprintString.charCodeAt(i)
        hash = ((hash << 5) - hash) + char
        hash = hash & hash // Convert to 32bit integer
      }
      
      return `device_${Math.abs(hash).toString(36)}`
      
    } catch (err) {
      console.warn('Fingerprint generation failed, using fallback:', err)
      // Фолбэк на основе localStorage
      let storedFingerprint = localStorage.getItem('deviceFingerprint')
      if (!storedFingerprint) {
        storedFingerprint = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        localStorage.setItem('deviceFingerprint', storedFingerprint)
      }
      return storedFingerprint
    }
  }

  useEffect(() => {
    // Генерируем фингерпринт при загрузке компонента
    generateDeviceFingerprint().then(setDeviceFingerprint)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!deviceFingerprint) {
      setError('Инициализация устройства... Пожалуйста, подождите')
      return
    }
    
    setError('')
    setIsLoading(true)

    try {
      console.log('📤 Creating ticket with:', {
        event_code: eventCode.trim(),
        session_id: deviceFingerprint,
        notes: notes.trim() || ''
      })

      // Создаем талон
      const ticket = await apiCall('/ticket/', {
        method: 'POST',
        body: JSON.stringify({
          event_code: eventCode.trim(),
          session_id: deviceFingerprint,
          notes: notes.trim() || ''
        })
      })

      console.log('✅ Ticket created:', ticket)

      // Сохраняем данные и переходим
      localStorage.setItem('currentTicketId', ticket.id)
      localStorage.setItem('currentEventId', ticket.event_id)
      localStorage.setItem('currentQueueId', ticket.queue_id)
      localStorage.setItem('sessionId', deviceFingerprint)
      
      navigate('/user')

    } catch (err) {
      console.error('❌ Ticket creation error:', err)
      
      if (err.message.includes('400') && err.message.includes('У вас уже есть активный талон')) {
        // Если талон уже существует, просто переходим на страницу пользователя
        console.log('🎫 Ticket already exists, redirecting to user page...')
        
        // Пытаемся найти существующий талон
        try {
          const tickets = await apiCall(`/ticket/?session_id=${encodeURIComponent(deviceFingerprint)}&event_code=${encodeURIComponent(eventCode.trim())}`)
          
          if (tickets && tickets.length > 0) {
            const activeTicket = tickets.find(t => t.status === 'active') || tickets[0]
            
            console.log('✅ Found existing ticket:', activeTicket)

            // Сохраняем данные существующего талона
            localStorage.setItem('currentTicketId', activeTicket.id)
            localStorage.setItem('currentEventId', activeTicket.event_id)
            localStorage.setItem('currentQueueId', activeTicket.queue_id)
            localStorage.setItem('sessionId', deviceFingerprint)
            
            navigate('/user')
            return
          }
        } catch (searchError) {
          console.error('❌ Error searching for existing ticket:', searchError)
          // Если не нашли, показываем обычную ошибку
        }
        
        setError('У вас уже есть активный талон. Переход на страницу талона...')
        // Даже если не нашли через поиск, все равно переходим - возможно данные уже в localStorage
        setTimeout(() => navigate('/user'), 1000)
        
      } else if (err.message.includes('404') || err.message.includes('не найдено')) {
        setError('Мероприятие с таким кодом не найдено')
      } else if (err.message.includes('400')) {
        setError('Неверные данные для создания талона')
      } else if (err.message.includes('422')) {
        setError('Проверьте правильность введенных данных')
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
        {isDark ? ' ☼ ' : ' ☾ '}
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
              pattern="[A-Z0-9]{1,20}"
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

          {error && (
            <div className={`error-message ${error.includes('Переход') ? 'info-message' : ''}`}>
              {error}
            </div>
          )}
          
          <button 
            type="submit" 
            className="submit-btn"
            disabled={isLoading || !deviceFingerprint}
          >
            {!deviceFingerprint ? 'Инициализация...' : 
             isLoading ? 'Создание талона...' : 'Войти в очередь'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
