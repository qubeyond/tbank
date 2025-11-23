// User.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './User.css'
import { apiCall } from '../api.js'

function User() {
  const [isDark, setIsDark] = useState(true)
  const [ticketData, setTicketData] = useState(null)
  const [timeLeft, setTimeLeft] = useState('--:--:--')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [showSupportModal, setShowSupportModal] = useState(false)
  const [showComplaintModal, setShowComplaintModal] = useState(false)
  const [supportMessage, setSupportMessage] = useState('')
  const [complaintType, setComplaintType] = useState('')
  
  const navigate = useNavigate()

  const complaintTypes = [
    'Долгое ожидание',
    'Некорректное поведение сотрудников', 
    'Технические проблемы',
    'Другое'
  ]

  useEffect(() => {
    loadTicketData()
    const timer = startTimer()
    return () => clearInterval(timer)
  }, [])

  const loadTicketData = async () => {
    try {
      setIsLoading(true)
      const ticketId = localStorage.getItem('currentTicketId')
      const sessionId = localStorage.getItem('sessionId')
      
      console.log('Loading ticket data for ID:', ticketId)

      if (!ticketId || !sessionId) {
        navigate('/login')
        return
      }

      // Получаем талон по ID
      const ticket = await apiCall(`/ticket/${ticketId}`)
      console.log('Ticket loaded:', ticket)

      // Получаем данные очереди
      const queue = await apiCall(`/queue/${ticket.queue_id}`)
      console.log('Queue loaded:', queue)

      // Получаем данные мероприятия
      const event = await apiCall(`/event/${queue.event_id}`)
      console.log('Event loaded:', event)

      // Получаем статус очереди для информации о текущей позиции
      const queueStatus = await apiCall(`/queue/${ticket.queue_id}/status`)
      console.log('Queue status:', queueStatus)

      setTicketData({
        ...ticket,
        event_name: event.name,
        queue_name: queue.name,
        current_position: queueStatus.current_position,
        waiting_count: queueStatus.waiting_count,
        processing_count: queueStatus.processing_count,
        completed_count: queueStatus.completed_count
      })

    } catch (err) {
      console.error('Error loading ticket data:', err)
      setError('Ошибка загрузки данных талона: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const calculateTimeLeft = () => {
    if (!ticketData) return '--:--:--'
    
    const positionDiff = ticketData.position - ticketData.current_position
    if (positionDiff <= 0) return '00:00:00'
    
    // Предполагаем среднее время обслуживания 5 минут на человека
    const estimatedMinutes = positionDiff * 5
    const hours = Math.floor(estimatedMinutes / 60)
    const minutes = estimatedMinutes % 60
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`
  }

  const startTimer = () => {
    return setInterval(() => {
      setTimeLeft(calculateTimeLeft())
    }, 1000)
  }

  const handleSupportSubmit = async () => {
    try {
      console.log('Sending support message:', supportMessage)
      // Здесь будет вызов API для отправки сообщения в техподдержку
      alert('Сообщение отправлено в техподдержку')
      setSupportMessage('')
      setShowSupportModal(false)
    } catch (err) {
      console.error('Error sending support message:', err)
      alert('Ошибка отправки сообщения')
    }
  }

  const handleComplaintSubmit = async () => {
    try {
      console.log('Sending complaint:', complaintType)
      // Здесь будет вызов API для отправки жалобы
      alert('Жалоба отправлена')
      setComplaintType('')
      setShowComplaintModal(false)
    } catch (err) {
      console.error('Error sending complaint:', err)
      alert('Ошибка отправки жалобы')
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  const handleRefresh = () => {
    loadTicketData()
  }

  const getStatusText = (status) => {
    const statusMap = {
      'waiting': 'Ожидание',
      'called': 'Вызван',
      'completed': 'Завершен',
      'cancelled': 'Отменен'
    }
    return statusMap[status] || status
  }

  const getStatusClass = (status) => {
    const statusClassMap = {
      'waiting': 'waiting',
      'called': 'active',
      'completed': 'completed',
      'cancelled': 'inactive'
    }
    return statusClassMap[status] || 'inactive'
  }

  if (isLoading) {
    return (
      <div className={`app ${isDark ? 'dark' : 'light'}`}>
        <div className="loading">Загрузка данных талона...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`app ${isDark ? 'dark' : 'light'}`}>
        <div className="error-message">
          {error}
          <button onClick={loadTicketData} className="retry-btn">
            Попробовать снова
          </button>
          <button onClick={() => navigate('/login')} className="retry-btn">
            Вернуться к входу
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? ' ☼ ' : ' ☾ '}
      </button>
      
      <svg className="background-line" width="100%" height="100%">
        <path
          d="M-100,250 C150,50 300,450 450,250 S600,50 850,350 S900,450 2300,650"
          fill="none" 
          strokeWidth="90" 
        />
      </svg>
      
      <div className="content">
        <div className="main-display-label">Примерное время ожидания</div>
        <div className="main-display">{timeLeft}</div>
        
        <div className="ticket-box">
          <div className="ticket-label">Ваш талон</div>
          <div className="ticket-number">
            {ticketData?.queue_name}-{ticketData?.position?.toString().padStart(3, '0')}
          </div>
          <div className="ticket-type">{ticketData?.event_name}</div>
          
          <div className="ticket-info">
            <div className="info-row">
              <span>Текущая позиция:</span>
              <span>{ticketData?.current_position}</span>
            </div>
            <div className="info-row">
              <span>Ваша позиция:</span>
              <span>{ticketData?.position}</span>
            </div>
            <div className="info-row">
              <span>Людей перед вами:</span>
              <span>{Math.max(0, (ticketData?.position || 0) - (ticketData?.current_position || 0))}</span>
            </div>
            <div className="info-row">
              <span>Статус:</span>
              <span className={`status ${getStatusClass(ticketData?.status)}`}>
                {getStatusText(ticketData?.status)}
              </span>
            </div>
            {ticketData?.notes && (
              <div className="info-row">
                <span>Примечания:</span>
                <span>{ticketData.notes}</span>
              </div>
            )}
          </div>
        </div>

        <div className="action-buttons">
          <button 
            className="action-btn support-btn"
            onClick={() => setShowSupportModal(true)}
          >
            <i className="fas fa-headset"></i> Тех. поддержка
          </button>
          <button 
            className="action-btn complaint-btn"
            onClick={() => setShowComplaintModal(true)}
          >
            <i className="fas fa-exclamation-triangle"></i> Пожаловаться
          </button>
          <button 
            className="action-btn refresh-btn"
            onClick={handleRefresh}
          >
            <i className="fas fa-sync-alt"></i> Обновить
          </button>
        </div>
      </div>

      {/* Модальное окно техподдержки */}
      {showSupportModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Техническая поддержка</h3>
            <p className="modal-description">
              Опишите вашу проблему, и мы постараемся помочь вам как можно скорее.
            </p>
            <textarea
              value={supportMessage}
              onChange={(e) => setSupportMessage(e.target.value)}
              placeholder="Опишите вашу проблему подробно..."
              rows={6}
              className="support-textarea"
            />
            <div className="modal-actions">
              <button 
                className="modal-btn cancel-btn"
                onClick={() => setShowSupportModal(false)}
              >
                Отмена
              </button>
              <button 
                className="modal-btn submit-btn"
                onClick={handleSupportSubmit}
                disabled={!supportMessage.trim()}
              >
                Отправить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно жалобы */}
      {showComplaintModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Отправка жалобы</h3>
            <p className="modal-description">
              Выберите тип жалобы. Мы рассмотрим её в кратчайшие сроки.
            </p>
            <div className="complaint-options">
              {complaintTypes.map(type => (
                <label key={type} className="complaint-option">
                  <input
                    type="radio"
                    name="complaintType"
                    value={type}
                    checked={complaintType === type}
                    onChange={(e) => setComplaintType(e.target.value)}
                  />
                  <span>{type}</span>
                </label>
              ))}
            </div>
            <div className="modal-actions">
              <button 
                className="modal-btn cancel-btn"
                onClick={() => setShowComplaintModal(false)}
              >
                Отмена
              </button>
              <button 
                className="modal-btn submit-btn"
                onClick={handleComplaintSubmit}
                disabled={!complaintType}
              >
                Отправить жалобу
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default User
