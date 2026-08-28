<template>
  <div>
    <!-- Agent总览统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="6" v-for="s in agentStats" :key="s.agent">
        <el-card shadow="hover" :body-style="{ padding: '14px' }">
          <div style="text-align:center;">
            <div style="font-size:14px;font-weight:bold;margin-bottom:4px;">{{ s.display_name }}</div>
            <div style="font-size:12px;color:#909399;margin-bottom:8px;">{{ s.agent }}</div>
            <div style="font-size:28px;font-weight:bold;color:#409EFF;">{{ s.success_rate }}%</div>
            <div style="font-size:12px;color:#909399;margin-bottom:6px;">成功率</div>
            <div style="display:flex;justify-content:center;gap:12px;font-size:12px;">
              <span>执行 <strong>{{ s.total_runs }}</strong> 次</span>
              <span>平均 <strong>{{ s.avg_duration_sec }}s</strong></span>
            </div>
            <div v-if="s.failed_runs > 0" style="margin-top:6px;">
              <el-tag type="danger" size="small">{{ s.failed_runs }} 次失败</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细日志表格 -->
    <el-card shadow="hover">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>执行日志（最近100条）</span>
          <el-button size="small" @click="refresh">刷新</el-button>
        </div>
      </template>
      <el-table :data="logs" stripe v-loading="loading" style="width:100%;" :max-height="500">
        <el-table-column prop="display_agent" label="Agent" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.display_agent }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_sec" label="耗时" width="80" align="right">
          <template #default="{ row }">{{ row.duration_sec }}s</template>
        </el-table-column>
        <el-table-column prop="input" label="输入摘要" min-width="180" show-overflow-tooltip />
        <el-table-column prop="output" label="输出摘要" min-width="180" show-overflow-tooltip />
        <el-table-column prop="time" label="时间" width="150" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAgentLogs } from '../api'
import axios from 'axios'

const loading = ref(true)
const logs = ref([])
const agentStats = ref([])

const agentAlias = {
  content_analyzer: '内容分析',
  creative_analyzer: '创意拆解',
  scoring_agent: '评分总结',
  consumption_agent: '消耗分析',
  review_agent: '审核',
  prompt_optimizer: '提示词优化',
  script_generator: '脚本生成',
}

async function loadAll() {
  loading.value = true
  try {
    // 同时获取统计和日志
    const [statsRes, logsRes] = await Promise.all([
      axios.get('/api/agents/stats').then(r => r.data),
      getAgentLogs(100),
    ])
    agentStats.value = (statsRes.stats || []).sort((a, b) => b.total_runs - a.total_runs)

    const rawLogs = logsRes.logs || []
    logs.value = rawLogs.map(l => ({
      ...l,
      display_agent: agentAlias[l.agent] || l.agent,
      duration_sec: l.duration_ms ? (l.duration_ms / 1000).toFixed(1) : '-',
    }))
  } catch (e) {
    console.error('加载Agent监控失败:', e)
  }
  loading.value = false
}

async function refresh() {
  await loadAll()
}

onMounted(loadAll)
</script>

