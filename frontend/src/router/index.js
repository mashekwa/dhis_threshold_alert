import { createRouter, createWebHistory } from 'vue-router';
import ProvinceView from '../components/ProvinceView.vue';
import DistrictView from '../components/DistrictView.vue';

const routes = [
  { path: '/', component: ProvinceView },
  { path: '/districts/:province', name: 'districts', component: DistrictView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;