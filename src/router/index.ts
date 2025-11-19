import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';
// 导入已有的页面组件
import Home from '@/views/Home.vue';


import ReviewPage from '@/views/ReviewPage.vue';
// 新增：导入FileManage组件
import FileManage from '@/views/FileManage.vue'; // 关键：导入新页面
// 新增：导入ChatPage组件
import ChatPage from '@/views/ChatPage.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '公平审查平台 - 首页' }
  },
  {
    path: '/review/:articleId',
    name: 'ReviewPage',
    component: ReviewPage,
    props: true,
    meta: { title: '文件审查详情' }
  },
  // 新增：注册FileManage页面的路由规则
  {
    path: '/file-manage', // 访问路径：http://localhost:5173/file-manage
    name: 'FileManage',
    component: FileManage,
    meta: { title: '文件管理' } // 页面标题
  },
  // 新增：注册ChatPage页面的路由规则
  {
    path: '/chat', // 访问路径：http://localhost:5173/chat
    name: 'ChatPage',
    component: ChatPage,
    meta: { title: 'AI 智能助手' } // 页面标题
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

router.beforeEach((to) => {
  if (to.meta.title) document.title = to.meta.title as string;
});

export default router;
