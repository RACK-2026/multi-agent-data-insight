<template>
  <div class="dashboard">
    <!-- 筛选器 -->
    <el-card shadow="hover" style="margin-bottom: 16px;">
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <span style="font-size:13px;color:#909399;">筛选：</span>
        <el-select v-model="filterProduct" placeholder="全部产品" clearable style="width:180px;" @change="reloadAll">
          <el-option v-for="p in productOptions" :key="p" :label="p" :value="p" />
        </el-select>
        <el-select v-model="filterDirector" placeholder="全部编导" clearable style="width:160px;" @change="reloadAll">
          <el-option v-for="d in directorOptions" :key="d" :label="d" :value="d" />
        </el-select>
        <el-tag v-if="filterProduct || filterDirector" type="info" closable @close="clearFilters" size="small">
          筛选中{{ filterProduct ? ' · ' + filterProduct : '' }}{{ filterDirector ? ' · ' + filterDirector : '' }}
        </el-tag>
      </div>
    </el-card>

    <!-- 关键指标卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="6" v-for="kpi in kpiCards" :key="kpi.label">
        <el-card shadow="hover" :body-style="{ padding: '16px' }">
          <div class="kpi-card">
            <div class="kpi-label">{{ kpi.label }}</div>
            <div class="kpi-value" :style="{ color: kpi.color }">{{ kpi.value }}</div>
            <div class="kpi-sub">{{ kpi.sub }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>消耗趋势</span>
              <el-radio-group v-model="trendField" size="small" @change="loadTrend">
                <el-radio-button value="视频消耗">消耗</el-radio-button>
                <el-radio-button value="完播率">完播率</el-radio-button>
                <el-radio-button value="整体支付ROI">ROI</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>产品消耗分布</span></template>
          <div ref="productChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 产品统计表 -->
    <el-card shadow="hover">
      <template #header><span>产品维度统计</span></template>
      <el-table :data="productStats" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="产品名称" min-width="120" />
        <el-table-column prop="count" label="视频数" width="80" align="center" />
        <el-table-column prop="total_cost" label="总消耗" width="120" align="right">
          <template #default="{ row }">{{ row.total_cost.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="avg_roi" label="平均ROI" width="100" align="right">
          <template #default="{ row }">{{ row.avg_roi.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="avg_completion_rate" label="完播率" width="100" align="right">
          <template #default="{ row }">{{ (row.avg_completion_rate * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="video_samples" label="代表视频" min-width="200">
          <template #default="{ row }">
            <el-tag v-for="v in row.video_samples.slice(0, 3)" :key="v" size="small" style="margin: 2px;">{{ v }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { getSummary, getTrend, getProductStats } from '../api'
import { formatNumber } from '../utils/format'
import * as echarts from 'echarts'

const loading = ref(true)
const trendField = ref('视频消耗')
const filterProduct = ref('')
const filterDirector = ref('')
const productOptions = ref([])
const directorOptions = ref([])

const kpiCards = ref([])
const productStats = ref([])
const trendChart = ref(null)
const productChart = ref(null)
let trendInstance = null
let productInstance = null

function clearFilters() {
  filterProduct.value = ''
  filterDirector.value = ''
  reloadAll()
}

async function reloadAll() {
  loading.value = true
  const params = {}
  if (filterProduct.value) params.product = filterProduct.value
  if (filterDirector.value) params.director = filterDirector.value
  try {
    const summary = await getSummary(params)
    const s = summary.summary || {}
    kpiCards.value = [
      { label: '记录数', value: summary.total_records || 0, color: '#409EFF', sub: '有效视频总量' },
      { label: '总消耗', value: formatNumber(s.total_cost), color: '#f56c6c', sub: '累计消耗金额' },
      { label: '平均ROI', value: formatNumber(s.avg_roi), color: '#67c23a', sub: '整体投产比' },
      { label: '平均完播率', value: formatNumber(s.avg_completion_rate * 100, 1) + '%', color: '#e6a23c', sub: '完播率' },
    ]

    // 提取筛选选项
    const fo = summary.filter_options || {}
    productOptions.value = fo.products || []
    directorOptions.value = fo.directors || []

    // 产品统计+图表
    const prodData = await getProductStats()
    productStats.value = prodData.products || []
    loading.value = false
    await nextTick()
    initProductChart(prodData.products || [])
    loadTrend()
  } catch (e) {
    loading.value = false
    console.error('加载看板失败:', e)
  }
}

async function loadTrend() {
  try {
    const data = await getTrend(trendField.value, 30, filterProduct.value, filterDirector.value)
    await nextTick()
    initTrendChart(data.trend || [])
  } catch (e) {
    console.error('加载趋势失败:', e)
  }
}

function initTrendChart(trend) {
  if (!trendChart.value) return
  if (!trendInstance) trendInstance = echarts.init(trendChart.value)
  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: trend.map(t => t.date?.substring(5) || ''), axisLabel: { rotate: 45, fontSize: 11 } },
    yAxis: { type: 'value' },
    series: [{ data: trend.map(t => t.value), type: 'line', smooth: true, areaStyle: { opacity: 0.15 } }],
  })
}

function initProductChart(products) {
  if (!productChart.value) return
  if (!productInstance) productInstance = echarts.init(productChart.value)
  const top5 = products.slice(0, 8)
  productInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    series: [{ type: 'pie', radius: ['30%', '60%'], data: top5.map(p => ({ name: p.name, value: p.total_cost })), label: { show: true, fontSize: 11, formatter: '{b}' } }],
  })
}

onMounted(reloadAll)
</script>

<style scoped>
.kpi-card { text-align: center; }
.kpi-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: bold; margin-bottom: 4px; }
.kpi-sub { font-size: 12px; color: #c0c4cc; }
</style>

