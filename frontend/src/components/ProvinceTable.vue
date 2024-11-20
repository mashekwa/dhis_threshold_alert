<template>
    <div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div class="max-w-7xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">New alerts generated in week 30</h1>
        
        <div class="flex flex-col lg:flex-row bg-white rounded-lg shadow overflow-hidden">
          <!-- Map Section -->
          <div class="lg:w-1/2 p-4">
            <div class="bg-gray-200 rounded-lg overflow-hidden h-full min-h-[300px] lg:min-h-[600px]">
              <!-- Placeholder map for Zambia; replace with dynamic map if needed -->
              <img 
                src="/zambia-map-placeholder.svg?height=600&width=600" 
                alt="Map of Zambia showing alert regions" 
                class="w-full h-full object-cover"
              />
            </div>
          </div>
  
          <!-- Table Section -->
          <div class="lg:w-1/2 overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th 
                    v-for="header in headers" 
                    :key="header.key"
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    @click="sortBy(header.key)"
                  >
                    {{ header.label }}
                    <span v-if="sortKey === header.key" class="ml-1">
                      {{ sortOrder === 'asc' ? '↑' : '↓' }}
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr 
                  v-for="region in sortedData" 
                  :key="region.name"
                  class="hover:bg-gray-50"
                >
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ region.name }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ region.newAlerts }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ region.verified }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span 
                      class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="region.pending > 5 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'"
                    >
                      {{ region.pending }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ region.discarded }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div class="bg-gray-50 px-6 py-4">
              <div class="text-sm text-gray-500">
                Total Alerts: {{ totalAlerts }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  
  // Headers for the table, removing the 'Substantiated' field
  const headers = [
    { key: 'name', label: 'Region' },
    { key: 'newAlerts', label: 'New Alerts' },
    { key: 'verified', label: 'Verified' },
    { key: 'pending', label: 'Pending' },
    { key: 'discarded', label: 'Discarded' }
  ]
  
  // Dummy data will be replaced with real API response
  const alertData = ref([])
  
  // Fetch data from the API endpoint
  async function fetchProvinces() {
    try {
      const response = await fetch('/api/provinces') // Replace with your actual API endpoint
      if (response.ok) {
        alertData.value = await response.json()
      } else {
        console.error('Failed to fetch provinces data')
      }
    } catch (error) {
      console.error('Error fetching provinces data:', error)
    }
  }
  
  // Fetch data on component mount
  fetchProvinces()
  
  // Sorting functionality
  const sortKey = ref('name')
  const sortOrder = ref('asc')
  
  const sortBy = (key) => {
    if (sortKey.value === key) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKey.value = key
      sortOrder.value = 'asc'
    }
  }
  
  const sortedData = computed(() => {
    return [...alertData.value].sort((a, b) => {
      const aValue = a[sortKey.value]
      const bValue = b[sortKey.value]
      
      if (sortOrder.value === 'asc') {
        return aValue > bValue ? 1 : -1
      }
      return aValue < bValue ? 1 : -1
    })
  })
  
  // Compute total alerts based on newAlerts only
  const totalAlerts = computed(() => {
    return alertData.value.reduce((sum, region) => sum + region.newAlerts, 0)
  })
  </script>
  