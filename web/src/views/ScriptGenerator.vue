<template>
  <div class="sg-root">
    <!-- 头部操作区 -->
    <div class="sg-header">
      <div class="sg-header-left">
        <h2 class="sg-page-title">脚本生成</h2>
        <button class="sg-btn sg-btn-primary" :disabled="genLoading" @click="generateOne">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {{ genLoading ? '生成中…' : '生成3个不同脚本' }}
        </button>
      </div>
      <div class="sg-header-right">
        <div class="sg-segmented">
          <button :class="['sg-seg-item', { active: filterStatus === '' }]" @click="filterStatus = ''; loadScripts()">全部</button>
          <button :class="['sg-seg-item', { active: filterStatus === 'pending' }]" @click="filterStatus = 'pending'; loadScripts()">待审核</button>
          <button :class="['sg-seg-item', { active: filterStatus === 'approved' }]" @click="filterStatus = 'approved'; loadScripts()">已通过</button>
          <button :class="['sg-seg-item', { active: filterStatus === 'rejected' }]" @click="filterStatus = 'rejected'; loadScripts()">已拒绝</button>
        </div>
      </div>
    </div>

    <!-- 脚本列表 -->
    <div class="sg-list" v-if="scripts.length">
      <div v-for="s in scripts" :key="s.id" class="sg-card" :class="'sg-card-' + s.review_status">
        <!-- 头部 -->
        <div class="sg-card-header">
          <div class="sg-card-header-left">
            <span :class="['sg-pill', tagPill(s.script_type)]">{{ s.script_type }}</span>
            <span class="sg-pill sg-pill-green" v-if="s.hook_type">{{ s.hook_type }}</span>
            <span class="sg-meta-text">v{{ s.prompt_version }} · {{ s.generated_at?.substring(0,10) }}</span>
          </div>
          <div class="sg-card-header-right">
            <span :class="['sg-status-pill', 'sg-status-' + s.review_status]">
              <span class="sg-dot" :class="'sg-dot-' + s.review_status"></span>
              {{ statusLabel(s.review_status) }}
            </span>
          </div>
        </div>
        <div class="sg-divider"></div>

        <!-- 参考素材行 -->
        <div class="sg-ref" v-if="s.video_name">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          {{ s.video_name }} · {{ s.product_name }}
          <!-- 制作标签下拉 -->
          <span style="margin-left:auto;display:flex;align-items:center;gap:6px;">
            <span class="sg-meta-text">制作:</span>
            <select class="sg-select-mini" :value="s.production_tag" @change="(e) => updateTag(s.id, e.target.value)">
              <option value="">选择标签</option>
              <option value="AI完全生成">AI完全生成</option>
              <option value="真人+绿幕(低成本)">真人+绿幕(低成本)</option>
              <option value="真人+绿幕(高成本)">真人+绿幕(高成本)</option>
              <option value="真人+绿幕(模拟真实场景)">真人+绿幕(模拟真实场景)</option>
            </select>
          </span>
        </div>

        <!-- 脚本文本阅读区 -->
        <div class="sg-script-body">
          <div class="sg-script-text">{{ s.script_text }}</div>
        </div>

        <!-- 核心卖点 -->
        <div class="sg-focus" v-if="s.focus_point">
          <span class="sg-focus-label">核心卖点</span>
          <span class="sg-focus-text">{{ s.focus_point }}</span>
        </div>

        <!-- 底部操作栏 -->
        <div class="sg-card-footer">
          <button :class="['sg-btn sg-btn-sm', s.review_status === 'approved' ? 'sg-btn-green' : 'sg-btn-outline']" :disabled="s.review_status === 'approved'" @click="review(s.id, 'approved')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            通过
          </button>
          <button :class="['sg-btn sg-btn-sm', s.review_status === 'rejected' ? 'sg-btn-red' : 'sg-btn-outline']" :disabled="s.review_status === 'rejected'" @click="review(s.id, 'rejected')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            拒绝
          </button>
          <input class="sg-note-input" v-model="reviewNotes[s.id]" placeholder="编导备注（可选）" />
          <button class="sg-btn sg-btn-sm sg-btn-ghost" @click="copyScript(s.script_text)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            复制
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="sg-empty" v-else>
      <div class="sg-empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d0d5dd" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      </div>
      <div class="sg-empty-title">暂无生成脚本</div>
      <div class="sg-empty-desc">点击下方按钮，AI将基于视频数据生成3个不同角度的脚本</div>
      <button class="sg-btn sg-btn-primary sg-btn-lg" @click="generateOne">开始生成</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { generateScript, getScripts, reviewScript, updateScriptTag } from '../api'

