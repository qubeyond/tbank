const API_BASE = 'http://localhost:8000';

export async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`
    console.log('🔄 API Call:', url, options)
    
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
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
            // ФИКС: Правильно извлекаем сообщение об ошибке
            let errorMessage = 'Unknown error'
            
            if (data.detail && Array.isArray(data.detail)) {
                // Формат FastAPI: берем первое сообщение из массива detail
                errorMessage = data.detail[0]?.msg || JSON.stringify(data.detail)
            } else if (data.detail) {
                // Если detail не массив
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
