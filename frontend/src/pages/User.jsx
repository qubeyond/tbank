import { useState, useEffect } from 'react'
import './User.css'

function User() {
  const [isDark, setIsDark] = useState(true)
  const [mainDataTime, setMainDataTime] = useState('12:45:23')
  const [mainDataType, setMainDataType] = useState('Type Of Meropriyatiye')
  const [ticketNumber, setTicketNumber] = useState('А-55') // Будет из API

  const toggleTheme = () => {
    setIsDark(!isDark)
  }

  // Заглушка для API - потом заменишь на реальный запрос
  useEffect(() => {
    // Здесь будет fetch к твоему FastAPI
    // const fetchTicketData = async () => {
    //   const response = await fetch('/api/ticket')
    //   const data = await response.json()
    //   setTicketNumber(data.ticket_number)
    //   setMainDataType(data.event_type)
    // }
    // fetchTicketData()
  }, [])

  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>
      <button className="theme-toggle" onClick={toggleTheme}>
        {isDark ? ' ☼ ' : ' ☾ '}
      </button>
      
      <svg className="background-line" width="100%" height="100%">
        <path
          d={` M-100,250 
               C150,50 300,450 450,250 
               S600,50 850,350 
               S900,450 1800,650 `}
          fill="none" strokeWidth="90" />
      </svg>
      
      <div className="content">
        {/* Убрал лого */}
        <div className="main-display-label">Время до вашей очереди</div>
        <div className="main-display">{mainDataTime}</div>
        
        <div className="ticket-box">
          <div className="ticket-label">Талон</div>
          <div className="ticket-number">{ticketNumber}</div>
          <div className="ticket-type">{mainDataType}</div>
        </div>
      </div>
    </div>
  )
}

export default User
