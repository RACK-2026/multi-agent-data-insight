import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 数据看板
export const getSummary = (params) => api.get('/dashboard/summary', { params }).then(r => r.data)
export const getTrend = (field, days, product = '', director = '') => api.get('/dashboard/trend', { params: { field, days, product, director } }).then(r => r.data)
export const getVideos = (params) => api.get('/dashboard/videos', { params }).then(r => r.data)
export const getVideoDetail = (id) => api.get(`/dashboard/videos/${id}`).then(r => r.data)
export const getProductStats = () => api.get('/dashboard/products').then(r => r.data)

// Agent
export const analyzeVideo = (recordId) => api.post('/agents/analyze', { record_id: recordId }).then(r => r.data)
export const batchAnalyze = (limit = 10) => api.post('/agents/analyze/batch', { limit }, { timeout: 180000 }).then(r => r.data)
export const getPrompts = () => api.get('/agents/prompts').then(r => r.data)
export const getPromptDetail = (agentName) => api.get(`/agents/prompts/${agentName}`).then(r => r.data)
export const triggerReview = () => api.post('/agents/review/trigger').then(r => r.data)
export const getAgentLogs = (limit = 50) => api.get('/agents/logs', { params: { limit } }).then(r => r.data)

// 复盘报告
export const getReviewSummary = () => api.get('/review/summary').then(r => r.data)
export const getReviewTop = (limit = 10, sortBy = '视频消耗') => api.get('/review/top', { params: { limit, sort_by: sortBy } }).then(r => r.data)
export const getReviewTrend = (field = '视频消耗', days = 30) => api.get('/review/trend', { params: { field, days } }).then(r => r.data)
export const getReviewTags = () => api.get('/review/tags').then(r => r.data)
export const getReviewAiAnalysis = (limit = 20) => api.get('/review/ai-analysis', { params: { limit } }).then(r => r.data)
export const getDailyReport = (startDate = '', endDate = '') => api.get('/review/daily-report', { params: { start_date: startDate, end_date: endDate } }).then(r => r.data)

// 优化建议
export const getOptimizationSummary = () => api.get('/optimization/summary').then(r => r.data)

// 脚本生成
export const generateScript = (recordId = '', notes = '') => api.post('/scripts/generate', { record_id: recordId, director_notes: notes }).then(r => r.data)
export const batchGenerateScripts = (count = 3) => api.post(`/scripts/generate/batch?count=${count}`).then(r => r.data)
export const getScripts = (status = '', limit = 50) => api.get('/scripts/scripts', { params: { status, limit } }).then(r => r.data)
export const reviewScript = (id, action, notes = '') => api.post(`/scripts/scripts/${id}/review`, { action, notes }).then(r => r.data)
export const updateScriptTag = (id, productionTag) => api.patch(`/scripts/scripts/${id}/tag`, { production_tag: productionTag }).then(r => r.data)
export const getLocalPrompts = () => api.get('/scripts/prompts/local').then(r => r.data)
export const getPromptHistory = (category) => api.get(`/scripts/prompts/local/${category}`).then(r => r.data)
export const saveLocalPrompt = (category, content, version = '', notes = '') => api.post('/scripts/prompts/local/save', { category, content, version, notes }).then(r => r.data)
export const optimizeFromFeedback = () => api.post('/scripts/optimize/feedback').then(r => r.data)

// 标题生成
export const generateTitles = (platform, productName = '', brand = '', focusPoint = '', productId = 0) => api.post('/titles/generate', {
  platform, product_name: productName, brand, focus_point: focusPoint, product_id: productId,
}).then(r => r.data)
export const getPlatforms = () => api.get('/titles/platforms').then(r => r.data)
export const getTitleList = (platform = '', limit = 50) => api.get('/titles/list', { params: { platform, limit } }).then(r => r.data)
export const reviewTitle = (id, action, notes = '') => api.post(`/titles/${id}/review`, { action, notes }).then(r => r.data)

// 产品管理
export const getProducts = () => api.get('/products').then(r => r.data)
export const getProductDetail = (id) => api.get(`/products/${id}`).then(r => r.data)
export const uploadProductFile = (formData) => api.post('/products/upload', formData, { timeout: 120000 }).then(r => r.data)
export const generateProductTags = (id) => api.post(`/products/${id}/generate-tags`).then(r => r.data)
export const deleteProduct = (id) => api.delete(`/products/${id}`).then(r => r.data)

export const getHealth = () => api.get('/health').then(r => r.data)
export const getConfig = () => api.get('/config').then(r => r.data)

export default api

