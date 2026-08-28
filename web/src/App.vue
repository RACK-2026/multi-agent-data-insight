<template>
  <div id="app-container">
    <el-container style="height: 100vh;">
      <el-aside width="236px" class="app-sidebar">
        <div class="sidebar-header">
          <div class="sidebar-logo">QA</div>
          <div class="sidebar-title">千川Agent</div>
        </div>
        <div class="sidebar-menu">
          <div class="sidebar-group-label">数据监控</div>
          <router-link to="/dashboard" class="sidebar-item" :class="{ active: route.path === '/dashboard' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            <span>数据总看板</span>
          </router-link>
          <router-link to="/videos" class="sidebar-item" :class="{ active: route.path.startsWith('/videos') }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            <span>视频分析</span>
          </router-link>
          <router-link to="/scripts" class="sidebar-item" :class="{ active: route.path === '/scripts' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            <span>脚本生成</span>
          </router-link>
          <div class="sidebar-group-label" style="margin-top:20px;">内容创作</div>
          <router-link to="/titles" class="sidebar-item" :class="{ active: route.path === '/titles' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
            <span>标题生成</span>
          </router-link>
          <router-link to="/products" class="sidebar-item" :class="{ active: route.path === '/products' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
            <span>产品管理</span>
          </router-link>
          <router-link to="/workshop" class="sidebar-item" :class="{ active: route.path === '/workshop' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <span>创意工坊</span>
          </router-link>
          <div class="sidebar-group-label" style="margin-top:20px;">系统工具</div>
          <router-link to="/import" class="sidebar-item" :class="{ active: route.path === '/import' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>脚本导入</span>
          </router-link>
          <router-link to="/prompts" class="sidebar-item" :class="{ active: route.path === '/prompts' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            <span>提示词管理</span>
          </router-link>
          <router-link to="/agents" class="sidebar-item" :class="{ active: route.path === '/agents' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>Agent监控</span>
          </router-link>
          <router-link to="/review" class="sidebar-item" :class="{ active: route.path === '/review' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            <span>复盘报告</span>
          </router-link>
          <router-link to="/optimization" class="sidebar-item" :class="{ active: route.path === '/optimization' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            <span>优化建议</span>
          </router-link>
        </div>
        <!-- 使用说明按钮 - 放在侧栏底部 -->
        <a class="sidebar-help-btn" href="/manual.html" target="_blank" title="打开员工使用手册">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>📖 使用说明</span>
        </a>
      </el-aside>
      <el-container>
        <el-header class="app-header">
          <div style="display:flex;align-items:center;gap:12px;">
            <h3 class="page-title">{{ route.meta?.title || '千川数据多Agent分析平台' }}</h3>
            <a href="/manual.html" target="_blank" class="header-help-btn" title="打开员工使用手册">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              使用说明
            </a>
          </div>
          <div class="header-status">
            <div class="status-item">
              <span class="status-dot" :class="health.feishu === 'connected' ? 'status-ok' : 'status-warn'"></span>
              <span>飞书{{ health.feishu === 'connected' ? '已连接' : '未连接' }}</span>
            </div>
            <div class="status-item">
              <span class="status-dot" :class="health.llm === 'configured' ? 'status-ok' : 'status-warn'"></span>
              <span>{{ health.llm === 'configured' ? 'LLM就绪' : 'LLM未配置' }}</span>
            </div>
          </div>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getHealth } from './api'

const route = useRoute()
const health = ref({ feishu: 'unknown', llm: 'unknown' })

onMounted(async () => {
  try {
    health.value = await getHealth()
  } catch (e) {
    health.value = { feishu: 'error', llm: 'error' }
  }
})
</script>

<style>
:root {
  --color-bg: #F4F5F7;
  --color-text: #1A1A2E;
  --color-text-secondary: #5F6368;
  --color-text-muted: #9CA3AF;
  --color-border: #E5E7EB;
  --font-display: 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', -apple-system, sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
}

