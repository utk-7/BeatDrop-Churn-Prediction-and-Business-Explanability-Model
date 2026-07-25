async function apiFetch(endpoint, options = {}) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT_MS);
    
    try {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        clearTimeout(id);
        
        if (!response.ok) {
            let errorMsg = `API Error: ${response.status} ${response.statusText}`;
            try {
                const errJson = await response.json();
                if (errJson.detail) errorMsg = errJson.detail;
                else if (typeof errJson === 'string') errorMsg = errJson;
            } catch(e) {}
            throw new Error(errorMsg);
        }
        
        return await response.json();
    } catch (error) {
        clearTimeout(id);
        if (error.name === 'AbortError') {
            throw new Error("Request timed out. The server took too long to respond.");
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error("Cannot connect to the backend — is it running?");
        }
        throw error;
    }
}
