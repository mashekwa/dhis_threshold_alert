<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="flex items-center gap-4 mb-6">
      <button
        @click="$router.push('/')"
        class="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg shadow inline-flex items-center gap-2"
      >
        <span>←</span> Back
      </button>
      <h1 class="text-xl font-semibold">{{ $route.params.province }} Province Districts</h1>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b">
            <th class="text-left p-4 font-medium">District</th>
            <th class="text-right p-4 font-medium">New</th>
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
            <td class="text-right p-4">{{ district.newAlerts }}</td>
            <td class="text-right p-4 border-l">{{ district.verified }}</td>
            <td class="text-right p-4 bg-red-50">{{ district.pending }}</td>
            <td class="text-right p-4">{{ district.discarded }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const districts = ref([]);

const fetchDistricts = async (province) => {
  try {
    const response = await fetch(`http://localhost:8001/api/province/${province}/districts`);
    districts.value = await response.json();
  } catch (error) {
    console.error('Error fetching district data:', error);
  }
};

onMounted(() => fetchDistricts(route.params.province));

watch(() => route.params.province, (newProvince) => {
  fetchDistricts(newProvince);
});
</script>

<style scoped>
.border-l {
  border-left-width: 1px;
  border-left-color: #e5e7eb;
}
</style>