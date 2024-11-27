<template>
  <div class="flex">
    <MapView
      class="w-full md:w-1/3 mr-4"
      :geoData="districtGeoJsonData"
      :highlightFeatureId="selectedDistrictId"
      :alertInfo="districtAlertData"
      autoZoom
    />
    <div class="w-full md:w-2/3">
    <div>
      <div class="flex items-center gap-4 mb-6">
        <button
          @click="$router.push('/')"
          class="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-2 rounded-lg shadow inline-flex items-center gap-2"
        >
          <span>←</span> Back to Provinces
        </button>        
      </div>
      <h1 class="text-xl font-semibold">{{ $route.params.province }} Province Districts</h1>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="w-full text-sm">
          <thead class="text-xs uppercase">
            <tr class="border-b">
              <th class="text-left p-4 font-medium">District</th>
              <th class="text-right p-4 font-medium">New alerts</th>
              <th class="text-right p-4 font-medium border-l">Verified</th>
              <th class="text-right p-4 font-medium bg-red-50">Pending</th>
              <th class="text-right p-4 font-medium">Discarded</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(district, index) in districts" 
                :key="district.district_name"
                :class="{'bg-gray-50': index % 2 === 0}"
            >
              <td class="p-4">{{ district.district_name }}</td>
              <td class="text-right p-2">{{ district.newAlerts }}</td>
              <td class="text-right p-2 border-l bg-red-20">{{ district.verified }}</td>
              <td class="text-right p-2 bg-red-50">{{ district.pending }}</td>
              <td class="text-right p-2">{{ district.discarded }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>
  </div>
</div>
  </template>
  
  <script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { fetchDistricts } from '@/services/api';
import geoJsonData from '@/assets/data/gisData.geojson'; // Import GeoJSON data
import MapView from '@/components/MapView.vue';

const route = useRoute();
const districts = ref([]);
const districtAlertData = ref([]);
const selectedDistrictId = ref(null);

const fetchDistrictData = async () => {
  try {
    districts.value = await fetchDistricts(route.params.province);
    districtAlertData.value = districts.value.map(district => ({
      name: district.district_name,
      alerts: district.newAlerts,
      id: district.id,
    }));
  } catch (error) {
    console.error('Error fetching district data:', error);
  }
};

onMounted(fetchDistrictData);

watch(() => route.params.province, (newProvince) => {
  getDistricts(newProvince);
});
</script>

  
  <style scoped>
  .border-l {
    border-left-width: 1px;
    border-left-color: #e5e7eb;
  }
  </style>