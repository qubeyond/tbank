// api.js - ОБНОВЛЕННАЯ ВЕРСИЯ
const API_BASE = 'http://localhost:8000';

export async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`
    
    // Получаем токен из localStorage
    const token = localStorage.getItem('adminToken')
    
    // Создаем заголовки с учетом токена
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    }
    
    // Добавляем токен авторизации, если он есть
    if (token) {
        headers['Authorization'] = `Bearer ${token}`
    }
    
    console.log('🔄 API Call:', url, { ...options, headers })
    
    try {
        const response = await fetch(url, {
            headers,
            ...options
        })
        
        console.log('📡 Response status:', response.status)
        
        let data
        try {
            data = await response.json()
        } catch (jsonError) {
            const text = await response.text()
            data = { message: text, _raw: text }
        }
        
        console.log('📄 Response data:', data)
        
        if (!response.ok) {
            let errorMessage = 'Unknown error'
            
            if (data.detail && Array.isArray(data.detail)) {
                errorMessage = data.detail[0]?.msg || JSON.stringify(data.detail)
            } else if (data.detail) {
                errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
            } else if (data.message) {
                errorMessage = data.message
            } else if (typeof data === 'string') {
                errorMessage = data
            }
            
            throw new Error(`HTTP ${response.status}: ${errorMessage}`)
        }
        
        return data
    } catch (error) {
        console.error('❌ API Call failed:', error.message)
        throw error
    }
}
