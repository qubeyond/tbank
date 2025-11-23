// pages/AdminQueue.jsx
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import './AdminQueue.css'
import { apiCall } from '../api.js'

function AdminQueue() {
  const { eventId } = useParams()
  const [event, setEvent] = useState(null)
  const [queues, setQueues] = useState([])
  const [isDark, setIsDark] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [showQueueForm, setShowQueueForm] = useState(false)
  const [showEditQueueForm, setShowEditQueueForm] = useState(null)
  const [isSubmittingQueue, setIsSubmittingQueue] = useState(false)
  const [error, setError] = useState('')
  const [createQueueForm, setCreateQueueForm] = useState({
    is_active: true,
    event_id: parseInt(eventId)
  })
  const [editQueueForm, setEditQueueForm] = useState({
    name: '',
    is_active: true,
    current_position: 0
  })
  const navigate = useNavigate()

  useEffect(() => {
    checkAuth()
    loadEventData()
    loadQueues()
  }, [eventId])

  const checkAuth = () => {
    const token = localStorage.getItem('adminToken')
    if (!token) {
      navigate('/admlogin')
    }
  }

  const loadEventData = async () => {
    try {
      const eventData = await apiCall(`/event/${eventId}`)
      setEvent(eventData)
    } catch (err) {
      setError('Ошибка загрузки мероприятия: ' + err.message)
    }
  }

  const loadQueues = async () => {
    try {
      setIsLoading(true)
      setError('')
      
      // Реальный API запрос с параметром event_id
      const queuesData = await apiCall(`/queue/?event_id=${eventId}&include_deleted=false`)
      setQueues(queuesData)
      
    } catch (err) {
      console.error('Error loading queues:', err)
      
      // Временная заглушка - тестовые данные только при ошибке
      if (err.message.includes('404') || err.message.includes('500')) {
        const testQueues = [
          {
            id: 1,
            name: 'A',
            is_active: true,
            current_position: 5,
            created_at: new Date().toISOString(),
            event_id: parseInt(eventId)
          },
          {
            id: 2,
            name: 'B', 
            is_active: false,
            current_position: 0,
            created_at: new Date().toISOString(),
            event_id: parseInt(eventId)
          }
        ]
        setQueues(testQueues)
      } else {
        setError('Ошибка загрузки очередей: ' + err.message)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateQueue = async (e) => {
    e.preventDefault()
    try {
      setIsSubmittingQueue(true)
      setError('')
      
      console.log(' Creating queue with data:', createQueueForm)
      
      // Создаем очередь согласно API документации
      const newQueue = await apiCall('/queue/', {
        method: 'POST',
        body: JSON.stringify({
          is_active: createQueueForm.is_active,
          event_id: parseInt(eventId)
        })
      })
      
      console.log(' Queue created successfully:', newQueue)
      
      // Обновляем список очередей
      await loadQueues()
      setCreateQueueForm({ is_active: true, event_id: parseInt(eventId) })
      setShowQueueForm(false)
      setError('')
      
    } catch (err) {
      console.error(' Queue creation error:', err)
      const errorMessage = err.message.includes('422') ? 'Неверные данные для создания очереди' : 
                          err.message.includes('400') ? 'Ошибка в запросе' : 
                          err.message.includes('409') ? 'Очередь с таким именем уже существует' :
                          err.message
      setError('Ошибка создания очереди: ' + errorMessage)
    } finally {
      setIsSubmittingQueue(false)
    }
  }

  const handleUpdateQueue = async (queueId) => {
    try {
      setError('')
      
      console.log('📤 Updating queue with data:', editQueueForm)
      
      const updatedQueue = await apiCall(`/queue/${queueId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: editQueueForm.name,
          is_active: editQueueForm.is_active,
          current_position: parseInt(editQueueForm.current_position)
        })
      })
      
      console.log(' Queue updated:', updatedQueue)
      
      await loadQueues()
      setShowEditQueueForm(null)
      
    } catch (err) {
      console.error(' Queue update error:', err)
      setError('Ошибка обновления очереди: ' + err.message)
    }
  }

  const handleDeleteQueue = async (queueId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту очередь?')) {
      return
    }
    
    try {
      setError('')
      
      await apiCall(`/queue/${queueId}`, {
        method: 'DELETE',
        body: JSON.stringify({
          hard_delete: false,
          move_tickets_to: 0  // 0 означает не перемещать талоны
        })
      })
      
      console.log(' Queue deleted')
      
      await loadQueues()
      
    } catch (err) {
      console.error(' Queue deletion error:', err)
      setError('Ошибка удаления очереди: ' + err.message)
    }
  }

  const handleEditQueueClick = (queue) => {
    setShowEditQueueForm(queue.id)
    setEditQueueForm({
      name: queue.name,
      is_active: queue.is_active,
      current_position: queue.current_position
    })
  }

  const handleBackToEvents = () => {
    navigate('/admin')
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU')
  }

  if (!event) {
    return (
      <div className={`admin-queue-page ${isDark ? 'dark' : 'light'}`}>
        <div className="loading">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className={`admin-queue-page ${isDark ? 'dark' : 'light'}`}>
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

      <div className="admin-queue-container">
        <div className="admin-queue-header">
          <div className="header-main">
            <button className="back-btn" onClick={handleBackToEvents}>
              ← Назад к мероприятиям
            </button>
            <h1>Управление очередями</h1>
          </div>
          <div className="header-actions">
            <button className="refresh-btn" onClick={loadQueues} disabled={isLoading}>
              🔄 Обновить
            </button>
          </div>
        </div>

        {/* Информация о мероприятии */}
        <div className="event-info-card">
          <h2>{event.name}</h2>
          <div className="event-details">
            <p><strong>Код:</strong> {event.code}</p>
            <p><strong>ID:</strong> {event.id}</p>
            <p><strong>Статус:</strong> 
              <span className={`status ${event.is_active ? 'active' : 'inactive'}`}>
                {event.is_active ? ' Активно' : ' Неактивно'}
              </span>
            </p>
          </div>
        </div>

        <div className="queues-content">
          <div className="section-header">
            <h2>Очереди мероприятия</h2>
            <button 
              className="create-btn" 
              onClick={() => setShowQueueForm(!showQueueForm)}
              disabled={isLoading}
            >
              {showQueueForm ? '× Отмена' : '+ Создать очередь'}
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {/* Форма создания очереди */}
          {showQueueForm && (
            <div className="create-form-container">
              <h3>Создать новую очередь</h3>
              <form onSubmit={handleCreateQueue} className="create-form">
                <div className="form-group checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={createQueueForm.is_active}
                      onChange={(e) => setCreateQueueForm({...createQueueForm, is_active: e.target.checked})}
                      disabled={isSubmittingQueue}
                    />
                    Активная очередь
                  </label>
                </div>
                <div className="form-actions">
                  <button 
                    type="submit" 
                    className="submit-create-btn"
                    disabled={isSubmittingQueue}
                  >
                    {isSubmittingQueue ? 'Создание...' : 'Создать очередь'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Список очередей */}
          {isLoading ? (
            <div className="loading">Загрузка очередей...</div>
          ) : queues.length === 0 ? (
            <div className="no-queues">
              <p>Очередей пока нет</p>
              <p>Создайте первую очередь для этого мероприятия</p>
            </div>
          ) : (
            <div className="queues-grid">
              {queues.map(queue => (
                <div key={queue.id} className="queue-card">
                  {showEditQueueForm === queue.id ? (
                    <div className="queue-edit-form">
                      <h4>Редактирование очереди</h4>
                      <div className="form-group">
                        <label>Название:</label>
                        <input
                          type="text"
                          value={editQueueForm.name}
                          onChange={(e) => setEditQueueForm({...editQueueForm, name: e.target.value})}
                          placeholder="Введите название очереди"
                        />
                      </div>
                      <div className="form-group">
                        <label>Текущая позиция:</label>
                        <input
                          type="number"
                          value={editQueueForm.current_position}
                          onChange={(e) => setEditQueueForm({...editQueueForm, current_position: parseInt(e.target.value) || 0})}
                          min="0"
                        />
                      </div>
                      <div className="form-group checkbox-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={editQueueForm.is_active}
                            onChange={(e) => setEditQueueForm({...editQueueForm, is_active: e.target.checked})}
                          />
                          Активная очередь
                        </label>
                      </div>
                      <div className="form-actions">
                        <button 
                          className="submit-create-btn"
                          onClick={() => handleUpdateQueue(queue.id)}
                        >
                          Сохранить
                        </button>
                        <button 
                          className="cancel-btn"
                          onClick={() => setShowEditQueueForm(null)}
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="queue-header">
                        <h3>Очередь {queue.name}</h3>
                        <div className="queue-actions">
                          <button 
                            className="edit-btn"
                            onClick={() => handleEditQueueClick(queue)}
                          >
                            edit
                          </button>
                          <button 
                            className="delete-btn"
                            onClick={() => handleDeleteQueue(queue.id)}
                          >
                            delete
                          </button>
                        </div>
                      </div>
                      <div className="queue-info">
                        <p><strong>Текущая позиция:</strong> {queue.current_position}</p>
                        <p><strong>Статус:</strong> 
                          <span className={`status ${queue.is_active ? 'active' : 'inactive'}`}>
                            {queue.is_active ? ' Активна' : ' Неактивна'}
                          </span>
                        </p>
                        <p><strong>Создана:</strong> {formatDate(queue.created_at)}</p>
                        <p><strong>ID очереди:</strong> {queue.id}</p>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminQueue
