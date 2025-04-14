import { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  CircularProgress,
  Container,
  Typography
} from '@mui/material';
import { Rating } from './types';
import RatingsTable from './RatingsTable';
import axios from 'axios';

const darkTheme = createTheme({
  palette: {
    mode: 'light',
  },
});

function App() {
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRatings();
  }, []);

  const loadRatings = async () => {
    try {
      const response = await axios.get('https://raw.githubusercontent.com/dandi-ai-notebooks/dandi-ai-notebooks-2/refs/heads/main/ratings.json');
      setRatings(response.data);
    } catch (err) {
      setError('Failed to load ratings data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth={false}>
        <RatingsTable ratings={ratings} />
      </Container>
    </ThemeProvider>
  );
}

export default App;
