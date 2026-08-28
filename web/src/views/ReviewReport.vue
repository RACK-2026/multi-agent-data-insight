<template>
  <div class="review-report">
    <!-- 日期筛选 -->
    <el-card shadow="hover" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <span style="font-size:13px;color:#6B7280;font-weight:500;">报告日期：</span>
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至"
          start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD"
          style="width:280px;" @change="loadReport" />
        <button :class="['sg-btn', quickDate === 'today' ? 'sg-btn-primary' : 'sg-btn-outline']" @click="quickDate='today';loadToday()">今日</button>
        <button :class="['sg-btn', quickDate === 'week' ? 'sg-btn-primary' : 'sg-btn-outline']" @click="quickDate='week';loadWeek()">本周</button>
        <button :class="['sg-btn', quickDate === 'month' ? 'sg-btn-primary' : 'sg-btn-outline']" @click="quickDate='month';loadMonth()">本月</button>
        <el-tag v-if="dateRange" type="info" closable @close="clearDate" size="small">{{ dateRange[0] }} ~ {{ dateRange[1] }}</el-tag>
      </div>
    </el-card>

    <!-- ===== 总览KPI ===== -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;" v-if="summary">
      <div class="kpi-card2"><div class="kpi-label">报告天数</div><div class="kpi-value">{{ days.length }}</div></div>
      <div class="kpi-card2"><div class="kpi-label">总消耗</div><div class="kpi-value" style="color:#EF4444;">{{ formatNum(summary.total_cost) }}</div></div>
      <div class="kpi-card2"><div class="kpi-label">平均ROI</div><div class="kpi-value" :style="{color: summary.avg_roi >= 1 ? '#10B981' : '#EF4444'}">{{ formatNum(summary.avg_roi) }}</div></div>
      <div class="kpi-card2"><div class="kpi-label">日均视频数</div><div class="kpi-value">{{ summary.avg_daily_videos }}</div></div>
    </div>

    <!-- ===== 数据概况文字总结 ===== -->
    <el-card shadow="hover" style="margin-bottom:20px;" v-if="days.length">
      <template #header><span style="font-weight:600;font-size:15px;">📊 数据概况</span></template>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div>
          <div class="insight-item"><span class="insight-label">总视频数</span><span class="insight-value">{{ totalVideos }}</span></div>
          <div class="insight-item"><span class="insight-label">总消耗</span><span class="insight-value" style="color:#EF4444;">{{ formatNum(summary.total_cost) }}</span></div>
          <div class="insight-item"><span class="insight-label">平均ROI</span><span class="insight-value" :style="{color: summary.avg_roi >= 1 ? '#10B981' : '#EF4444'}">{{ formatNum(summary.avg_roi) }}</span></div>
          <div class="insight-item"><span class="insight-label">平均完播率</span><span class="insight-value">{{ avgCompletion }}</span></div>
        </div>
        <div>
          <div class="insight-item"><span class="insight-label">平均点击率</span><span class="insight-value">{{ avgClickRate }}</span></div>
          <div class="insight-item"><span class="insight-label">高点播(>60%)</span><span class="insight-value">{{ highPlayCount }}条</span></div>
          <div class="insight-item"><span class="insight-label">低完播(&lt;10%)</span><span class="insight-value">{{ lowCompCount }}条</span></div>
          <div class="insight-item"><span class="insight-label">ROI>1占比</span><span class="insight-value">{{ roiHealth }}%</span></div>
        </div>
      </div>
    </el-card>

    <!-- ===== 产品排行 ===== -->
    <el-row :gutter="16" style="margin-bottom:20px;" v-if="productRanking.length">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span style="font-weight:600;">🏆 产品消耗排行</span></template>
          <div v-for="(p,i) in productRanking" :key="p.name" class="rank-row">
            <span class="rank-num">{{ i+1 }}</span>
            <span class="rank-name">{{ p.name }}</span>
            <span class="rank-bar-bg"><span class="rank-bar" :style="{width: p.pct+'%'}"></span></span>
            <span class="rank-value">{{ formatNum(p.cost) }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span style="font-weight:600;">🏆 编导视频量排行</span></template>
          <div v-for="(d,i) in directorRanking" :key="d.name" class="rank-row">
            <span class="rank-num">{{ i+1 }}</span>
            <span class="rank-name">{{ d.name }}</span>
            <span class="rank-bar-bg"><span class="rank-bar bar-green" :style="{width: d.pct+'%'}"></span></span>
            <span class="rank-value">{{ d.count }}条</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ===== 每日明细表 ===== -->
    <el-card shadow="hover" v-if="days.length">
      <template #header><span style="font-weight:600;">📋 每日详细数据</span></template>
      <el-table :data="days" stripe style="width:100%;">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="video_count" label="视频数" width="70" align="center" />
        <el-table-column prop="total_cost" label="消耗" width="100" align="right">
          <template #default="{ row }">{{ formatNum(row.total_cost) }}</template>
        </el-table-column>
        <el-table-column prop="avg_roi" label="平均ROI" width="80" align="right" />
        <el-table-column label="完播率" width="80" align="right">
          <template #default="{ row }">{{ (row.avg_completion * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column label="点击率" width="70" align="right">
          <template #default="{ row }">{{ row.avg_click_rate }}%</template>
        </el-table-column>
        <el-table-column label="主要产品" min-width="140">
          <template #default="{ row }">
            <span v-for="p in (row.top_products||[]).slice(0,3)" :key="p[0]" class="mini-tag">{{ p[0] }}({{ p[1] }})</span>
          </template>
        </el-table-column>
        <el-table-column label="主要编导" min-width="140">
          <template #default="{ row }">
            <span v-for="d in (row.top_directors||[]).slice(0,3)" :key="d[0]" class="mini-tag mini-tag-green">{{ d[0] }}({{ d[1] }})</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-empty v-else-if="!loading" :description="hasSearched ? '所选日期范围内暂无数据' : '选择日期范围查看每日数据分析报告'" style="margin-top:40px;" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDailyReport } from '../api'