/* ===== 侧栏 ===== */
.app-sidebar {
  background: #1A2436 !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  padding: 18px 18px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.sidebar-logo {
  width: 30px; height: 30px;
  border-radius: 6px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-family: var(--font-display);
}
.sidebar-title { color: #e8edf5; font-size: 14px; font-weight: 700; letter-spacing: 0.2px; }
.sidebar-menu { flex: 1; overflow-y: auto; padding: 10px 0; }
.sidebar-group-label {
  padding: 6px 18px;
  font-size: 10px;
  font-weight: 700;
  color: #6b7a99;
  text-transform: uppercase;
  letter-spacing: 1.2px;
}
.sidebar-item {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 18px; margin: 1px 0;
  font-size: 13px; font-weight: 500;
  color: #9aa8c0; text-decoration: none;
  transition: all 0.15s;
  border-left: 3px solid transparent;
}
.sidebar-item:hover { color: #e8edf5; background: rgba(255,255,255,0.04); }
.sidebar-item.active { color: #e8edf5; border-left-color: #3b82f6; background: rgba(59,130,246,0.08); }
.sidebar-item svg { flex-shrink: 0; opacity: 0.5; }
.sidebar-item.active svg { opacity: 1; }

/* ===== 侧栏底部使用说明按钮 ===== */
.sidebar-help-btn {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 18px; margin: 8px 10px 16px;
  background: linear-gradient(135deg, #3B82F6, #6366F1);
  border-radius: 8px;
  font-size: 14px; font-weight: 700; color: #fff;
  text-decoration: none; cursor: pointer;
  transition: all 0.15s; border: none;
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}
.sidebar-help-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59,130,246,0.4);
  background: linear-gradient(135deg, #2563EB, #4F46E5);
}
.sidebar-help-btn svg { flex-shrink: 0; opacity: 1; }

/* ===== 顶栏使用说明按钮 ===== */
.header-help-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 14px; border-radius: 20px;
  background: #EFF6FF; border: 1px solid #BFDBFE;
  font-size: 12px; font-weight: 600; color: #1E40AF;
  text-decoration: none; transition: all 0.15s;
}
.header-help-btn:hover {
  background: #DBEAFE; border-color: #93C5FD;
  transform: translateY(-1px);
}

/* ===== 顶栏 ===== */
.app-header {
  background: #fff !important;
  border-bottom: 1px solid var(--color-border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px !important; height: 50px !important;
}
.page-title { margin: 0; font-size: 15px; font-weight: 600; color: var(--color-text); }
.header-status { display: flex; align-items: center; gap: 8px; }
.status-item {
  display: flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  background: #F3F4F6; font-size: 11px; color: #6B7280; font-weight: 500;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.status-ok { background: #10B981; }
.status-warn { background: #F59E0B; }

/* ===== 主内容区 ===== */
.app-main {
  background: var(--color-bg);
  padding: 20px 24px;
  overflow-y: auto;
}

/* ===== Element Plus 轻量覆盖 ===== */
.el-card {
  border-radius: 8px !important;
  border: none !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04) !important;
  transition: box-shadow 0.15s, transform 0.15s;
}
.el-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04) !important; }
.el-table { border-radius: 6px; }
.el-table::before { display: none; }
.el-table th.el-table__cell { background: #F9FAFB !important; font-weight: 600; font-size: 12px; color: #6B7280; }
.el-button { border-radius: 6px; font-weight: 500; }
.el-button--primary { background: #3B82F6; border-color: #3B82F6; }
.el-button--primary:hover { background: #2563EB; }
.el-tag { border-radius: 20px; font-weight: 500; border: none; padding: 0 10px; }
.el-tag--success { background: #D1FAE5 !important; color: #065F46 !important; }
.el-tag--danger { background: #FEE2E2 !important; color: #991B1B !important; }
.el-tag--warning { background: #FEF3C7 !important; color: #92400E !important; }
.el-tag--primary { background: #DBEAFE !important; color: #1E40AF !important; }
.el-empty { padding: 40px 0; }
.el-dialog { border-radius: 12px !important; }
.el-tabs__item { font-size: 13px; font-weight: 500; }
.el-tabs__item.is-active { color: #3B82F6; }
.el-tabs__active-bar { background: #3B82F6; }

/* ===== 滚动条 ===== */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 2px; }
</style>