const scripts = ref([])
const genLoading = ref(false)
const filterStatus = ref('')
const reviewNotes = ref({})

function tagPill(t) {
  if (!t) return ''
  if (t.includes('痛点')) return 'sg-pill-red'
  if (t.includes('场景')) return 'sg-pill-green'
  if (t.includes('价格')) return 'sg-pill-orange'
  if (t.includes('专家') || t.includes('口播') || t.includes('数据') || t.includes('权威')) return 'sg-pill-blue'
  return 'sg-pill-gray'
}
function statusLabel(s) { return { pending: '待审核', approved: '已通过', rejected: '已拒绝' }[s] || s }

async function loadScripts() {
  try {
    const data = await getScripts(filterStatus.value, 50)
    scripts.value = data.scripts || []
  } catch (e) { console.error(e) }
}

async function generateOne() {
  genLoading.value = true
  try {
    const res = await generateScript()
    if (res.scripts?.length) scripts.value = [...res.scripts, ...scripts.value]
  } catch (e) { console.error(e) }
  genLoading.value = false
}

async function review(id, action) {
  try {
    await reviewScript(id, action, reviewNotes.value[id] || '')
    reviewNotes.value[id] = ''
    await loadScripts()
  } catch (e) { console.error(e) }
}

async function updateTag(id, tag) {
  if (!tag) return
  try {
    await updateScriptTag(id, tag)
    ElMessage.success('标签已更新')
  } catch (e) { ElMessage.error('更新失败'); await loadScripts() }
}

function copyScript(text) {
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制'))
    .catch(() => {
      const ta = document.createElement('textarea')
      ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta)
      ElMessage.success('已复制')
    })
}

onMounted(loadScripts)
</script>

<style scoped>
/* ===== 全局变量 ===== */
.sg-root {
  --sg-bg: #F4F5F7;
  --sg-card-bg: #FFFFFF;
  --sg-text: #1A1A2E;
  --sg-text-secondary: #5F6368;
  --sg-text-muted: #9CA3AF;
  --sg-border: #E5E7EB;
  --sg-blue: #3B82F6;
  --sg-green: #10B981;
  --sg-red: #EF4444;
  --sg-orange: #F59E0B;
  --sg-shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --sg-shadow-hover: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--sg-text);
}

/* ===== 头部 ===== */
.sg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}
.sg-header-left { display: flex; align-items: center; gap: 16px; }
.sg-header-right { display: flex; align-items: center; gap: 12px; }
.sg-page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.3px;
  color: var(--sg-text);
}