const dateRange = ref(null)
const quickDate = ref('month')
const days = ref([])
const summary = ref(null)
const change = ref(null)
const loading = ref(true)
const hasSearched = ref(false)

const totalVideos = computed(() => days.value.reduce((s,d) => s + d.video_count, 0))
const avgCompletion = computed(() => {
  const v = days.value.filter(d => d.avg_completion)
  if (!v.length) return '-'
  return (v.reduce((s,d) => s + d.avg_completion, 0) / v.length * 100).toFixed(1) + '%'
})
const avgClickRate = computed(() => {
  const v = days.value.filter(d => d.avg_click_rate)
  if (!v.length) return '-'
  return (v.reduce((s,d) => s + d.avg_click_rate, 0) / v.length).toFixed(2) + '%'
})
const highPlayCount = computed(() => {
  // approx 2s play rate - not in daily data directly, use a proxy
  return '—'
})
const lowCompCount = computed(() => '—')
const roiHealth = computed(() => '—')

const productRanking = computed(() => {
  if (!days.value.length) return []
  const map = {}
  for (const d of days.value) {
    for (const [name, count] of (d.top_products || [])) {
      map[name] = (map[name] || 0) + count
    }
  }
  const max = Math.max(...Object.values(map), 1)
  return Object.entries(map).sort((a,b) => b[1]-a[1]).map(([name, count]) => ({
    name, count, cost: summary.value?.total_cost || 0,
    pct: Math.round(count / max * 80)
  }))
})

const directorRanking = computed(() => {
  if (!days.value.length) return []
  const map = {}
  for (const d of days.value) {
    for (const [name, count] of (d.top_directors || [])) {
      map[name] = (map[name] || 0) + count
    }
  }
  const max = Math.max(...Object.values(map), 1)
  return Object.entries(map).sort((a,b) => b[1]-a[1]).map(([name, count]) => ({
    name, count,
    pct: Math.round(count / max * 80)
  }))
})

function formatNum(val, d = 2) {
  if (val === null || val === undefined) return '-'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d })
}

function clearDate() { dateRange.value = null; days.value = []; summary.value = null; change.value = null }

async function loadReport() {
  if (!dateRange.value || !dateRange.value[0]) return
  loading.value = true; hasSearched.value = true
  try {
    const data = await getDailyReport(dateRange.value[0], dateRange.value[1])
    days.value = data.days || []
    summary.value = data.summary || null
    change.value = data.change || null
  } catch (e) { console.error('加载报告失败:', e) }
  loading.value = false
}

function loadToday() {
  const d = new Date().toISOString().substring(0, 10)
  dateRange.value = [d, d]; loadReport()
}
function loadWeek() {
  const now = new Date(); const end = now.toISOString().substring(0,10)
  const start = new Date(now.getTime() - 7*86400000).toISOString().substring(0,10)
  dateRange.value = [start, end]; loadReport()
}
function loadMonth() {
  const now = new Date(); const end = now.toISOString().substring(0,10)
  const start = new Date(now.getTime() - 30*86400000).toISOString().substring(0,10)
  dateRange.value = [start, end]; loadReport()
}

onMounted(() => loadMonth())
</script>

<style scoped>
.sg-btn {
  display:inline-flex;align-items:center;gap:4px;padding:6px 14px;border-radius:6px;
  font-size:13px;font-weight:500;cursor:pointer;transition:all .15s;border:none;font-family:inherit;
}
.sg-btn-primary { background:#3B82F6; color:#fff; }
.sg-btn-primary:hover { background:#2563EB; }
.sg-btn-outline { background:#fff; color:#6B7280; border:1px solid #E5E7EB; }
.sg-btn-outline:hover { border-color:#D1D5DB; background:#F9FAFB; }

.kpi-card2 {
  background:#fff; border-radius:8px; padding:18px 16px; text-align:center;
  box-shadow:0 1px 3px rgba(0,0,0,.06);
}
.kpi-label { font-size:12px; color:#6B7280; margin-bottom:6px; }
.kpi-value { font-size:26px; font-weight:700; color:#1A1A2E; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; }

.insight-item { display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #F3F4F6; }
.insight-item:last-child { border:none; }
.insight-label { font-size:13px; color:#6B7280; }
.insight-value { font-size:14px; font-weight:700; color:#1A1A2E; }

.rank-row { display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid #F3F4F6; }
.rank-row:last-child { border:none; }
.rank-num { width:20px; font-size:12px; font-weight:700; color:#9CA3AF; }
.rank-name { width:100px; font-size:13px; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rank-bar-bg { flex:1; height:6px; background:#F3F4F6; border-radius:3px; overflow:hidden; }
.rank-bar { display:block; height:100%; background:#3B82F6; border-radius:3px; transition:width .3s; }
.bar-green { background:#10B981; }
.rank-value { width:70px; text-align:right; font-size:13px; font-weight:600; color:#1A1A2E; }

.mini-tag {
  display:inline-block; padding:1px 6px; margin:1px;
  background:#F3F4F6; border-radius:3px; font-size:11px; color:#4B5563;
}
.mini-tag-green { background:#D1FAE5; color:#065F46; }
</style>

