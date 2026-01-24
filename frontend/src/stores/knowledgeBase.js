import { defineStore } from 'pinia'
import { ref } from 'vue'
import { kbAPI } from '@/api'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  const knowledgeBases = ref([])
  const currentKB = ref(null)
  const documents = ref([])
  const loading = ref(false)
  
  async function fetchKnowledgeBases() {
    loading.value = true
    try {
      knowledgeBases.value = await kbAPI.getKnowledgeBases()
      return knowledgeBases.value
    } finally {
      loading.value = false
    }
  }
  
  async function createKnowledgeBase(data) {
    const kb = await kbAPI.createKnowledgeBase(data)
    knowledgeBases.value.push(kb)
    return kb
  }
  
  async function updateKnowledgeBase(id, data) {
    const kb = await kbAPI.updateKnowledgeBase(id, data)
    const index = knowledgeBases.value.findIndex(kb => kb.id === id)
    if (index !== -1) {
      knowledgeBases.value[index] = kb
    }
    return kb
  }
  
  async function deleteKnowledgeBase(id) {
    await kbAPI.deleteKnowledgeBase(id)
    knowledgeBases.value = knowledgeBases.value.filter(kb => kb.id !== id)
  }
  
  async function fetchDocuments(kbId) {
    loading.value = true
    try {
      documents.value = await kbAPI.getDocuments(kbId)
    } finally {
      loading.value = false
    }
  }
  
  async function uploadDocument(kbId, file) {
    const doc = await kbAPI.uploadDocument(kbId, file)
    documents.value.push(doc)
    return doc
  }
  
  async function deleteDocument(docId) {
    await kbAPI.deleteDocument(docId)
    documents.value = documents.value.filter(doc => doc.id !== docId)
  }
  
  function setCurrentKB(kb) {
    currentKB.value = kb
  }
  
  return {
    knowledgeBases,
    currentKB,
    documents,
    loading,
    fetchKnowledgeBases,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    setCurrentKB
  }
})