import { createRouter, createWebHistory } from 'vue-router'
import { TOKEN_KEY } from '@/utils/constants'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AdminLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '数据看板' },
        },
        {
          path: 'questions',
          name: 'QuestionList',
          component: () => import('@/views/questions/QuestionListView.vue'),
          meta: { title: '题库管理' },
        },
        {
          path: 'questions/create',
          name: 'QuestionCreate',
          component: () => import('@/views/questions/QuestionFormView.vue'),
          meta: { title: '录入题干' },
        },
        {
          path: 'questions/:id/edit',
          name: 'QuestionEdit',
          component: () => import('@/views/questions/QuestionFormView.vue'),
          meta: { title: '编辑题干' },
        },
        {
          path: 'questions/:id/review',
          name: 'QuestionReview',
          component: () => import('@/views/questions/QuestionReviewView.vue'),
          meta: { title: '审核分析结果' },
        },
        {
          path: 'cognitive-test',
          name: 'CognitiveTest',
          component: () => import('@/views/cognitive-test/CognitiveTestView.vue'),
          meta: { title: '五力测试题维护' },
        },
        {
          path: 'cognitive-test/create',
          name: 'CognitiveCreate',
          component: () => import('@/views/cognitive-test/CognitiveFormView.vue'),
          meta: { title: '新增测试题目' },
        },
        {
          path: 'cognitive-test/:id/edit',
          name: 'CognitiveEdit',
          component: () => import('@/views/cognitive-test/CognitiveFormView.vue'),
          meta: { title: '编辑测试题目' },
        },
        {
          path: 'training-config',
          name: 'TrainingConfig',
          component: () => import('@/views/training-config/TrainingConfigView.vue'),
          meta: { title: '训练配置管理' },
        },
        {
          path: 'system-config',
          name: 'SystemConfig',
          component: () => import('@/views/system-config/SystemConfigView.vue'),
          meta: { title: '系统参数配置' },
        },
        {
          path: 'students',
          name: 'StudentList',
          component: () => import('@/views/students/StudentListView.vue'),
          meta: { title: '学生管理' },
        },
        {
          path: 'students/:id',
          name: 'StudentDetail',
          component: () => import('@/views/students/StudentDetailView.vue'),
          meta: { title: '学生详情' },
        },
        {
          path: 'audit-logs',
          name: 'AuditLogs',
          component: () => import('@/views/audit-logs/AuditLogView.vue'),
          meta: { title: '审计日志' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (!to.meta.public && !token) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && token) {
    return { path: '/' }
  }
})

export default router
