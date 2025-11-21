const API_BASE = 'http://localhost:8000';

// Utility functions
async function apiCall(endpoint, options = {}) {
    const resultDiv = document.getElementById('apiResult');
    resultDiv.innerHTML = 'Loading...';
    resultDiv.className = 'result loading';
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        // Проверяем, есть ли контент для парсинга
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else if (response.status === 204) {
            // No content (для DELETE запросов)
            data = { message: 'Success' };
        } else {
            // Для других типов контента
            data = { message: await response.text() };
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${JSON.stringify(data)}`);
        }
        
        resultDiv.textContent = JSON.stringify(data, null, 2);
        resultDiv.className = 'result success';
        return data;
    } catch (error) {
        console.error('API Call error:', error);
        resultDiv.textContent = error.message;
        resultDiv.className = 'result error';
        throw error;
    }
}

function formatJSON(data) {
    return JSON.stringify(data, null, 2);
}

// Health Check
document.getElementById('healthStatusBtn').addEventListener('click', async () => {
    await apiCall('/health/status');
});

document.getElementById('healthDbBtn').addEventListener('click', async () => {
    await apiCall('/health/db');
});

// Events
document.getElementById('createEventBtn').addEventListener('click', async () => {
    const name = document.getElementById('eventName').value;
    const qrCode = document.getElementById('eventQr').value;
    
    if (!name || !qrCode) {
        alert('Please fill event name and QR code');
        return;
    }
    
    const result = await apiCall('/event/', {
        method: 'POST',
        body: JSON.stringify({ name, qr_code: qrCode, is_active: true })
    });
    
    document.getElementById('eventsResult').textContent = formatJSON(result);
});

document.getElementById('getEventBtn').addEventListener('click', async () => {
    const eventId = document.getElementById('eventId').value;
    if (!eventId) {
        alert('Please enter event ID');
        return;
    }
    
    const result = await apiCall(`/event/${eventId}`);
    document.getElementById('eventsResult').textContent = formatJSON(result);
});

document.getElementById('getAllEventsBtn').addEventListener('click', async () => {
    const skip = document.getElementById('eventsSkip').value || 0;
    const limit = document.getElementById('eventsLimit').value || 100;
    
    const result = await apiCall(`/event/?skip=${skip}&limit=${limit}`);
    document.getElementById('eventsResult').textContent = formatJSON(result);
});

document.getElementById('updateEventBtn').addEventListener('click', async () => {
    const eventId = document.getElementById('eventId').value;
    const name = document.getElementById('eventName').value;
    const qrCode = document.getElementById('eventQr').value;
    
    if (!eventId) {
        alert('Please enter event ID');
        return;
    }
    
    const updateData = {};
    if (name) updateData.name = name;
    if (qrCode) updateData.qr_code = qrCode;
    
    const result = await apiCall(`/event/${eventId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
    });
    
    document.getElementById('eventsResult').textContent = formatJSON(result);
});

document.getElementById('deleteEventBtn').addEventListener('click', async () => {
    const eventId = document.getElementById('eventId').value;
    if (!eventId) {
        alert('Please enter event ID');
        return;
    }
    
    await apiCall(`/event/${eventId}`, { method: 'DELETE' });
    document.getElementById('eventsResult').textContent = 'Event deleted successfully';
});

// Queues
document.getElementById('createQueueBtn').addEventListener('click', async () => {
    const eventId = document.getElementById('queueEventId').value;
    const letter = document.getElementById('queueLetter').value;
    
    if (!eventId || !letter) {
        alert('Please fill event ID and queue letter');
        return;
    }
    
    const result = await apiCall('/queue/', {
        method: 'POST',
        body: JSON.stringify({ 
            event_id: parseInt(eventId), 
            letter: letter.toUpperCase(),
            is_active: true 
        })
    });
    
    document.getElementById('queuesResult').textContent = formatJSON(result);
});

