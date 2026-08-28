<template>
  <div class="title-generator">
    <!-- 产品选择 -->
    <el-card shadow="hover" style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <span style="font-size:13px;color:#909399;">关联产品：</span>
        <el-select v-model="selectedProductId" placeholder="选择产品（标题将基于该产品生成）" clearable filterable style="width:280px;" @change="onProductChange">
          <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id">
            <span>{{ p.name }}</span>
            <span style="font-size:11px;color:#909399;margin-left:8px;">{{ (p.tags||[]).slice(0,2).join('、') }}</span>
          </el-option>
        </el-select>
      </div>
      <!-- 选中的产品详情 -->
      <div v-if="selectedProduct" style="margin-top:8px;padding:8px 12px;background:#f8fafc;border-radius:6px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <strong style="font-size:14px;">{{ selectedProduct.name }}</strong>
            <el-tag v-for="t in (selectedProduct.tags||[])" :key="t" size="small" style="margin-left:4px;">{{ t }}</el-tag>
          </div>
        </div>
        <div style="font-size:12px;color:#606266;margin-top:4px;">{{ (selectedProduct.details||'').substring(0,200) }}</div>
      </div>
    </el-card>

    <el-card shadow="hover" style="margin-bottom: 16px;">
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
        <div style="display:flex;gap:4px;flex-wrap:wrap;">
          <el-button v-for="p in platforms" :key="p.key" :type="currentPlatform === p.key ? 'primary' : 'default'" size="small" @click="switchPlatform(p.key)">{{ p.icon }} {{ p.name }}</el-button>
        </div>
        <el-button type="primary" :loading="genLoading" @click="doGenerate">{{ genLoading ? '生成中...' : '🎯 生成5个标题' }}</el-button>
        <el-button size="small" @click="loadTitles">刷新历史</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" v-if="titles.length">
      <template #header>
        <span>生成的标题（点击卡片复制，可审核打勾/打叉）</span>
      </template>
      <div v-for="t in titles" :key="t.id" style="border:1px solid #ebeef5;border-radius:6px;padding:12px;margin-bottom:8px;" :class="'title-card-' + t.review_status">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
          <div style="flex:1;">
            <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px;flex-wrap:wrap;">
              <el-tag size="small">{{ t.platform }}</el-tag>
              <el-tag v-if="t.style_tag" size="small" :type="tagType(t.style_tag)">{{ t.style_tag }}</el-tag>
              <el-tag :type="t.review_status === 'approved' ? 'success' : t.review_status === 'rejected' ? 'danger' : 'info'" size="small">
                {{ {pending:'待审核',approved:'已通过',rejected:'已拒绝'}[t.review_status] || t.review_status }}
              </el-tag>
            </div>
            <div style="font-size:16px;line-height:1.5;cursor:pointer;" @click="copyTitle(t.title_text)" title="点击复制">
              {{ t.title_text }}
            </div>
            <div v-if="t.reason" style="font-size:12px;color:#909399;margin-top:4px;">{{ t.reason }}</div>
            <!-- 参考来源显示 -->
            <div v-if="t.reference_title" style="margin-top:4px;font-size:11px;color:#909399;border-top:1px dashed #eee;padding-top:4px;">
              参考: 「{{ t.reference_title }}」 👍 {{ t.reference_likes || '?' }}
            </div>
          </div>
          <div style="display:flex;gap:4px;flex-shrink:0;align-items:center;">
            <el-button size="small" :type="t.review_status === 'approved' ? 'success' : 'default'" :disabled="t.review_status === 'approved'" @click="review(t.id, 'approved')">
              👍 通过
            </el-button>
            <el-button size="small" :type="t.review_status === 'rejected' ? 'danger' : 'default'" :disabled="t.review_status === 'rejected'" @click="review(t.id, 'rejected')">
              👎 拒绝
            </el-button>
            <el-input v-model="reviewNotes[t.id]" placeholder="备注" size="small" style="width:160px;" clearable />
          </div>
        </div>
      </div>
    </el-card>
    <el-empty v-else description="暂无标题，点击生成" style="margin-top:40px;" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlatforms, generateTitles as apiGenerateTitles, getTitleList, reviewTitle, getProducts } from '../api'

const platforms = ref([])
const currentPlatform = ref('douyin')
const titles = ref([])
const genLoading = ref(false)
const reviewNotes = ref({})
const products = ref([])
const selectedProductId = ref(null)
const selectedProduct = ref(null)

async function loadProducts() {
  try {
    const data = await getProducts()
    products.value = data.products || []
  } catch (e) { console.error(e) }
}

function onProductChange(id) {
  if (!id) { selectedProduct.value = null; return }
  selectedProduct.value = products.value.find(p => p.id === id) || null
}

function tagType(tag) {
  const m = { '好奇心': 'warning', '痛点': 'danger', '价格': 'success', '信任': 'primary', '场景': '' }
  return m[tag] || 'info'
}

function switchPlatform(key) {
  currentPlatform.value = key
}

function loadTitles() {
  getTitleList(currentPlatform.value, 50).then(data => {
    titles.value = data.titles || []
  }).catch(e => console.error(e))
}

async function doGenerate() {
  genLoading.value = true
  try {
    await apiGenerateTitles(currentPlatform.value, '', '', '', selectedProductId.value || 0)
    ElMessage.success('生成完成')
    await loadTitles()
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  }
  genLoading.value = false
}

async function review(id, action) {
  try {
    await reviewTitle(id, action, reviewNotes.value[id] || '')
    reviewNotes.value[id] = ''
    ElMessage.success(action === 'approved' ? '已标记通过' : '已拒绝')
    await loadTitles()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function copyTitle(text) {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制: ' + text.substring(0, 20) + (text.length > 20 ? '...' : ''))
  }).catch(() => {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success('已复制')
  })
}

onMounted(async () => {
  try {
    const [platRes, prodRes] = await Promise.all([getPlatforms(), getProducts()])
    platforms.value = platRes.platforms || []
    products.value = prodRes.products || []
    if (platforms.value.length) currentPlatform.value = platforms.value[0].key
    await loadTitles()
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.title-card-approved { border-left: 3px solid #67c23a; background: #f0f9eb; }
.title-card-rejected { border-left: 3px solid #f56c6c; opacity: 0.7; }
</style>

