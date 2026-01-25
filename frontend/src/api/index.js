import request from '@/utils/request'

export const authAPI = {
  login(data) {
    return request({
      url: '/auth/login',
      method: 'post',
      data
    })
  },
  
  register(data) {
    return request({
      url: '/auth/register',
      method: 'post',
      data
    })
  },
  
  getCurrentUser() {
    return request({
      url: '/auth/me',
      method: 'get'
    })
  },
  
  getUsers(params) {
    return request({
      url: '/auth/users',
      method: 'get',
      params
    })
  },
  
  createUser(data) {
    return request({
      url: '/auth/users',
      method: 'post',
      data
    })
  },
  
  updateUser(id, data) {
    return request({
      url: `/auth/users/${id}`,
      method: 'put',
      data
    })
  },
  
  deleteUser(id) {
    return request({
      url: `/auth/users/${id}`,
      method: 'delete'
    })
  },
  
  getRoles() {
    return request({
      url: '/auth/roles',
      method: 'get'
    })
  },
  
  createRole(data) {
    return request({
      url: '/auth/roles',
      method: 'post',
      data
    })
  },
  
  assignRoleToUser(userId, roleId) {
    return request({
      url: `/auth/users/${userId}/roles/${roleId}`,
      method: 'post'
    })
  },
  
  removeRoleFromUser(userId, roleId) {
    return request({
      url: `/auth/users/${userId}/roles/${roleId}`,
      method: 'delete'
    })
  },
  
  getPermissions() {
    return request({
      url: '/auth/permissions',
      method: 'get'
    })
  },
  
  createPermission(data) {
    return request({
      url: '/auth/permissions',
      method: 'post',
      data
    })
  },
  
  assignPermissionToRole(roleId, permissionId) {
    return request({
      url: `/auth/roles/${roleId}/permissions/${permissionId}`,
      method: 'post'
    })
  }
}

export const kbAPI = {
  getKnowledgeBases(params) {
    return request({
      url: '/knowledge-bases',
      method: 'get',
      params
    })
  },
  
  createKnowledgeBase(data) {
    return request({
      url: '/knowledge-bases',
      method: 'post',
      data
    })
  },
  
  getKnowledgeBase(id) {
    return request({
      url: `/knowledge-bases/${id}`,
      method: 'get'
    })
  },
  
  updateKnowledgeBase(id, data) {
    return request({
      url: `/knowledge-bases/${id}`,
      method: 'put',
      data
    })
  },
  
  deleteKnowledgeBase(id) {
    return request({
      url: `/knowledge-bases/${id}`,
      method: 'delete'
    })
  },
  
  uploadDocument(kbId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: `/knowledge-bases/${kbId}/documents`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  getDocuments(kbId) {
    return request({
      url: `/knowledge-bases/${kbId}/documents`,
      method: 'get'
    })
  },
  
  deleteDocument(docId) {
    return request({
      url: `/documents/${docId}`,
      method: 'delete'
    })
  },
  
  getDocumentContent(docId) {
    return request({
      url: `/documents/${docId}/content`,
      method: 'get'
    })
  },
  
  grantPermission(kbId, data) {
    return request({
      url: `/knowledge-bases/${kbId}/permissions`,
      method: 'post',
      data
    })
  },
  
  revokePermission(kbId, userId, permissionType) {
    return request({
      url: `/knowledge-bases/${kbId}/permissions/${userId}/${permissionType}`,
      method: 'delete'
    })
  }
}

export const ragAPI = {
  search(data) {
    return request({
      url: '/search',
      method: 'post',
      data
    })
  },
  
  questionAnswer(data) {
    return request({
      url: '/qa',
      method: 'post',
      data
    })
  },
  
  questionAnswerStream(data, onChunk, onComplete, onError) {
    const token = localStorage.getItem('token')
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api/v1'
    
    console.log('Starting stream request to:', `${baseUrl}/qa/stream`)
    console.log('Request data:', data)
    
    return fetch(`${baseUrl}/qa/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    }).then(response => {
      console.log('Stream response status:', response.status)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('Stream completed')
            if (onComplete) onComplete()
            return
          }
          
          const chunk = decoder.decode(value, { stream: true })
          console.log('Raw chunk:', chunk)
          
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                console.log('Parsed chunk data:', data)
                if (onChunk) onChunk(data)
              } catch (e) {
                console.error('Failed to parse chunk:', e, 'Line:', line)
              }
            }
          }
          
          read()
        }).catch(error => {
          console.error('Stream read error:', error)
          if (onError) onError(error)
        })
      }
      
      read()
    }).catch(error => {
      console.error('Stream request error:', error)
      if (onError) onError(error)
    })
  },
  
  getStats() {
    return request({
      url: '/stats',
      method: 'get'
    })
  },
  
  getChatHistory(kbId, days = 7) {
    return request({
      url: '/query-logs',
      method: 'get',
      params: {
        knowledge_base_id: kbId,
        days: days
      }
    })
  }
}

export const fileAPI = {
  uploadFile(file, storageType = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (storageType) {
      formData.append('storage_type', storageType)
    }
    return request({
      url: '/files/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  getFile(fileId) {
    return request({
      url: `/files/${fileId}`,
      method: 'get'
    })
  },
  
  deleteFile(fileId) {
    return request({
      url: `/files/${fileId}`,
      method: 'delete'
    })
  }
}

export const departmentAPI = {
  getDepartments() {
    return request({
      url: '/departments',
      method: 'get'
    })
  },
  
  getDepartment(id) {
    return request({
      url: `/departments/${id}`,
      method: 'get'
    })
  },
  
  createDepartment(data) {
    return request({
      url: '/departments',
      method: 'post',
      data
    })
  },
  
  updateDepartment(id, data) {
    return request({
      url: `/departments/${id}`,
      method: 'put',
      data
    })
  },
  
  deleteDepartment(id) {
    return request({
      url: `/departments/${id}`,
      method: 'delete'
    })
  }
}

export const queryLogAPI = {
  getQueryLogs(params) {
    return request({
      url: '/query-logs',
      method: 'get',
      params
    })
  },
  
  getQueryLogStats() {
    return request({
      url: '/query-logs/stats',
      method: 'get'
    })
  }
}

const api = {
  ...authAPI,
  ...kbAPI,
  ...ragAPI,
  ...fileAPI,
  ...departmentAPI,
  ...queryLogAPI
}

export default api