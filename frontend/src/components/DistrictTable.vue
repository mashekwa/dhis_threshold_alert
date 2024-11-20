<template>
    <div>
      <h2>Districts in {{ provinceName }}</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Population</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="district in districts" :key="district.id">
            <td>{{ district.name }}</td>
            <td>{{ district.population }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch } from 'vue';
  import api from '@/services/api';
  
  export default {
    name: 'DistrictTable',
    props: {
      provinceId: {
        type: String,
        required: true
      }
    },
    setup(props) {
      const districts = ref([]);
      const provinceName = ref('');
  
      const fetchDistricts = async () => {
        try {
          const response = await api.getDistricts(props.provinceId);
          districts.value = response.data.districts;
          provinceName.value = response.data.name;
        } catch (error) {
          console.error('Failed to load districts', error);
        }
      };
  
      watch(() => props.provinceId, fetchDistricts, { immediate: true });
  
      return {
        districts,
        provinceName
      };
    }
  };
  </script>
  