import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './AdmLogin.css'
import { apiCall } from '../api.js'

function AdmLogin() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isDark, setIsDark] = useState(true)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  // Проверяем, авторизован ли пользователь при загрузке
  const isLoggedIn = localStorage.getItem('adminToken')

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await apiCall('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          password: password
        })
      })

      // Сохраняем токен и данные админа
      localStorage.setItem('adminToken', response.access_token)
      localStorage.setItem('adminData', JSON.stringify(response.admin))
      
      console.log(' Admin login successful:', response)
      // navigate('/user')

    } catch (err) {
      if (err.message.includes('401') || err.message.includes('неверные')) {
        setError('Неверное имя пользователя или пароль')
      } else if (err.message.includes('404')) {
        setError('Пользователь не найден')
      } else {
        setError('Ошибка при входе: ' + err.message)
      }
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
      console.error(' Logout API call failed:', err)
    } finally {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminData')
      console.log(' Logout successful')
      window.location.reload()
    }
  }

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  // Если пользователь уже авторизован, показываем панель администратора
  if (isLoggedIn) {
    const adminData = JSON.parse(localStorage.getItem('adminData') || '{}')
    
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
          <h2>Панель администратора</h2>
          
          <div className="admin-info">
            <div className="info-item">
              <strong>Имя пользователя:</strong> {adminData.username}
            </div>
            <div className="info-item">
              <strong>Email:</strong> {adminData.email}
            </div>
            <div className="info-item">
              <strong>ID:</strong> {adminData.id}
            </div>
            <div className="info-item">
              <strong>Статус:</strong> 
              <span className={`status ${adminData.is_active ? 'active' : 'inactive'}`}>
                {adminData.is_active ? ' Активен' : ' Неактивен'}
              </span>
            </div>
            <div className="info-item">
              <strong>Дата регистрации:</strong> {new Date(adminData.created_at).toLocaleDateString('ru-RU')}
            </div>
          </div>

          <div className="admin-actions">
            <button 
              onClick={() => navigate('/admin')}
              className="action-btn primary"
            >
              Перейти к управлению
            </button>
            
            <button 
              onClick={handleLogout}
              className="action-btn logout-btn"
            >
              Выйти из системы
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Форма логина для администратора
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
        <h1>Вход для администратора</h1>
        
        <form onSubmit={handleLogin} className="login-form">
          <div className="input-group">
            <label>Имя пользователя:</label>
            <input 
              type="text"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value)
                setError('')
              }}
              placeholder="Введите имя пользователя"
              required
              disabled={isLoading}
            />
          </div>

          <div className="input-group">
            <label>Пароль:</label>
            <input 
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setError('')
              }}
              placeholder="Введите пароль"
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
            {isLoading ? 'Вход...' : 'Войти как администратор'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AdmLogin
