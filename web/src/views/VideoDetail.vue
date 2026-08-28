<template>
  <div>
    <!-- 加载错误提示 -->
    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="error"
      show-icon
      style="margin-bottom:16px;"
      :closable="false"
    />

    <!-- 视频基本信息 -->
    <el-card shadow="hover" v-if="video">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>视频分析详情</span>
          <el-button size="small" type="primary" :loading="analyzing" @click="analyze">AI分析</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="视频名称" :span="2">{{ video.视频名称 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="产品">{{ video.产品名称 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ video.品牌 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="编导">{{ video.编导 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="剪辑">{{ video.剪辑 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时长">{{ video.时长 ? video.时长+'秒' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="消耗">{{ video.视频消耗 || '-' }}</el-descriptions-item>
        <el-descriptions-item label="ROI">{{ video.整体支付ROI || '-' }}</el-descriptions-item>
        <el-descriptions-item label="完播率">{{ video.完播率 ? (video.完播率*100).toFixed(1)+'%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="2秒播放率">{{ video['2秒播放率'] ? (video['2秒播放率']*100).toFixed(1)+'%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="3秒播放率">{{ video['3秒播放率'] ? (video['3秒播放率']*100).toFixed(1)+'%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="点击率">{{ video['整体点击率(%)'] ? video['整体点击率(%)']+'%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="转化率">{{ video['整体转化率(%)'] ? video['整体转化率(%)']+'%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="净成交ROI">{{ video['净成交ROI'] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="千次展现费用">{{ video['千次展现费用'] || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 分析结果 -->
    <el-card shadow="hover" style="margin-top: 16px;" v-if="analysis">
      <template #header><span>AI分析结果</span></template>
      <el-tabs>
        <el-tab-pane label="内容分析">
          <div v-if="analysis.content_analysis?.summary">
            <h4>总结</h4>
            <p style="white-space:pre-wrap;line-height:1.7;">{{ analysis.content_analysis.summary }}</p>
          </div>
          <div v-else style="color:#909399;padding:12px;">暂无内容分析数据，请先执行AI分析</div>
        </el-tab-pane>
        <el-tab-pane label="评分">
          <div v-if="analysis.scoring" style="text-align:center;padding:20px;">
            <div style="font-size:48px;font-weight:bold;color:#409EFF;">{{ analysis.scoring.overall_score || '-' }}</div>
            <div style="font-size:14px;color:#909399;">综合评分</div>
            <div style="margin-top:8px;">
              <el-tag :type="analysis.scoring.level === '优质' ? 'success' : analysis.scoring.level === '普通' ? 'warning' : 'info'">
                {{ analysis.scoring.level || '未知' }}
              </el-tag>
            </div>
            <div style="margin-top:16px;text-align:left;">
              <div v-for="s in (analysis.scoring.strengths || [])" :key="s" style="padding:4px 0;">✅ {{ s }}</div>
              <div v-for="w in (analysis.scoring.weaknesses || [])" :key="w" style="padding:4px 0;">⚠️ {{ w }}</div>
            </div>
          </div>
          <div v-else style="color:#909399;padding:12px;">暂无评分数据</div>
        </el-tab-pane>
        <el-tab-pane label="消耗分析">
          <pre v-if="analysis.consumption_analysis" style="background:#f5f7fa;padding:12px;border-radius:4px;white-space:pre-wrap;font-size:13px;">{{ JSON.stringify(analysis.consumption_analysis, null, 2) }}</pre>
          <div v-else style="color:#909399;padding:12px;">暂无消耗分析数据</div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { analyzeVideo } from '../api'
import axios from 'axios'

const route = useRoute()
const video = ref(null)
const analysis = ref(null)
const analyzing = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  try {
    const res = await axios.get('/api/dashboard/videos/' + route.params.id + '/full')
    if (res.data.error) {
      errorMsg.value = '未找到该视频记录，record_id: ' + route.params.id
    } else {
      video.value = { ...res.data.basic, ...res.data.ai_analysis, record_id: res.data.record_id }
    }
  } catch (e) {
    errorMsg.value = '加载视频详情失败: ' + (e.response?.data?.detail || e.message)
  }
})

async function analyze() {
  analyzing.value = true
  try {
    analysis.value = await analyzeVideo(route.params.id)
  } catch (e) {
    analysis.value = { error: '分析失败: ' + e.message }
  }
  analyzing.value = false
}
</script>