document.getElementById('getEventQueuesBtn').addEventListener('click', async () => {
    const eventId = document.getElementById('eventIdForQueues').value;
    if (!eventId) {
        alert('Please enter event ID');
        return;
    }
    
    const result = await apiCall(`/queue/event/${eventId}`);
    document.getElementById('queuesResult').textContent = formatJSON(result);
});

document.getElementById('getQueueBtn').addEventListener('click', async () => {
    const queueId = document.getElementById('queueId').value;
    if (!queueId) {
        alert('Please enter queue ID');
        return;
    }
    
    const result = await apiCall(`/queue/${queueId}`);
    document.getElementById('queuesResult').textContent = formatJSON(result);
});

document.getElementById('getQueueStatusBtn').addEventListener('click', async () => {
    const queueId = document.getElementById('queueId').value;
    if (!queueId) {
        alert('Please enter queue ID');
        return;
    }
    
    const result = await apiCall(`/queue/${queueId}/status`);
    document.getElementById('queuesResult').textContent = formatJSON(result);
});

document.getElementById('callNextBtn').addEventListener('click', async () => {
    const queueId = document.getElementById('queueId').value;
    if (!queueId) {
        alert('Please enter queue ID');
        return;
    }
    
    const result = await apiCall(`/queue/${queueId}/next`, { method: 'POST' });
    document.getElementById('queuesResult').textContent = formatJSON(result);
});

// Tickets
document.getElementById('createTicketBtn').addEventListener('click', async () => {
    const queueId = document.getElementById('ticketQueueId').value;
    const clientIdentity = document.getElementById('clientIdentity').value;
    
    if (!queueId || !clientIdentity) {
        alert('Please fill queue ID and client identity');
        return;
    }
    
    const result = await apiCall('/ticket/', {
        method: 'POST',
        body: JSON.stringify({ 
            queue_id: parseInt(queueId), 
            client_identity: clientIdentity 
        })
    });
    
    document.getElementById('ticketsResult').textContent = formatJSON(result);
});

document.getElementById('getTicketBtn').addEventListener('click', async () => {
    const ticketId = document.getElementById('ticketId').value;
    if (!ticketId) {
        alert('Please enter ticket ID');
        return;
    }
    
    const result = await apiCall(`/ticket/${ticketId}`);
    document.getElementById('ticketsResult').textContent = formatJSON(result);
});

document.getElementById('updateTicketBtn').addEventListener('click', async () => {
    const ticketId = document.getElementById('ticketId').value;
    if (!ticketId) {
        alert('Please enter ticket ID');
        return;
    }
    
    const result = await apiCall(`/ticket/${ticketId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'processing' })
    });
    
    document.getElementById('ticketsResult').textContent = formatJSON(result);
});

document.getElementById('completeTicketBtn').addEventListener('click', async () => {
    const ticketId = document.getElementById('ticketId').value;
    if (!ticketId) {
        alert('Please enter ticket ID');
        return;
    }
    
    const result = await apiCall(`/ticket/${ticketId}/complete`, { method: 'POST' });
    document.getElementById('ticketsResult').textContent = formatJSON(result);
});

document.getElementById('getQueueTicketsBtn').addEventListener('click', async () => {
    const queueId = document.getElementById('queueIdForTickets').value;
    if (!queueId) {
        alert('Please enter queue ID');
        return;
    }
    
    const result = await apiCall(`/ticket/queue/${queueId}`);
    document.getElementById('ticketsResult').textContent = formatJSON(result);
});

// Raw API Tester
document.getElementById('apiTestBtn').addEventListener('click', async () => {
    const url = document.getElementById('apiUrl').value;
    const method = document.getElementById('apiMethod').value;
    const body = document.getElementById('apiBody').value;
    
    if (!url) {
        alert('Please enter API URL');
        return;
    }
    
    const options = { method };
    if (body && method !== 'GET') {
        try {
            options.body = JSON.stringify(JSON.parse(body));
        } catch (e) {
            alert('Invalid JSON body');
            return;
        }
    }
    
    await apiCall(url, options);
});

// Initialize - test connection on load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Frontend initialized');
});