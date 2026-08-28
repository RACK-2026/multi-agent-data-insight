<template>
  <div class="creative-workshop">
    <!-- 编导脚本建议 -->
    <el-card shadow="hover" style="margin-bottom: 16px;">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:20px;">🎬</span>
          <span style="font-weight:bold;font-size:16px;">编导脚本建议</span>
          <span style="font-size:12px;color:#909399;">—— 提交你对脚本优化的想法，帮助优化编导提示词</span>
        </div>
      </template>
      <el-input
        v-model="scriptSuggestion"
        type="textarea"
        :rows="4"
        placeholder="请描述您对脚本优化的建议，例如：希望能生成更多场景带入类型的脚本、前3秒的钩子可以更暴力一些..."
        style="margin-bottom:12px;"
      />
      <div style="display:flex;justify-content:flex-end;">
        <el-button type="primary" :loading="scriptLoading" @click="submitSuggestion('script')">
          提交建议
        </el-button>
      </div>
    </el-card>

    <!-- 标题创新建议 -->
    <el-card shadow="hover" style="margin-bottom: 16px;">
      <template #header>
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:20px;">💡</span>
          <span style="font-weight:bold;font-size:16px;">标题创新建议</span>
          <span style="font-size:12px;color:#909399;">—— 提交你对标题创新的想法，帮助优化标题提示词</span>
        </div>
      </template>
      <el-input
        v-model="titleSuggestion"
        type="textarea"
        :rows="4"
        placeholder="请描述您对标题创新的建议，例如：小红书平台的标题可以更注重情绪表达、抖音标题可以加入热搜词..."
        style="margin-bottom:12px;"
      />
      <div style="display:flex;justify-content:flex-end;">
        <el-button type="primary" :loading="titleLoading" @click="submitSuggestion('title')">
          提交建议
        </el-button>
      </div>
    </el-card>

    <!-- 已提交的建议历史 -->
    <el-card shadow="hover" v-if="suggestions.length">
      <template #header><span>已提交的建议</span></template>
      <div v-for="s in suggestions" :key="s.id" style="padding:8px 0;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center;">
        <div style="flex:1;">
          <el-tag size="small" :type="s.type === 'script' ? 'warning' : 'primary'" style="margin-right:8px;">
            {{ s.type === 'script' ? '🎬 编导脚本' : '💡 标题创新' }}
          </el-tag>
          <span style="font-size:13px;">{{ s.content.substring(0,60) }}{{ s.content.length > 60 ? '...' : '' }}</span>
        </div>
        <div style="font-size:11px;color:#909399;white-space:nowrap;margin-left:12px;">
          <el-tag size="small" :type="s.status === 'optimized' ? 'success' : 'info'">
            {{ {pending:'待评审',reviewed:'已评审',optimized:'已优化'}[s.status] || s.status }}
          </el-tag>
          {{ s.created_at?.substring(0,10) }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const scriptSuggestion = ref('')
const titleSuggestion = ref('')
const scriptLoading = ref(false)
const titleLoading = ref(false)
const suggestions = ref([])

async function submitSuggestion(type) {
  const content = type === 'script' ? scriptSuggestion.value : titleSuggestion.value
  if (!content.trim()) {
    ElMessage.warning('请先填写建议内容')
    return
  }
  if (type === 'script') scriptLoading.value = true
  else titleLoading.value = true
  try {
    const res = await axios.post('/api/workshop/suggestion', { type, content })
    ElMessage.success(res.data.message || '提交成功')
    if (type === 'script') scriptSuggestion.value = ''
    else titleSuggestion.value = ''
    await loadSuggestions()
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
  }
  if (type === 'script') scriptLoading.value = false
  else titleLoading.value = false
}

async function loadSuggestions() {
  try {
    const res = await axios.get('/api/workshop/suggestions')
    suggestions.value = (res.data.suggestions || []).slice(0, 30)
  } catch (e) { console.error(e) }
}

onMounted(loadSuggestions)
</script>

