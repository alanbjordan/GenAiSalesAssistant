// src/App.js
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Chat from './components/Chat';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#61dafb', // Grok-like accent color
    },
    background: {
      default: '#151515',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#e0e0e0',
      secondary: '#a0a0a0',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <div className="App">
        <Chat />
      </div>
    </ThemeProvider>
  );
}

export default App;