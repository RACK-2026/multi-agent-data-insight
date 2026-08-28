<template>
  <div style="display:flex;gap:16px;height:calc(100vh - 120px);">
    <!-- 左栏：产品列表+上传 -->
    <div style="width:340px;flex-shrink:0;display:flex;flex-direction:column;gap:12px;">
      <el-card shadow="hover" :body-style="{padding:'14px'}">
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <el-upload :auto-upload="false" :show-file-list="false" accept=".txt,.csv,.xlsx,.xls,.pdf,.jpg,.jpeg,.png" @change="handleUpload">
            <el-button size="small" type="primary">📤 上传文件</el-button>
          </el-upload>
          <el-button size="small" @click="showFeishuInput = !showFeishuInput">🔗 飞书链接</el-button>
          <el-button size="small" @click="showManualInput = !showManualInput">✏️ 手动添加</el-button>
        </div>
        <div v-if="showFeishuInput" style="margin-top:8px;display:flex;gap:8px;">
          <el-input v-model="feishuUrl" placeholder="飞书Bitable链接" size="small" />
          <el-input v-model="feishuName" placeholder="产品名" size="small" style="width:100px;" />
          <el-button size="small" type="primary" :loading="flLoading" @click="importFeishu">导入</el-button>
        </div>
        <div v-if="showManualInput" style="margin-top:8px;">
          <el-input v-model="manualName" placeholder="产品名称" size="small" style="margin-bottom:4px;" />
          <el-input v-model="manualDetails" placeholder="产品详情（选填）" size="small" type="textarea" :rows="2" style="margin-bottom:4px;" />
          <el-input v-model="manualTags" placeholder="标签（逗号分隔）" size="small" style="margin-bottom:4px;" />
          <el-button size="small" type="primary" @click="addManual">添加</el-button>
        </div>
      </el-card>

      <el-card shadow="hover" :body-style="{padding:'0'}" style="flex:1;overflow:auto;">
        <div v-for="p in products" :key="p.id" :class="['product-item', selectedId === p.id ? 'product-active' : '']" @click="selectProduct(p.id)">
          <div style="font-weight:600;font-size:13px;">{{ p.name }}</div>
          <div style="font-size:11px;color:#909399;margin-top:2px;">
            <el-tag v-for="t in (p.tags||[]).slice(0,3)" :key="t" size="small" style="margin:1px;">{{ t }}</el-tag>
          </div>
          <div style="font-size:11px;color:#909399;margin-top:2px;">{{ p.source_type }} · {{ p.created_at?.substring(0,10) }}</div>
        </div>
        <el-empty v-if="!products.length" description="暂无产品，请上传" :image-size="60" style="padding:40px 0;" />
      </el-card>
    </div>

    <!-- 右栏：产品详情 -->
    <div style="flex:1;overflow:auto;">
      <el-card shadow="hover" v-if="detail">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <strong style="font-size:16px;">{{ detail.name }}</strong>
              <el-tag size="small" style="margin-left:8px;">{{ detail.source_type }}</el-tag>
            </div>
            <div style="display:flex;gap:8px;">
              <el-button size="small" type="primary" :loading="tagLoading" @click="generateTags">🎯 生成标签</el-button>
              <el-button size="small" type="danger" @click="removeProduct">删除</el-button>
            </div>
          </div>
        </template>
        <div style="margin-bottom:12px;">
          <div style="font-size:12px;color:#909399;margin-bottom:4px;">产品详情</div>
          <div style="font-size:13px;line-height:1.7;white-space:pre-wrap;background:#f8fafc;padding:12px;border-radius:6px;">{{ detail.details || '暂无详情' }}</div>
        </div>
        <div v-if="detail.tags?.length">
          <div style="font-size:12px;color:#909399;margin-bottom:4px;">产品标签</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px;">
            <el-tag v-for="t in detail.tags" :key="t" size="medium" effect="plain" style="font-size:13px;">{{ t }}</el-tag>
          </div>
        </div>
        <div style="margin-top:12px;font-size:11px;color:#909399;">
          来源: {{ detail.source_name || detail.source_type }} · {{ detail.created_at }}
        </div>
      </el-card>
      <el-empty v-else description="选择一个产品查看详情" style="margin-top:60px;" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProducts, getProductDetail, uploadProductFile, generateProductTags, deleteProduct } from '../api'
import axios from 'axios'

const products = ref([])
const detail = ref(null)
const selectedId = ref(0)
const tagLoading = ref(false)
const showFeishuInput = ref(false)
const showManualInput = ref(false)
const feishuUrl = ref('')
const feishuName = ref('')
const flLoading = ref(false)
const manualName = ref('')
const manualDetails = ref('')
const manualTags = ref('')

async function loadList() {
  try {
    const data = await getProducts()
    products.value = data.products || []
    if (selectedId.value && !products.value.find(p => p.id === selectedId.value)) {
      detail.value = null
    }
  } catch (e) { console.error(e) }
}

async function selectProduct(id) {
  selectedId.value = id
  try {
    detail.value = await getProductDetail(id)
  } catch (e) { ElMessage.error('加载失败'); detail.value = null }
}

async function handleUpload(uploadFile) {
  const form = new FormData()
  form.append('file', uploadFile.raw || uploadFile.file)
  try {
    const res = await uploadProductFile(form)
    ElMessage.success(res.message || '上传成功')
    await loadList()
    if (res.id) await selectProduct(res.id)
  } catch (e) {
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function importFeishu() {
  if (!feishuUrl.value) return
  flLoading.value = true
  try {
    const res = await axios.post('/api/products/feishu', { url: feishuUrl.value, product_name: feishuName.value })
    ElMessage.success('导入成功')
    feishuUrl.value = ''; feishuName.value = ''
    await loadList()
  } catch (e) { ElMessage.error('导入失败') }
  flLoading.value = false
}

async function addManual() {
  if (!manualName.value) return
  try {
    const form = new FormData()
    form.append('name', manualName.value)
    form.append('details', manualDetails.value)
    form.append('tags', manualTags.value)
    await axios.post('/api/products/manual', form)
    manualName.value = ''; manualDetails.value = ''; manualTags.value = ''
    ElMessage.success('已添加')
    await loadList()
  } catch (e) { ElMessage.error('添加失败') }
}

async function generateTags() {
  if (!selectedId.value) return
  tagLoading.value = true
  try {
    const res = await generateProductTags(selectedId.value)
    ElMessage.success('标签已生成')
    detail.value.tags = res.tags
    await loadList()
  } catch (e) { ElMessage.error('生成失败') }
  tagLoading.value = false
}

async function removeProduct() {
  if (!selectedId.value || !confirm('确认删除？')) return
  try {
    await deleteProduct(selectedId.value)
    selectedId.value = 0; detail.value = null
    await loadList()
  } catch (e) { ElMessage.error('删除失败') }
}

onMounted(loadList)
</script>

<style scoped>
.product-item { padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #f0f0f0; transition: all 0.2s; }
.product-item:hover { background: #f8fafc; }
.product-active { background: #ecf5ff; border-left: 3px solid #1a73e8; }
</style>

