<template>
  <div class="video-list">
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div style="display:flex;gap:8px;align-items:center;">
            <span>千川视频列表</span>
            <el-select v-model="filterProduct" placeholder="全部产品" clearable size="small" style="width:150px;" @change="refresh">
              <el-option v-for="p in productOptions" :key="p" :label="p" :value="p" />
            </el-select>
            <el-select v-model="filterDirector" placeholder="全部编导" clearable size="small" style="width:150px;" @change="refresh">
              <el-option v-for="d in directorOptions" :key="d" :label="d" :value="d" />
            </el-select>
          </div>
          <div>
            <el-button size="small" @click="refresh">刷新</el-button>
            <el-button size="small" type="primary" :loading="analyzing" @click="runAnalysis">
              AI分析最新10条
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="videos" stripe v-loading="loading" style="width: 100%" :default-sort="{ prop: '视频消耗', order: 'descending' }">
        <el-table-column prop="视频名称" label="视频名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="产品名称" label="产品" width="80" />
        <el-table-column prop="品牌" label="品牌" width="80" />
        <el-table-column prop="编导" label="编导" width="70" />
        <el-table-column prop="时长" label="时长" width="60" align="right">
          <template #default="{ row }">{{ row.时长 ? row.时长 + 's' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="视频消耗" label="消耗" width="90" align="right" sortable>
          <template #default="{ row }">{{ formatNumber(row.视频消耗) }}</template>
        </el-table-column>
        <el-table-column prop="整体支付ROI" label="ROI" width="70" align="right" sortable>
          <template #default="{ row }">{{ formatNumber(row.整体支付ROI, 1) }}</template>
        </el-table-column>
        <el-table-column prop="完播率" label="完播率" width="75" align="right" sortable>
          <template #default="{ row }">{{ row.完播率 ? (row.完播率*100).toFixed(1)+'%' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="2秒播放率" label="2s播放" width="70" align="right">
          <template #default="{ row }">{{ row['2秒播放率'] ? (row['2秒播放率']*100).toFixed(1)+'%' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="3秒播放率" label="3s播放" width="70" align="right">
          <template #default="{ row }">{{ row['3秒播放率'] ? (row['3秒播放率']*100).toFixed(1)+'%' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="净成交ROI" label="净ROI" width="70" align="right">
          <template #default="{ row }">{{ formatNumber(row['净成交ROI'], 1) }}</template>
        </el-table-column>
        <el-table-column prop="整体点击率" label="点击率" width="70" align="right">
          <template #default="{ row }">{{ row['整体点击率'] ? row['整体点击率']+'%' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="采集时间" label="采集时间" width="110" />
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push('/videos/' + row.record_id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="text-align: center; margin-top: 16px;">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadVideos"
        />
      </div>
    </el-card>

    <!-- 分析结果对话框 -->
    <el-dialog v-model="resultVisible" title="AI分析结果" width="80%" top="5vh">
      <pre style="max-height: 60vh; overflow: auto; background: #f5f7fa; padding: 16px; border-radius: 4px; white-space: pre-wrap;">{{ analysisResult }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getVideos, batchAnalyze } from '../api'
import { formatNumber } from '../utils/format'

const videos = ref([])
const loading = ref(true)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const analyzing = ref(false)
const resultVisible = ref(false)
const analysisResult = ref('')
const filterProduct = ref('')
const filterDirector = ref('')
const productOptions = ref([])
const directorOptions = ref([])

async function loadVideos() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterProduct.value) params.product = filterProduct.value
    if (filterDirector.value) params.director = filterDirector.value
    const data = await getVideos(params)
    videos.value = data.items || []
    total.value = data.total || 0
    // 从API返回的filter_options中提取下拉选项
    const fo = data.filter_options || {}
    if (fo.products) productOptions.value = fo.products
    if (fo.directors) directorOptions.value = fo.directors
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

async function refresh() {
  page.value = 1
  await loadVideos()
}

async function runAnalysis() {
  analyzing.value = true
  try {
    const result = await batchAnalyze(10)
    analysisResult.value = JSON.stringify(result, null, 2)
    resultVisible.value = true
  } catch (e) {
    analysisResult.value = '分析失败: ' + e.message
    resultVisible.value = true
  }
  analyzing.value = false
}

onMounted(loadVideos)
</script>

