<template>
  <div class="prompt-manager">
    <!-- 分类Tab -->
    <el-tabs v-model="activeTab" type="card" @tab-change="loadPrompts">
      <el-tab-pane label="🎬 编导提示词" name="director">
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
          <el-card v-for="a in directorAgents" :key="a.key" :class="['agent-card', selectedAgent === a.key ? 'agent-card-active' : '']"
            shadow="hover" :body-style="{ padding: '12px 16px' }" @click="selectAgent(a.key)" style="cursor:pointer;width:160px;">
            <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">{{ a.display }}</div>
            <div style="font-size:11px;color:#909399;">v{{ a.version }}</div>
            <div style="font-size:11px;color:#909399;">{{ a.updated }}</div>
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="💡 标题提示词" name="title">
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">
          <el-card v-for="a in titleAgents" :key="a.key" :class="['agent-card', selectedAgent === a.key ? 'agent-card-active' : '']"
            shadow="hover" :body-style="{ padding: '12px 16px' }" @click="selectAgent(a.key)" style="cursor:pointer;width:160px;">
            <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">{{ a.display }}</div>
            <div style="font-size:11px;color:#909399;">v{{ a.version }}</div>
            <div style="font-size:11px;color:#909399;">{{ a.updated }}</div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 当前Agent提示词编辑器 -->
    <el-card shadow="hover" v-if="currentPrompt" style="margin-bottom:16px;">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div>
            <strong>{{ currentDisplay }}</strong>
            <el-tag size="small" style="margin-left:8px;">v{{ currentPrompt.version }}</el-tag>
            <el-tag size="small" type="info" style="margin-left:4px;">{{ currentPrompt.source }}</el-tag>
            <span style="font-size:12px;color:#909399;margin-left:8px;">{{ currentPrompt.created_at }}</span>
          </div>
          <div style="display:flex;gap:8px;">
            <el-button size="small" @click="loadHistory">查看历史 ({{ historyCount }})</el-button>
            <el-button size="small" type="primary" :loading="saving" @click="saveAsNew">保存为新版本</el-button>
          </div>
        </div>
      </template>
      <el-input type="textarea" :rows="16" v-model="editingContent" placeholder="提示词内容(JSON格式)" style="font-family:'Courier New',monospace;font-size:13px;" />
      <div style="margin-top:8px;font-size:12px;color:#909399;">
        <el-input v-model="saveNotes" placeholder="本次修改说明（选填）" size="small" style="width:400px;" />
      </div>
    </el-card>

    <!-- 历史版本对话框 -->
    <el-dialog v-model="historyVisible" title="历史版本" width="75%" top="5vh">
      <el-timeline>
        <el-timeline-item v-for="h in historyList" :key="h.id" :timestamp="h.created_at" placement="top">
          <el-card shadow="never">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <div>
                <strong>v{{ h.version }}</strong>
                <el-tag size="small" style="margin-left:8px;">{{ h.source }}</el-tag>
                <el-tag v-if="h.is_active" size="small" type="success" style="margin-left:4px;">当前</el-tag>
              </div>
            </div>
            <div v-if="h.notes" style="font-size:12px;color:#e6a23c;margin-bottom:4px;">备注: {{ h.notes }}</div>
            <pre style="background:#f5f7fa;padding:12px;border-radius:4px;font-size:12px;max-height:200px;overflow:auto;white-space:pre-wrap;">{{ h.content }}</pre>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLocalPrompts, getPromptHistory, saveLocalPrompt } from '../api'

const activeTab = ref('director')
const selectedAgent = ref('script_generator')
const allPrompts = ref({})
const currentPrompt = ref(null)
const editingContent = ref('')
const saving = ref(false)
const saveNotes = ref('')

const historyVisible = ref(false)
const historyList = ref([])
const historyCount = computed(() => historyList.value.length)

const agentConfig = {
  script_generator: { display: '脚本生成Agent', group: 'director', order: 1 },
  content_analyzer: { display: '内容分析Agent', group: 'director', order: 2 },
  creative_analyzer: { display: '创意拆解Agent', group: 'director', order: 3 },
  scoring_agent: { display: '评分总结Agent', group: 'director', order: 4 },
  consumption_agent: { display: '消耗分析Agent', group: 'director', order: 5 },
  review_agent: { display: '审核Agent', group: 'title', order: 1 },
  prompt_optimizer: { display: '提示词优化Agent', group: 'title', order: 2 },
  title_generator: { display: '标题生成Agent', group: 'title', order: 3 },
}

const currentDisplay = computed(() => agentConfig[selectedAgent.value]?.display || selectedAgent.value)

const directorAgents = computed(() => {
  return Object.entries(allPrompts.value)
    .filter(([k]) => agentConfig[k]?.group === 'director')
    .sort((a, b) => (agentConfig[a[0]]?.order || 99) - (agentConfig[b[0]]?.order || 99))
    .map(([k, v]) => ({ key: k, display: agentConfig[k]?.display || k, version: v.version, updated: v.created_at?.substring(0, 10) || '' }))
})

const titleAgents = computed(() => {
  return Object.entries(allPrompts.value)
    .filter(([k]) => agentConfig[k]?.group === 'title')
    .sort((a, b) => (agentConfig[a[0]]?.order || 99) - (agentConfig[b[0]]?.order || 99))
    .map(([k, v]) => ({ key: k, display: agentConfig[k]?.display || k, version: v.version, updated: v.created_at?.substring(0, 10) || '' }))
})

function selectAgent(key) {
  selectedAgent.value = key
  const p = allPrompts.value[key]
  if (p) {
    currentPrompt.value = p
    editingContent.value = p.full_content || p.content || ''
  } else {
    currentPrompt.value = null
    editingContent.value = ''
  }
}

async function loadPrompts() {
  try {
    const data = await getLocalPrompts()
    allPrompts.value = data.prompts || {}
    selectAgent(selectedAgent.value)
  } catch (e) { console.error(e) }
}

async function loadHistory() {
  try {
    const data = await getPromptHistory(selectedAgent.value)
    historyList.value = data.history || []
    historyVisible.value = true
  } catch (e) { console.error(e) }
}

async function saveAsNew() {
  if (!editingContent.value.trim()) {
    ElMessage.warning('请输入提示词内容')
    return
  }
  saving.value = true
  try {
    await saveLocalPrompt(selectedAgent.value, editingContent.value, '', saveNotes.value || 'Web端编辑')
    ElMessage.success('已保存为新版本')
    saveNotes.value = ''
    await loadPrompts()
  } catch (e) {
    ElMessage.error('保存失败: ' + e.message)
  }
  saving.value = false
}

onMounted(loadPrompts)
</script>

<style scoped>
.agent-card { transition: all 0.2s; border: 2px solid transparent; }
.agent-card:hover { border-color: #409EFF; transform: translateY(-2px); }
.agent-card-active { border-color: #409EFF; background: #ecf5ff; }
</style>

