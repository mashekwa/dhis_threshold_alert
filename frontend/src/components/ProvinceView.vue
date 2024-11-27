<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <h1 class="text-xl font-semibold mb-6">New alerts generated in week 30</h1>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Map Section -->
      <div class="bg-white rounded-lg shadow p-4">
        <!-- <img 
          src="/placeholder.svg?height=400&width=400" 
          alt="Province Map"
          class="w-full h-auto"
        /> -->
      </div>
      
      <!-- Data Table Section -->
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="text-left p-4 font-medium">Province</th>
              <th class="text-right p-4 font-medium">New alerts</th>
              <th colspan="2" class="text-center p-4 font-medium border-l">
                Under verification
              </th>
              <th colspan="2" class="text-center p-4 font-medium border-l">
                Verified
              </th>
            </tr>
            <tr class="bg-gray-50 text-sm">
              <th class="text-left p-4"></th>
              <th class="text-right p-4"></th>
              <th class="text-right p-4 border-l">Verified</th>
              <th class="text-right p-4 bg-red-50">Pending</th>
              <th class="text-right p-4 border-l">Substantiated</th>
              <th class="text-right p-4">Discarded</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(province, index) in provinces" 
                :key="province.name"
                :class="{'bg-gray-50': index % 2 === 0}"
                class="hover:bg-gray-100 transition-colors cursor-pointer"
                @click="showDistricts(province.name)"
            >
              <td class="p-4">{{ province.name }}</td>
              <td class="text-right p-4">{{ province.newAlerts }}</td>
              <td class="text-right p-4 border-l">{{ province.verified }}</td>
              <td class="text-right p-4 bg-red-50">{{ province.pending }}</td>
              <td class="text-right p-4 border-l">0</td>
              <td class="text-right p-4">{{ province.discarded }}</td>
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
    console.log(provinces)
  } catch (error) {
    console.error('Error fetching province data:', error);
  }
};

const showDistricts = (provinceName) => {
  router.push({ name: 'districts', params: { province: provinceName } });
};

onMounted(fetchProvinces);
</script>

<style scoped>
.border-l {
  border-left-width: 1px;
  border-left-color: #e5e7eb;
}
</style>