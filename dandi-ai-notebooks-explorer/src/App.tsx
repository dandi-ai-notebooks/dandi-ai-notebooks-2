import { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  CircularProgress,
  Container,
  Typography,
  Tabs,
  Tab
} from '@mui/material';
import { Rating, PlotRating } from './types';
import RatingsTable from './RatingsTable';
import PlotRatingsTable from './PlotRatingsTable';
import axios from 'axios';

const darkTheme = createTheme({
  palette: {
    mode: 'light',
  },
});

function App() {
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [plotRatings, setPlotRatings] = useState<PlotRating[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);

  useEffect(() => {
    loadAllRatings();
  }, []);

  const loadAllRatings = async () => {
    try {
      const [ratingsResponse, plotRatingsResponse] = await Promise.all([
        axios.get('https://raw.githubusercontent.com/dandi-ai-notebooks/dandi-ai-notebooks-2/refs/heads/main/ratings.json'),
        axios.get('https://raw.githubusercontent.com/dandi-ai-notebooks/dandi-ai-notebooks-2/refs/heads/main/plot_ratings.json')
      ]);
      setRatings(ratingsResponse.data);
      setPlotRatings(plotRatingsResponse.data);
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
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
            <Tab label="Notebooks" />
            <Tab label="Plots" />
          </Tabs>
        </Box>
        {currentTab === 0 ? (
          <RatingsTable ratings={ratings} />
        ) : (
          <PlotRatingsTable plotRatings={plotRatings} />
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;
