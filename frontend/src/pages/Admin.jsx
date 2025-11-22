import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Admin.css'
import { apiCall } from '../api.js'

function Admin() {
  const [events, setEvents] = useState([])
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [isDark, setIsDark] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState('')
  const [createForm, setCreateForm] = useState({
    name: '',
    is_active: true
  })
  const navigate = useNavigate()

  useEffect(() => {
    checkAuth()
    loadEvents()
  }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('adminToken')
    if (!token) {
      navigate('/admlogin')
    }
  }

  const loadEvents = async () => {
    try {
      setIsLoading(true)
      setError('')
      const eventsData = await apiCall('/event/?skip=0&limit=100&include_deleted=false')
      setEvents(eventsData)
    } catch (err) {
      setError('Ошибка загрузки мероприятий: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleEventClick = async (eventId) => {
    try {
      setIsLoading(true)
      setError('')
      const eventData = await apiCall(`/event/${eventId}`)
      setSelectedEvent(eventData)
    } catch (err) {
      setError('Ошибка загрузки мероприятия: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateEvent = async (e) => {
    e.preventDefault()
    try {
      setIsCreating(true)
      setError('')
      
      const newEvent = await apiCall('/event/', {
        method: 'POST',
        body: JSON.stringify(createForm)
      })
      
      // Обновляем список мероприятий
      await loadEvents()
      
      // Сбрасываем форму
      setCreateForm({
        name: '',
        is_active: true
      })
      
      // Показываем созданное мероприятие
      setSelectedEvent(newEvent)
      
    } catch (err) {
      setError('Ошибка создания мероприятия: ' + err.message)
    } finally {
      setIsCreating(false)
    }
  }

  const handleLogout = async () => {
    const token = localStorage.getItem('adminToken')
    
    try {
      if (token) {
        await apiCall('/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminData')
      navigate('/admlogin')
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU')
  }

  return (
    <div className={`admin-page ${isDark ? 'dark' : 'light'}`}>
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

      <div className="admin-container">
        <div className="admin-header">
          <h1>Панель управления мероприятиями</h1>
          <div className="header-actions">
            <button className="refresh-btn" onClick={loadEvents} disabled={isLoading}>
              🔄 Обновить
            </button>
            <button className="logout-btn" onClick={handleLogout}>
              Выйти
            </button>
          </div>
        </div>

        <div className="admin-content">
          <div className="events-section">
            <div className="section-header">
              <h2>Мероприятия</h2>
              <button 
                className="create-btn" 
                onClick={() => setIsCreating(!isCreating)}
                disabled={isLoading}
              >
                {isCreating ? '× Отмена' : '+ Создать мероприятие'}
              </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            {/* Форма создания мероприятия */}
            {isCreating && (
              <div className="create-form-container">
                <h3>Создать новое мероприятие</h3>
                <form onSubmit={handleCreateEvent} className="create-form">
                  <div className="form-group">
                    <label>Название мероприятия:</label>
                    <input
                      type="text"
                      value={createForm.name}
                      onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                      placeholder="Введите название мероприятия"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={createForm.is_active}
                        onChange={(e) => setCreateForm({...createForm, is_active: e.target.checked})}
                      />
                      Активное мероприятие
                    </label>
                  </div>
                  <div className="form-actions">
                    <button 
                      type="submit" 
                      className="submit-create-btn"
                      disabled={isLoading || !createForm.name.trim()}
                    >
                      {isLoading ? 'Создание...' : 'Создать'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {isLoading && !isCreating ? (
              <div className="loading">Загрузка мероприятий...</div>
            ) : events.length === 0 ? (
              <div className="no-events">
                <p>Мероприятий пока нет</p>
                <button 
                  className="create-btn" 
                  onClick={() => setIsCreating(true)}
                >
                  Создать первое мероприятие
                </button>
              </div>
            ) : (
              <div className="events-list">
                {events.map(event => (
                  <div 
                    key={event.id} 
                    className={`event-card ${selectedEvent?.id === event.id ? 'selected' : ''}`}
                    onClick={() => handleEventClick(event.id)}
                  >
                    <h3>{event.name}</h3>
                    <p><strong>Код:</strong> {event.code}</p>
                    <p><strong>Статус:</strong> 
                      <span className={`status ${event.is_active ? 'active' : 'inactive'}`}>
                        {event.is_active ? ' Активно' : ' Неактивно'}
                      </span>
                    </p>
                    <p><strong>ID:</strong> {event.id}</p>
                    <p><strong>Создано:</strong> {formatDate(event.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="details-section">
            {selectedEvent ? (
              <div className="event-details">
                <h2>Детали мероприятия</h2>
                <div className="event-info">
                  <div className="info-row">
                    <strong>ID:</strong> 
                    <span>{selectedEvent.id}</span>
                  </div>
                  <div className="info-row">
                    <strong>Название:</strong> 
                    <span>{selectedEvent.name}</span>
                  </div>
                  <div className="info-row">
                    <strong>Код:</strong> 
                    <span className="event-code">{selectedEvent.code}</span>
                  </div>
                  <div className="info-row">
                    <strong>Статус:</strong> 
                    <span className={`status ${selectedEvent.is_active ? 'active' : 'inactive'}`}>
                      {selectedEvent.is_active ? 'Активно' : 'Неактивно'}
                    </span>
                  </div>
                  <div className="info-row">
                    <strong>Удалено:</strong> 
                    <span className={`status ${selectedEvent.is_deleted ? 'inactive' : 'active'}`}>
                      {selectedEvent.is_deleted ? 'Да' : 'Нет'}
                    </span>
                  </div>
                  <div className="info-row">
                    <strong>Старый код:</strong> 
                    <span>{selectedEvent.is_old_code ? 'Да' : 'Нет'}</span>
                  </div>
                  <div className="info-row">
                    <strong>Создано:</strong> 
                    <span>{formatDate(selectedEvent.created_at)}</span>
                  </div>
                  {selectedEvent.updated_at && (
                    <div className="info-row">
                      <strong>Обновлено:</strong> 
                      <span>{formatDate(selectedEvent.updated_at)}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="no-selection">
                <h3>Выберите мероприятие</h3>
                <p>Нажмите на мероприятие в списке слева, чтобы увидеть его детали</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Admin
