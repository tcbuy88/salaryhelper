/*
  ApiClient - Real backend implementation
  Communicates with SalaryHelper FastAPI backend
  Provides functions:
    - sendSms(phone)
    - login(phone, code)
    - getCurrentUser()
    - logout()
    - listConversations(), createConversation(title), getConversation(id), sendMessage(convId, text)
    - uploadFile(file), listAttachments()
    - Health check and error handling
*/
(function(global){
  const API_BASE = 'http://localhost:8000/api/v1';
  
  // Helper functions
  function getAuthHeaders(){
    const token = localStorage.getItem('sh_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
  
  async function apiRequest(endpoint, options = {}){
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      return data;
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }
  
  const ApiClient = {
    // Auth methods
    async sendSms(phone){
      return await apiRequest('/auth/send-sms', {
        method: 'POST',
        body: JSON.stringify({ phone })
      });
    },
    
    async login(phone, code){
      const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ phone, code })
      });
      
      if (response.code === 0 && response.data.token) {
        localStorage.setItem('sh_token', response.data.token);
        localStorage.setItem('sh_current_user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    },
    
    async getCurrentUser(){
      try {
        const response = await apiRequest('/auth/me');
        if (response.code === 0) {
          localStorage.setItem('sh_current_user', JSON.stringify(response.data));
          return response.data;
        }
      } catch (error) {
        // Token might be invalid, clear it
        this.logout();
        throw error;
      }
    },
    
    logout(){
      localStorage.removeItem('sh_token');
      localStorage.removeItem('sh_current_user');
    },
    
    // Conversation methods
    async listConversations(){
      const response = await apiRequest('/conversations');
      return response.data || [];
    },
    
    async createConversation(title){
      const response = await apiRequest('/conversations', {
        method: 'POST',
        body: JSON.stringify({ title })
      });
      return response.data;
    },
    
    async getConversation(id){
      const response = await apiRequest(`/conversations/${id}`);
      return response.data;
    },
    
    async sendMessage(convId, text){
      const response = await apiRequest(`/conversations/${convId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ text })
      });
      return response.data;
    },
    
    // File methods
    async uploadFile(file){
      const formData = new FormData();
      formData.append('file', file);
      
      const url = `${API_BASE}/upload`;
      const response = await fetch(url, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Upload failed: ${response.statusText}`);
      }
      
      return data.data;
    },
    
    async listAttachments(){
      const response = await apiRequest('/attachments');
      return response.data || [];
    },
    
    // Health check
    async healthCheck(){
      return await apiRequest('/health');
    },
    
    // Utility method to check if user is logged in
    isLoggedIn(){
      return !!localStorage.getItem('sh_token');
    },
    
    // Get current user from localStorage (sync)
    getCurrentUserSync(){
      const userStr = localStorage.getItem('sh_current_user');
      return userStr ? JSON.parse(userStr) : null;
    }
  };
  
  global.ApiClient = ApiClient;
})(window);