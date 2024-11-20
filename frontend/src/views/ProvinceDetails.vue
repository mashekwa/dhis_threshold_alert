<template>
    <div>
      <h1>{{ province.name }} Details</h1>
      <p>Population: {{ province.population }}</p>
      <DistrictTable :provinceId="province.id" />
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from 'vue';
  import api from '@/services/api';
  import DistrictTable from '@/components/DistrictTable.vue';
  
  export default {
    name: 'ProvinceDetails',
    components: {
      DistrictTable
    },
    props: {
      id: {
        type: String,
        required: true
      }
    },
    setup(props) {
      const province = ref({});
  
      const fetchProvinceDetails = async () => {
        try {
          const response = await api.getProvinceDetails(props.id);
          province.value = response.data;
        } catch (error) {
          console.error('Failed to load province details', error);
        }
      };
  
      onMounted(() => {
        fetchProvinceDetails();
      });
  
      return {
        province
      };
    }
  };
  </script>
  