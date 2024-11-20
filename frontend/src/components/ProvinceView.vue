<template>
    <div>
      <h2 class="text-2xl font-semibold mb-4">Provincial Summary</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="w-full text-sm">
          <thead class="text-xs uppercase">
            <tr class="border-b">
              <th class="text-left p-4 font-medium">Province</th>
              <th class="text-right p-4 font-medium">New alerts</th>
              <th class="text-right p-4 font-medium border-l">Verified</th>
              <th class="text-right p-4 font-medium bg-red-50">Pending</th>
              <th class="text-right p-4 font-medium">Discarded</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="province in provinces"
                :key="province.name"
                :class="{'bg-gray-50': index % 2 === 0}"
                @click="showDistricts(province.name)"
            >
              <td class="p-1">{{ province.name }}</td>
              <td class="text-right p-2">{{ province.newAlerts }}</td>
              <td class="text-right p-2 border-l">{{ province.verified }}</td>
              <td class="text-right p-2 bg-red-50">{{ province.pending }}</td>
              <td class="text-right p-2">{{ province.discarded }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  
  const router = useRouter();
  const provinces = ref([]);
  
  const fetchProvinces = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/province-summary');
      provinces.value = await response.json();
    } catch (error) {
      console.error('Error fetching province data:', error);
    }
  };
  
  const showDistricts = (provinceName) => {
    router.push({ name: 'districts', params: { province: provinceName } });
  };
  
  onMounted(fetchProvinces);
  </script>