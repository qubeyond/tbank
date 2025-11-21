const API_BASE = 'http://localhost:8000';

export async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`
    console.log('🔄 API Call:', url)
    
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
            // Пытаемся прочитать как JSON
            data = await response.json()
        } catch (jsonError) {
            // Если не JSON, читаем как текст
            const text = await response.text()
            data = { message: text, _raw: text }
        }
        
        console.log('📄 Response data:', data)
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${data.message || 'Not Found'}`)
        }
        
        return data
    } catch (error) {
        console.error('❌ API Call failed:', error.message)
        throw error
    }
}
