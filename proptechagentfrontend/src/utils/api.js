// src/utils/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000', // Your backend URL
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export default api;
