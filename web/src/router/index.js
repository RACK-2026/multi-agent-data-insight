import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import VideoList from '../views/VideoList.vue'
import VideoDetail from '../views/VideoDetail.vue'
import PromptManager from '../views/PromptManager.vue'
import AgentMonitor from '../views/AgentMonitor.vue'
import ReviewReport from '../views/ReviewReport.vue'
import Optimization from '../views/Optimization.vue'
import ScriptGenerator from '../views/ScriptGenerator.vue'
import ScriptImport from '../views/ScriptImport.vue'
import TitleGenerator from '../views/TitleGenerator.vue'
import CreativeWorkshop from '../views/CreativeWorkshop.vue'
import ProductManage from '../views/ProductManage.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { title: '数据看板' } },
  { path: '/videos', name: 'VideoList', component: VideoList, meta: { title: '视频分析' } },
  { path: '/videos/:id', name: 'VideoDetail', component: VideoDetail, meta: { title: '视频详情' } },
  { path: '/prompts', name: 'PromptManager', component: PromptManager, meta: { title: '提示词管理' } },
  { path: '/agents', name: 'AgentMonitor', component: AgentMonitor, meta: { title: 'Agent监控' } },
  { path: '/review', name: 'ReviewReport', component: ReviewReport, meta: { title: '复盘报告' } },
  { path: '/optimization', name: 'Optimization', component: Optimization, meta: { title: '优化建议' } },
  { path: '/scripts', name: 'ScriptGenerator', component: ScriptGenerator, meta: { title: '脚本生成' } },
  { path: '/import', name: 'ScriptImport', component: ScriptImport, meta: { title: '脚本导入' } },
  { path: '/titles', name: 'TitleGenerator', component: TitleGenerator, meta: { title: '标题生成' } },
  { path: '/workshop', name: 'CreativeWorkshop', component: CreativeWorkshop, meta: { title: '奇思妙想创意工坊' } },
  { path: '/products', name: 'ProductManage', component: ProductManage, meta: { title: '产品管理' } },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})

