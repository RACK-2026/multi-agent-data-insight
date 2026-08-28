<template>
  <div class="optimization">
    <!-- 智能洞察卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="8">
        <el-card shadow="hover" :body-style="{ padding: '16px' }">
          <div style="text-align:center;">
            <div style="font-size:13px;color:#909399;margin-bottom:8px;">高消耗视频特征</div>
            <div v-if="highFeatures" style="text-align:left;font-size:13px;">
              <div>平均消耗: <strong style="color:#f56c6c">{{ highFeatures.avg_cost }}</strong></div>
              <div>平均ROI: <strong :style="{ color: highFeatures.avg_roi >= 1 ? '#67c23a' : '#f56c6c' }">{{ highFeatures.avg_roi }}</strong></div>
              <div>平均完播率: <strong>{{ (highFeatures.avg_completion * 100).toFixed(1) }}%</strong></div>
              <div>平均时长: <strong>{{ highFeatures.avg_duration }}s</strong></div>
              <div style="margin-top:4px;font-size:12px;color:#909399;">
                主要产品:
                <el-tag v-for="p in highFeatures.top_products" :key="p.name" size="small" style="margin:2px;">{{ p.name }}</el-tag>
              </div>
            </div>
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" :body-style="{ padding: '16px' }">
          <div style="text-align:center;">
            <div style="font-size:13px;color:#909399;margin-bottom:8px;">低消耗视频特征</div>
            <div v-if="lowFeatures" style="text-align:left;font-size:13px;">
              <div>平均消耗: <strong style="color:#909399">{{ lowFeatures.avg_cost }}</strong></div>
              <div>平均ROI: <strong :style="{ color: lowFeatures.avg_roi >= 1 ? '#67c23a' : '#f56c6c' }">{{ lowFeatures.avg_roi }}</strong></div>
              <div>平均完播率: <strong>{{ (lowFeatures.avg_completion * 100).toFixed(1) }}%</strong></div>
              <div>平均时长: <strong>{{ lowFeatures.avg_duration }}s</strong></div>
              <div style="margin-top:4px;font-size:12px;color:#909399;">
                主要产品:
                <el-tag v-for="p in lowFeatures.top_products" :key="p.name" size="small" style="margin:2px;">{{ p.name }}</el-tag>
              </div>
            </div>
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" :body-style="{ padding: '16px' }">
          <div style="text-align:center;">
            <div style="font-size:13px;color:#909399;margin-bottom:8px;">高低消耗对比</div>
            <div v-if="highFeatures && lowFeatures" style="text-align:left;font-size:13px;">
              <div>完播率差值: <strong :style="{ color: compDiff.completion >= 0 ? '#67c23a' : '#f56c6c' }">{{ compDiff.completion >= 0 ? '+' : '' }}{{ (compDiff.completion * 100).toFixed(1) }}%</strong></div>
              <div>ROI差值: <strong :style="{ color: compDiff.roi >= 0 ? '#67c23a' : '#f56c6c' }">{{ compDiff.roi >= 0 ? '+' : '' }}{{ compDiff.roi }}</strong></div>
              <div>时长差值: <strong>{{ compDiff.duration >= 0 ? '+' : '' }}{{ compDiff.duration.toFixed(0) }}s</strong></div>
              <div style="margin-top:8px;padding:8px;background:#f5f7fa;border-radius:4px;font-size:12px;color:#606266;">
                {{ comparisonSummary }}
              </div>
            </div>
            <el-empty v-else description="暂无对比数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 优化建议列表 -->
    <el-card shadow="hover" style="margin-bottom: 16px;">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>优化建议清单 ({{ suggestions.length }})</span>
          <el-button size="small" type="primary" :loading="loading" @click="loadData">刷新</el-button>
        </div>
      </template>

      <div v-if="suggestions.length">
        <div v-for="(s, i) in suggestions" :key="i" style="margin-bottom:12px;padding:12px;border:1px solid #ebeef5;border-radius:4px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div>
              <el-tag :type="priorityType(s.priority)" size="small" style="margin-right:8px;">
                {{ priorityLabel(s.priority) }}
              </el-tag>
              <el-tag size="small" type="info">{{ s.category }}</el-tag>
              <strong style="margin-left:8px;">{{ s.title }}</strong>
            </div>
            <span v-if="s.metric" style="font-size:13px;color:#909399;">{{ s.metric }}</span>
          </div>
          <div style="font-size:13px;color:#606266;line-height:1.6;">{{ s.detail }}</div>
        </div>
      </div>
      <el-empty v-else description="暂无优化建议（数据量不足时无法生成）" />
    </el-card>

    <!-- 团队分析 -->
    <el-row :gutter="16" v-if="highFeatures || lowFeatures">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>高消耗视频主要编导</span></template>
          <div v-if="highFeatures?.top_directors?.length">
            <div v-for="d in highFeatures.top_directors" :key="d.name" style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0;">
              <span>{{ d.name }}</span>
              <el-tag size="small">{{ d.count }}条</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>低消耗视频主要编导</span></template>
          <div v-if="lowFeatures?.top_directors?.length">
            <div v-for="d in lowFeatures.top_directors" :key="d.name" style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0;">
              <span>{{ d.name }}</span>
              <el-tag size="small">{{ d.count }}条</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getOptimizationSummary } from '../api'

const loading = ref(true)
const suggestions = ref([])
const highFeatures = ref(null)
const lowFeatures = ref(null)

function priorityType(p) {
  return { high: 'danger', medium: 'warning', low: 'info' }[p] || 'info'
}

function priorityLabel(p) {
  return { high: '高优先级', medium: '中优先级', low: '参考' }[p] || p
}

const compDiff = computed(() => {
  if (!highFeatures.value || !lowFeatures.value) return { completion: 0, roi: 0, duration: 0 }
  return {
    completion: (highFeatures.value.avg_completion || 0) - (lowFeatures.value.avg_completion || 0),
    roi: (highFeatures.value.avg_roi || 0) - (lowFeatures.value.avg_roi || 0),
    duration: (highFeatures.value.avg_duration || 0) - (lowFeatures.value.avg_duration || 0),
  }
})

const comparisonSummary = computed(() => {
  const diffs = []
  const c = compDiff.value
  if (Math.abs(c.completion) > 0.02) diffs.push(`完播率${c.completion > 0 ? '高' : '低'}${(Math.abs(c.completion) * 100).toFixed(0)}%`)
  if (Math.abs(c.roi) > 0.1) diffs.push(`ROI${c.roi > 0 ? '高' : '低'}${Math.abs(c.roi).toFixed(1)}`)
  if (Math.abs(c.duration) > 3) diffs.push(`时长${c.duration > 0 ? '长' : '短'}${Math.abs(c.duration).toFixed(0)}s`)
  return diffs.length ? '高消耗视频相比低消耗: ' + diffs.join('、') : '高低消耗视频特征差异不明显'
})

async function loadData() {
  loading.value = true
  try {
    const data = await getOptimizationSummary()
    suggestions.value = data.suggestions || []
    highFeatures.value = data.high_cost_features || null
    lowFeatures.value = data.low_cost_features || null
  } catch (e) {
    console.error('加载优化建议失败:', e)
  }
  loading.value = false
}

onMounted(loadData)
</script>

