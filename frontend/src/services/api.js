import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

export default {
  getProvinces() {
    return apiClient.get('/province-summary');
  },
  getProvinceDetails(id) {
    return apiClient.get(`/provinces/${id}`);
  },
  getDistricts(provinceId) {
    return apiClient.get(`/provinces/${provinceId}/districts`);
  }
};
