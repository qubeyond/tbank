import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Admin.css'
import { apiCall } from '../api.js'

function Admin() {
  const [events, setEvents] = useState([])
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [isDark, setIsDark] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [showEventForm, setShowEventForm] = useState(false)
  const [showEditEventForm, setShowEditEventForm] = useState(false)
  const [isSubmittingEvent, setIsSubmittingEvent] = useState(false)
  const [error, setError] = useState('')
  const [createEventForm, setCreateEventForm] = useState({
    name: '',
    is_active: true
  })
  const [editEventForm, setEditEventForm] = useState({
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
      setEditEventForm({
        name: eventData.name,
        is_active: eventData.is_active
      })
    } catch (err) {
      setError('Ошибка загрузки мероприятия: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateEvent = async (e) => {
    e.preventDefault()
    try {
      setIsSubmittingEvent(true)
      setError('')
      
      const newEvent = await apiCall('/event/', {
        method: 'POST',
        body: JSON.stringify(createEventForm)
      })
      
      await loadEvents()
      setCreateEventForm({ name: '', is_active: true })
      setShowEventForm(false)
      setSelectedEvent(newEvent)
      
    } catch (err) {
      setError('Ошибка создания мероприятия: ' + err.message)
    } finally {
      setIsSubmittingEvent(false)
    }
  }

  const handleUpdateEvent = async (e) => {
    e.preventDefault()
    try {
      setIsSubmittingEvent(true)
      setError('')
      
      const updatedEvent = await apiCall(`/event/${selectedEvent.id}`, {
        method: 'PUT',
        body: JSON.stringify(editEventForm)
      })
      
      await loadEvents()
      setSelectedEvent(updatedEvent)
      setShowEditEventForm(false)
      
    } catch (err) {
      setError('Ошибка обновления мероприятия: ' + err.message)
    } finally {
      setIsSubmittingEvent(false)
    }
  }

  const handleDeleteEvent = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить это мероприятие?')) {
      return
    }
    
    try {
      setIsLoading(true)
      setError('')
      
      await apiCall(`/event/${selectedEvent.id}`, {
        method: 'DELETE',
        body: JSON.stringify({ hard_delete: false })
      })
      
      await loadEvents()
      setSelectedEvent(null)
      
    } catch (err) {
      setError('Ошибка удаления мероприятия: ' + err.message)
    } finally {
      setIsLoading(false)
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
               S1010,450 2300,650 `}
          fill="none" 
          strokeWidth="60" 
        />
      </svg>
      <svg className="background-line2" width="100%" height="100%">
        <path
          d={` M-1800,650 
               C1950,850 200,250 2350,150`}
          fill="none" 
          strokeWidth="90" 
        />
      </svg>
      
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? ' ☼ ' : ' ☾ '}
      </button>

      <div className="admin-container">
        <div className="admin-header">
          <h1>Панель администратора</h1>
          <div className="header-actions">
            <button className="refresh-btn" onClick={loadEvents} disabled={isLoading}>
               Обновить
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
                onClick={() => setShowEventForm(!showEventForm)}
                disabled={isLoading}
              >
                {showEventForm ? '× Отмена' : '+ Создать мероприятие'}
              </button>
            </div>

            {error && <div className="error-message">{error}</div>}

            {showEventForm && (
              <div className="create-form-container">
                <h3>Создать новое мероприятие</h3>
                <form onSubmit={handleCreateEvent} className="create-form">
                  <div className="form-group">
                    <label>Название мероприятия:</label>
                    <input
                      type="text"
                      value={createEventForm.name}
                      onChange={(e) => setCreateEventForm({...createEventForm, name: e.target.value})}
                      placeholder="Введите название мероприятия"
                      required
                      disabled={isSubmittingEvent}
                    />
                  </div>
                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={createEventForm.is_active}
                        onChange={(e) => setCreateEventForm({...createEventForm, is_active: e.target.checked})}
                        disabled={isSubmittingEvent}
                      />
                      Активное мероприятие
                    </label>
                  </div>
                  <div className="form-actions">
                    <button 
                      type="submit" 
                      className="submit-create-btn"
                      disabled={isSubmittingEvent || !createEventForm.name.trim()}
                    >
                      {isSubmittingEvent ? 'Создание...' : 'Создать'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {isLoading ? (
              <div className="loading">Загрузка мероприятий...</div>
            ) : events.length === 0 ? (
              <div className="no-events">
                <p>Мероприятий пока нет</p>
                <button 
                  className="create-btn" 
                  onClick={() => setShowEventForm(true)}
                >
                  Создать первое мероприятие
                </button>
              </div>
            ) : (
              <div className="events-list">
                {events.map(event => (
                  <div 
                    key={event.id} 
                    className={`event-card ${selectedEvent?.id === event.id ? 'selected' : ''} ${event.is_deleted ? 'deleted' : ''}`}
                    onClick={() => handleEventClick(event.id)}
                  >
                    <h3>{event.name}</h3>
                    <p><strong>Код:</strong> {event.code}</p>
                    <p><strong>Статус:</strong> 
                      <span className={`status ${event.is_active ? 'active' : 'inactive'}`}>
                        {event.is_active ? ' Активно' : ' Неактивно'}
                      </span>
                    </p>
                    <p><strong>Удалено:</strong> 
                      <span className={`status ${event.is_deleted ? 'inactive' : 'active'}`}>
                        {event.is_deleted ? ' Да' : ' Нет'}
                      </span>
                    </p>
                    <p><strong>ID:</strong> {event.id}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
<div className="details-section">
  {selectedEvent ? (
    <>
      <div className="event-details">
        <h2>Детали мероприятия</h2>
        
        <div className="event-actions">
          <button 
            className="edit-btn"
            onClick={() => setShowEditEventForm(!showEditEventForm)}
          >
             Редактировать
          </button>
          <button 
            className="delete-btn"
            onClick={handleDeleteEvent}
            disabled={isLoading}
          >
             Удалить
          </button>
        </div>

        {showEditEventForm ? (
          <form onSubmit={handleUpdateEvent} className="edit-form">
            <div className="form-group">
              <label>Название:</label>
              <input
                type="text"
                value={editEventForm.name}
                onChange={(e) => setEditEventForm({...editEventForm, name: e.target.value})}
                required
                disabled={isSubmittingEvent}
              />
            </div>
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={editEventForm.is_active}
                  onChange={(e) => setEditEventForm({...editEventForm, is_active: e.target.checked})}
                  disabled={isSubmittingEvent}
                />
                Активное мероприятие
              </label>
            </div>
            <div className="form-actions">
              <button 
                type="submit" 
                className="submit-create-btn"
                disabled={isSubmittingEvent}
              >
                {isSubmittingEvent ? 'Обновление...' : 'Обновить'}
              </button>
              <button 
                type="button"
                className="cancel-btn"
                onClick={() => setShowEditEventForm(false)}
              >
                Отмена
              </button>
            </div>
          </form>
        ) : (
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
              <strong>Создано:</strong> 
              <span>{formatDate(selectedEvent.created_at)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Отдельный бокс для управления очередями */}
      <div className="queues-box">
        <h3>Управление очередями</h3>
        <button 
          className="manage-queues-btn"
          onClick={() => navigate(`/admin/queues/${selectedEvent.id}`)}
        >
           Перейти к очередям
        </button>
        <p className="queues-description">
          Управление очередями, талонами и настройками для этого мероприятия
        </p>
      </div>
    </>
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
