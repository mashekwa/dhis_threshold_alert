<template>
  <div>
    <h1>Home Page</h1>
    <ProvinceTable />
  </div>
</template>

<script>
import ProvinceTable from '@/components/ProvinceTable.vue';

export default {
  name: 'HomePage',
  components: {
    ProvinceTable
  }
};
</script>