/* ===== 分段胶囊 ===== */
.sg-segmented {
  display: inline-flex;
  background: #E8EAED;
  border-radius: 6px;
  padding: 3px;
  gap: 2px;
}
.sg-seg-item {
  border: none;
  background: transparent;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--sg-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.sg-seg-item.active {
  background: #FFFFFF;
  color: var(--sg-text);
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.sg-seg-item:hover:not(.active) { color: var(--sg-text); }

/* ===== 按钮 ===== */
.sg-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
  font-size: 13px;
  padding: 8px 16px;
}
.sg-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sg-btn-primary {
  background: var(--sg-blue);
  color: #fff;
  box-shadow: 0 1px 2px rgba(59,130,246,.3);
}
.sg-btn-primary:hover:not(:disabled) { background: #2563EB; box-shadow: 0 2px 8px rgba(59,130,246,.4); }
.sg-btn-lg { padding: 10px 24px; font-size: 14px; }
.sg-btn-sm { padding: 6px 12px; font-size: 12px; }
.sg-btn-outline {
  background: #fff;
  color: var(--sg-text-secondary);
  border: 1px solid var(--sg-border);
}
.sg-btn-outline:hover:not(:disabled) { border-color: #d0d5dd; background: #F9FAFB; color: var(--sg-text); }
.sg-btn-green { background: #D1FAE5; color: #065F46; }
.sg-btn-green:hover:not(:disabled) { background: #A7F3D0; }
.sg-btn-red { background: #FEE2E2; color: #991B1B; }
.sg-btn-red:hover:not(:disabled) { background: #FECACA; }
.sg-btn-ghost { background: transparent; color: var(--sg-text-muted); }
.sg-btn-ghost:hover { background: #F3F4F6; color: var(--sg-text-secondary); }

/* ===== 卡片 ===== */
.sg-list { display: flex; flex-direction: column; gap: 20px; }
.sg-card {
  background: var(--sg-card-bg);
  border-radius: 8px;
  box-shadow: var(--sg-shadow);
  transition: box-shadow 0.15s, transform 0.15s;
}
.sg-card:hover { box-shadow: var(--sg-shadow-hover); }
.sg-card-approved { border-left: 3px solid var(--sg-green); }
.sg-card-rejected { border-left: 3px solid var(--sg-red); opacity: 0.85; }

/* 卡片头部 */
.sg-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 18px 14px;
}
.sg-card-header-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sg-card-header-right { flex-shrink: 0; }
.sg-meta-text { font-size: 12px; color: var(--sg-text-muted); white-space: nowrap; }

/* 分割线 */
.sg-divider { height: 1px; background: var(--sg-border); margin: 0 18px; }

/* 参考素材行 */
.sg-ref {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  font-size: 12px;
  color: var(--sg-text-muted);
}
.sg-select-mini {
  border: 1px solid var(--sg-border);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  color: var(--sg-text-secondary);
  background: #fff;
  outline: none;
  font-family: inherit;
}

/* 脚本文本阅读区 */
.sg-script-body {
  padding: 14px 18px;
}
.sg-script-text {
  background: #F8FAFC;
  border-radius: 6px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: var(--sg-text);
}

/* 核心卖点 */
.sg-focus {
  padding: 0 18px 14px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.sg-focus-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--sg-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sg-focus-text { font-size: 13px; color: var(--sg-text); }

/* 底部操作栏 */
.sg-card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px 18px;
  border-top: 1px solid var(--sg-border);
}
.sg-note-input {
  flex: 1;
  border: 1px solid var(--sg-border);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
  background: #fff;
  color: var(--sg-text);
  min-width: 0;
}
.sg-note-input:focus { border-color: var(--sg-blue); box-shadow: 0 0 0 2px rgba(59,130,246,.15); }
.sg-note-input::placeholder { color: var(--sg-text-muted); }

/* ===== 药丸标签 ===== */
.sg-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.sg-pill::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.sg-pill-red { background: #FEE2E2; color: #991B1B; }
.sg-pill-red::before { background: #EF4444; }
.sg-pill-green { background: #D1FAE5; color: #065F46; }
.sg-pill-green::before { background: #10B981; }
.sg-pill-orange { background: #FEF3C7; color: #92400E; }
.sg-pill-orange::before { background: #F59E0B; }
.sg-pill-blue { background: #DBEAFE; color: #1E40AF; }
.sg-pill-blue::before { background: #3B82F6; }
.sg-pill-gray { background: #F3F4F6; color: #4B5563; }
.sg-pill-gray::before { background: #9CA3AF; }

/* 状态药丸 */
.sg-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.sg-dot { width: 6px; height: 6px; border-radius: 50%; }
.sg-status-pending { background: #F3F4F6; color: #6B7280; }
.sg-dot-pending { background: #9CA3AF; }
.sg-status-approved { background: #D1FAE5; color: #065F46; }
.sg-dot-approved { background: #10B981; }
.sg-status-rejected { background: #FEE2E2; color: #991B1B; }
.sg-dot-rejected { background: #EF4444; }

/* ===== 空状态 ===== */
.sg-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}
.sg-empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  background: #F8FAFC;
  border: 1px solid var(--sg-border);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.sg-empty-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
.sg-empty-desc { font-size: 13px; color: var(--sg-text-secondary); margin-bottom: 20px; max-width: 360px; line-height: 1.5; }

/* ===== 动画 ===== */
.sg-card { animation: sgFadeIn 0.2s ease; }
@keyframes sgFadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>

