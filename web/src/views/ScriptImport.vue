<template>
  <div class="script-import">
    <!-- 导入方式选择 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>上传文件导入</span></template>
          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".txt,.csv,.xlsx,.xls"
            :limit="1"
          >
            <el-icon style="font-size:48px;color:#409EFF;"><upload-filled /></el-icon>
            <div style="font-size:14px;color:#606266;margin-top:8px;">
              拖拽文件到此处，或点击选择文件
            </div>
            <template #tip>
              <div style="font-size:12px;color:#909399;margin-top:4px;">
                支持 TXT、CSV、Excel(.xlsx) 格式
              </div>
            </template>
          </el-upload>
          <div v-if="selectedFile" style="margin-top:12px;">
            <el-tag>{{ selectedFile.name }}</el-tag>
            <el-input v-model="fileDirector" placeholder="编导名称（可选）" size="small" style="width:200px;margin-left:8px;" />
            <el-button type="primary" size="small" :loading="uploading" @click="uploadFile" style="margin-left:8px;">
              {{ uploading ? '解析中...' : '开始导入' }}
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>飞书链接导入</span></template>
          <el-input
            v-model="feishuUrl"
            placeholder="输入飞书Bitable链接，例如: https://xxx.feishu.cn/base/xxx?table=tblxxx"
            style="margin-bottom:8px;"
          />
          <el-input v-model="feishuDirector" placeholder="编导名称（可选）" size="small" style="margin-bottom:8px;" />
          <el-button type="primary" :loading="feishuLoading" @click="importFeishu">
            {{ feishuLoading ? '读取中...' : '从飞书导入' }}
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导入结果提示 -->
    <el-alert
      v-if="importResult"
      :title="importResult"
      :type="importResult.includes('失败') ? 'error' : 'success'"
      show-icon
      closable
      style="margin-bottom: 16px;"
      @close="importResult = ''"
    />

    <!-- 已导入的参考脚本列表 -->
    <el-card shadow="hover">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>已导入的参考脚本 ({{ scripts.length }})</span>
          <div>
            <el-button size="small" @click="refreshList">刷新</el-button>
            <el-button size="small" type="warning" :loading="optLoading" @click="optimizeWithImported">
              使用这些脚本优化提示词
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="scripts" stripe v-loading="loading" style="width:100%">
        <el-table-column type="index" label="#" width="40" />
        <el-table-column prop="source" label="来源" width="80">
          <template #default="{ row }">
            <el-tag :type="sourceType(row.source)" size="small">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="script_type" label="类型" width="120" />
        <el-table-column prop="product_name" label="产品" width="100" />
        <el-table-column prop="director" label="编导" width="80" />
        <el-table-column prop="script_text" label="脚本内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="导入时间" width="140" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" text @click="deleteScript(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!scripts.length && !loading" description="暂无导入的脚本，请通过上方方式导入" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const selectedFile = ref(null)
const fileDirector = ref('')
const feishuUrl = ref('')
const feishuDirector = ref('')
const uploading = ref(false)
const feishuLoading = ref(false)
const optLoading = ref(false)
const importResult = ref('')
const scripts = ref([])
const loading = ref(false)

function sourceType(src) {
  return { feishu: 'primary', excel: 'success', csv: 'warning', txt: 'info' }[src] || 'default'
}

function handleFileChange(file) {
  selectedFile.value = file.raw || file
}

async function uploadFile() {
  if (!selectedFile.value) return
  uploading.value = true
  const form = new FormData()
  form.append('file', selectedFile.value)
  form.append('director', fileDirector.value)
  try {
    const res = await axios.post('/api/import/file', form)
    const d = res.data
    importResult.value = `导入成功：新增 ${d.imported || 0} 条（共 ${d.total || 0} 条）`
    await refreshList()
  } catch (e) {
    importResult.value = `导入失败：${e.response?.data?.detail || e.message}`
  }
  uploading.value = false
  selectedFile.value = null
}

async function importFeishu() {
  if (!feishuUrl.value) return
  feishuLoading.value = true
  try {
    const res = await axios.post('/api/import/feishu', {
      url: feishuUrl.value,
      director: feishuDirector.value,
    })
    const d = res.data
    importResult.value = `飞书导入成功：新增 ${d.imported || 0} 条（共 ${d.total || 0} 条）`
    await refreshList()
  } catch (e) {
    importResult.value = `飞书导入失败：${e.response?.data?.detail || e.message}`
  }
  feishuLoading.value = false
}

async function refreshList() {
  loading.value = true
  try {
    const res = await axios.get('/api/import/list?limit=100')
    scripts.value = res.data.scripts || []
  } catch (e) { console.error(e) }
  loading.value = false
}

async function deleteScript(id) {
  try {
    await axios.delete(`/api/import/${id}`)
    scripts.value = scripts.value.filter(s => s.id !== id)
  } catch (e) {
    console.error(e)
  }
}

async function optimizeWithImported() {
  optLoading.value = true
  try {
    const res = await axios.post('/api/import/optimize-prompt')
    const d = res.data
    if (d.status === 'optimized') {
      importResult.value = `提示词已优化！版本: ${d.version}，参考了 ${d.script_count} 条导入脚本`
    } else {
      importResult.value = '当前提示词无需优化'
    }
  } catch (e) {
    importResult.value = `优化失败：${e.response?.data?.detail || e.message}`
  }
  optLoading.value = false
}

onMounted(refreshList)
</script>

