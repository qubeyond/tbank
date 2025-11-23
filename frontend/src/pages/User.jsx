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

  const createNewTicket = async () => {
    const sessionId = localStorage.getItem('sessionId')
    const eventCode = localStorage.getItem('currentEventCode')
    
    if (!sessionId || !eventCode) {
      throw new Error('Не найдены данные сессии или мероприятия')
    }

    const ticket = await apiCall('/ticket/', {
      method: 'POST',
      body: JSON.stringify({
        event_code: eventCode,
        session_id: sessionId,
        notes: ''
      })
    })

    localStorage.setItem('currentTicketId', ticket.id.toString())
    return ticket
  }

  const loadTicketData = async () => {
    try {
      setIsLoading(true)
      
      const sessionId = localStorage.getItem('sessionId')
      const eventCode = localStorage.getItem('currentEventCode')
      
      if (!sessionId || !eventCode) {
        throw new Error('Не найдены данные сессии или мероприятия')
      }

      let ticket
      const ticketId = localStorage.getItem('currentTicketId')

      if (ticketId && ticketId !== 'null' && ticketId !== 'undefined') {
        try {
          const numericTicketId = parseInt(ticketId)
          if (!isNaN(numericTicketId)) {
            ticket = await apiCall(`/ticket/${numericTicketId}`)
          }
        } catch (err) {
          console.log('Error loading ticket, creating new one')
        }
      }

      if (!ticket) {
        ticket = await createNewTicket()
      }

      const queue = await apiCall(`/queue/${ticket.queue_id}`)
      const event = await apiCall(`/event/${queue.event_id}`)
      const queueStatus = await apiCall(`/queue/${ticket.queue_id}/status`)

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
      setError('Ошибка загрузки данных: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const calculateTimeLeft = () => {
    if (!ticketData) return '--:--:--'
    
    const peopleBefore = ticketData.position - ticketData.current_position
    if (peopleBefore <= 0) return '00:00:00'
    
    const estimatedMinutes = peopleBefore * 5
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
      await apiCall(`/ticket/${ticketData.id}`, {
        method: 'PUT',
        headers: {
          'X-Session-ID': localStorage.getItem('sessionId') || ''
        },
        body: JSON.stringify({
          notes: supportMessage
        })
      })
      
      alert('Сообщение отправлено в техподдержку')
      setSupportMessage('')
      setShowSupportModal(false)
      loadTicketData()
    } catch (err) {
      alert('Ошибка отправки сообщения')
    }
  }

  const handleComplaintSubmit = async () => {
    try {
      const complaintNote = `ЖАЛОБА: ${complaintType}`
      
      await apiCall(`/ticket/${ticketData.id}`, {
        method: 'PUT',
        headers: {
          'X-Session-ID': localStorage.getItem('sessionId') || ''
        },
        body: JSON.stringify({
          notes: complaintNote
        })
      })
      
      alert('Жалоба отправлена')
      setComplaintType('')
      setShowComplaintModal(false)
      loadTicketData()
    } catch (err) {
      alert('Ошибка отправки жалобы')
    }
  }

  const handleCancelTicket = async () => {
    if (window.confirm('Вы уверены, что хотите отменить талон?')) {
      try {
        await apiCall(`/ticket/${ticketData.id}/cancel`, {
          method: 'POST',
          headers: {
            'X-Session-ID': localStorage.getItem('sessionId') || ''
          }
        })
        
        alert('Талон отменен')
        localStorage.removeItem('currentTicketId')
        navigate('/login')
      } catch (err) {
        alert('Ошибка отмены талона')
      }
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  const handleRefresh = () => {
    loadTicketData()
  }

  const handleLogout = () => {
    localStorage.removeItem('currentTicketId')
    localStorage.removeItem('sessionId')
    localStorage.removeItem('currentEventCode')
    navigate('/login')
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
        <div className="loading">
          <i className="fas fa-spinner fa-spin"></i> Загрузка данных талона...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`app ${isDark ? 'dark' : 'light'}`}>
        <div className="error-message">
          <i className="fas fa-exclamation-triangle"></i> {error}
          <div className="error-actions">
            <button onClick={loadTicketData} className="retry-btn">
              <i className="fas fa-redo"></i> Попробовать снова
            </button>
            // <button onClick={handleLogout} className="retry-btn logout-btn">
            //   <i className="fas fa-sign-out-alt"></i> Выйти
            // </button>
          </div>
        </div>
      </div>
    )
  }

  const peopleBefore = ticketData.position - ticketData.current_position

  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>
      <div className="header-controls">
        <button className="theme-toggle" onClick={toggleTheme}>

          {isDark ? ' ☼ ' : ' ☾ '}
         </button>
      </div>
      
      <svg className="background-line" width="100%" height="100%">
        <path
          d="M-100,250 C150,50 300,450 450,250 S600,50 850,350 S900,450 2400,650"
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
              <span>Ваш номер:</span>
              <span className="position-number">{ticketData?.position}</span>
            </div>
            <div className="info-row">
              <span>Перед вами:</span>
              <span>
                {ticketData?.current_position === 0 && ticketData?.position === 1 ? (
                  <span className="you-next">Вы следующие!</span>
                ) : ticketData?.current_position === 0 ? (
                  <span>{ticketData.position - 1} человек</span>
                ) : (
                  <span>{peopleBefore} человек</span>
                )}
              </span>
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
                <span className="notes-text">{ticketData.notes}</span>
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
          <button 
            className="action-btn cancel-btn"
            onClick={handleCancelTicket}
          >
            <i className="fas fa-times"></i> Отменить
          </button>
        </div>
      </div>

      {showSupportModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Техническая поддержка</h3>
            <textarea
              value={supportMessage}
              onChange={(e) => setSupportMessage(e.target.value)}
              placeholder="Опишите вашу проблему..."
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

      {showComplaintModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Отправка жалобы</h3>
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
                Отправить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default User
