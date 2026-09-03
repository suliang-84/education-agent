import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/dashboard/DashboardView.vue'),
          meta: { title: '数据看板', breadcrumb: ['数据看板'] },
        },
        {
          path: 'questions',
          name: 'Questions',
          component: () => import('../views/questions/QuestionListView.vue'),
          meta: { title: '题目列表', breadcrumb: ['题库管理', '题目列表'] },
        },
        {
          path: 'questions/create',
          name: 'QuestionCreate',
          component: () => import('../views/questions/QuestionFormView.vue'),
          meta: { title: '新增题目', breadcrumb: ['题库管理', '新增题目'] },
        },
        {
          path: 'questions/edit/:id',
          name: 'QuestionEdit',
          component: () => import('../views/questions/QuestionFormView.vue'),
          meta: { title: '编辑题目', breadcrumb: ['题库管理', '编辑题目'] },
        },
        {
          path: 'annotations',
          name: 'Annotations',
          component: () => import('../views/annotations/AnnotationView.vue'),
          meta: { title: 'AI标注审核', breadcrumb: ['AI标注审核'] },
        },
        {
          path: 'cognitive-test',
          name: 'CognitiveTest',
          component: () => import('../views/cognitive-test/CognitiveTestView.vue'),
          meta: { title: '五力测试题维护', breadcrumb: ['五力测试题维护'] },
        },
        {
          path: 'training-config',
          name: 'TrainingConfig',
          component: () => import('../views/training-config/TrainingConfigView.vue'),
          meta: { title: '训练配置管理', breadcrumb: ['训练配置管理'] },
        },
        {
          path: 'system-config',
          name: 'SystemConfig',
          component: () => import('../views/system-config/SystemConfigView.vue'),
          meta: { title: '系统参数配置', breadcrumb: ['系统参数配置'] },
        },
        {
          path: 'strategies',
          name: 'Strategies',
          component: () => import('../views/strategies/StrategiesView.vue'),
          meta: { title: '启发策略管理', breadcrumb: ['启发策略管理'] },
        },
        {
          path: 'students',
          name: 'Students',
          component: () => import('../views/students/StudentListView.vue'),
          meta: { title: '学生管理', breadcrumb: ['学生管理'] },
        },
        {
          path: 'students/:id',
          name: 'StudentDetail',
          component: () => import('../views/students/StudentDetailView.vue'),
          meta: { title: '学生详情', breadcrumb: ['学生管理', '学生详情'] },
        },
        {
          path: 'audit-logs',
          name: 'AuditLogs',
          component: () => import('../views/audit-logs/AuditLogView.vue'),
          meta: { title: '审计日志', breadcrumb: ['审计日志'] },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
