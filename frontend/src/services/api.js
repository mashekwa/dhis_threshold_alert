import axios from 'axios';

// Base URL for the API
const baseURL = 'http://localhost:8001/api';

// Create an Axios instance
const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Fetch the list of provinces
export const fetchProvinces = async () => {
  try {
    const response = await apiClient.get('/province-summary');
    return response.data;
  } catch (error) {
    console.error('Error fetching province data:', error);
    throw error;
  }
};

// Fetch the list of districts for a specific province
export const fetchDistricts = async (province) => {
  try {
    const response = await apiClient.get(`/province/${province}/districts`);
    return response.data;
  } catch (error) {
    console.error('Error fetching district data:', error);
    throw error;
  }
};
