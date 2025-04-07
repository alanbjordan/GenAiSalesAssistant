// src/components/Chat.js
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Card,
  CardContent,
  Alert,
  CssBaseline,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import ReactMarkdown from 'react-markdown';
import api from '../utils/api';

// Main container for chat messages
const ChatCard = styled(Card)(({ theme }) => ({
  width: '900px',
  height: '600px',
  display: 'flex',
  flexDirection: 'column',
  border: '1px solid #3a3a3a',
  borderRadius: '8px',
  backgroundColor: 'transparent',
  boxShadow: 'none',
  [theme.breakpoints.down('md')]: {
    width: '90vw',
    height: '70vh',
  },
}));

// Wrapper for CardContent to enforce full height
const CardContentWrapper = styled(CardContent)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  padding: 0,
  height: '100%',
}));

// Scrollable chat area with explicit height
const ThreadArea = styled(Box)(({ theme }) => ({
  height: '100%', // fill parent container's height
  overflowY: 'auto',
  padding: theme.spacing(2),
}));

const MessageBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1.5),
  borderRadius: '6px',
  marginBottom: theme.spacing(1),
  backgroundColor: '#262626',
}));

// Input form container outside the scrollable area
const InputContainer = styled(Box)(({ theme }) => ({
  width: '900px',
  maxWidth: '90vw',
  display: 'flex',
  gap: theme.spacing(1),
  marginTop: theme.spacing(2),
  [theme.breakpoints.down('md')]: {
    width: '90vw',
  },
}));

const Chat = () => {
  const [message, setMessage] = useState('');
  const [threadId, setThreadId] = useState('');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');

  // Reference to the scrollable container
  const threadRef = useRef(null);

  // Clear threadId on component mount (page reload)
  useEffect(() => {
    setThreadId('');             // Reset state
    localStorage.removeItem('threadId'); // If you are using localStorage to persist threadId
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();

    const userMsg = message.trim();
    if (!userMsg) return;

    setMessage('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setError('');

    try {
      const response = await api.post('/chat', {
        message: userMsg,
        thread_id: threadId,
      });
      const { assistant_message, thread_id } = response.data;
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: assistant_message },
      ]);
      setThreadId(thread_id);
      // If desired, you could also persist the new thread id to localStorage:
      // localStorage.setItem('threadId', thread_id);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message.');
    }
  };

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTo({
        top: threadRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  return (
    <>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
        }}
      >
        {/* Scrollable chat box */}
        <ChatCard>
          <CardContentWrapper>
            <ThreadArea ref={threadRef}>
              {messages.length > 0 ? (
                messages.map((msg, index) => (
                  <MessageBox key={index}>
                    <Typography
                      variant="subtitle2"
                      gutterBottom
                      sx={{
                        color: msg.role === 'user' ? '#61dafb' : '#e0e0e0',
                      }}
                    >
                      {msg.role === 'user' ? 'You:' : 'Agent:'}
                    </Typography>
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      <Typography variant="body2">{msg.content}</Typography>
                    )}
                  </MessageBox>
                ))
              ) : (
                <Typography variant="body2" color="textSecondary" align="center">
                  Start a conversation...
                </Typography>
              )}
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </ThreadArea>
          </CardContentWrapper>
        </ChatCard>

        {/* Input box */}
        <InputContainer component="form" onSubmit={handleSend}>
          <TextField
            fullWidth
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask the property guide a question..."
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                color: '#e0e0e0',
                '& fieldset': {
                  borderColor: '#3a3a3a',
                },
                '&:hover fieldset': {
                  borderColor: '#61dafb',
                },
              },
            }}
          />
          <Button
            type="submit"
            variant="contained"
            sx={{
              backgroundColor: '#61dafb',
              color: '#1e1e1e',
              '&:hover': {
                backgroundColor: '#4db8d9',
              },
              borderRadius: '4px',
              minWidth: '80px',
            }}
          >
            Send
          </Button>
        </InputContainer>
      </Box>
    </>
  );
};

export default Chat;
