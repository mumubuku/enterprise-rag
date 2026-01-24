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
  
  getStats() {
    return request({
      url: '/stats',
      method: 'get'
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

const api = {
  ...authAPI,
  ...kbAPI,
  ...ragAPI,
  ...fileAPI
}

export default api