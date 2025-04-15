import { useMemo, useState } from 'react';
import './RatingsTable.css';
import { PlotRating } from './types';
import { FormControl, Select, MenuItem, InputLabel } from '@mui/material';

type SortConfig = {
  key: string;
  direction: 'asc' | 'desc';
};

interface Props {
  plotRatings: PlotRating[];
}

export default function PlotRatingsTable({ plotRatings }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDandiset, setSelectedDandiset] = useState<string>('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'date',
    direction: 'desc'
  });

  const uniqueDandisets = useMemo(() => {
    const dandisets = [...new Set(plotRatings.map(r => r.dandiset_id))];
    return dandisets.sort();
  }, [plotRatings]);
  const rowsPerPage = 1000;

  const handleSort = (key: string) => {
    const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
    setCurrentPage(1);
  };

  // Transform plot ratings into rows for the table
  const plotRows = useMemo(() => {
    return plotRatings.flatMap(rating =>
      rating.plots.map(plot => ({
        notebook: rating.notebook,
        subfolder: rating.subfolder,
        dandiset_id: rating.dandiset_id,
        model: rating.metadata?.model?.split('/')[1] || '',
        prompt: promptFromSubfolder(rating.subfolder),
        date: dateFromSubfolder(rating.subfolder),
        plot_id: plot.plot_id,
        quality_score: plot.scores[0]?.score || 0
      }))
    );
  }, [plotRatings]);

  const filteredAndSortedPlots = useMemo(() => {
    const filtered = selectedDandiset
      ? plotRows.filter(r => r.dandiset_id === selectedDandiset)
      : plotRows;

    const sorted = [...filtered];
    sorted.sort((a, b) => {
      let aValue: string | number = '';
      let bValue: string | number = '';

      if (sortConfig.key === 'dandiset_id') {
        aValue = a.dandiset_id;
        bValue = b.dandiset_id;
      } else if (sortConfig.key === 'model') {
        aValue = a.model;
        bValue = b.model;
      } else if (sortConfig.key === 'prompt') {
        aValue = a.prompt;
        bValue = b.prompt;
      } else if (sortConfig.key === 'date') {
        aValue = a.date;
        bValue = b.date;
      } else if (sortConfig.key === 'plot_id') {
        aValue = a.plot_id;
        bValue = b.plot_id;
      } else if (sortConfig.key === 'quality_score') {
        aValue = a.quality_score;
        bValue = b.quality_score;
      }

      if (typeof aValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue as string)
          : (bValue as string).localeCompare(aValue);
      }

      return sortConfig.direction === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });
    return sorted;
  }, [plotRows, sortConfig, selectedDandiset]);

  const pageCount = Math.ceil(filteredAndSortedPlots.length / rowsPerPage);
  const currentPlots = filteredAndSortedPlots.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  return (
    <div className="ratings-table-container">
      <h2>DANDI AI Notebooks Plot Explorer</h2>

      <FormControl sx={{ minWidth: 200, mb: 2 }}>
        <InputLabel id="dandiset-select-label">Filter by Dandiset ID</InputLabel>
        <Select
          labelId="dandiset-select-label"
          value={selectedDandiset}
          label="Filter by Dandiset ID"
          onChange={(e) => {
            setSelectedDandiset(e.target.value);
            setCurrentPage(1);
          }}
        >
          <MenuItem value="">
            <em>All Dandisets</em>
          </MenuItem>
          {uniqueDandisets.map((id) => (
            <MenuItem key={id} value={id}>{id}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>
                <span>Notebook</span>
              </th>
              <th onClick={() => handleSort('dandiset_id')} className="sortable">
                <span>Dandiset</span>
                {sortConfig.key === 'dandiset_id' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th onClick={() => handleSort('model')} className="sortable">
                <span>Model</span>
                {sortConfig.key === 'model' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th onClick={() => handleSort('prompt')} className="sortable">
                <span>Prompt</span>
                {sortConfig.key === 'prompt' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th onClick={() => handleSort('date')} className="sortable">
                <span>Date</span>
                {sortConfig.key === 'date' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th onClick={() => handleSort('plot_id')} className="sortable">
                <span>Plot ID</span>
                {sortConfig.key === 'plot_id' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th onClick={() => handleSort('quality_score')} className="sortable">
                <span>Quality Score</span>
                {sortConfig.key === 'quality_score' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            </tr>
          </thead>
          <tbody>
            {currentPlots.map((plot, index) => (
              <tr key={index}>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/${plot.dandiset_id}/blob/main/${plot.subfolder}/${plot.dandiset_id}.ipynb`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {plot.dandiset_id + ".ipynb"}
                  </a>
                </td>
                <td>{plot.dandiset_id}</td>
                <td>{plot.model}</td>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/dandi-ai-notebooks-2/blob/main/templates/${plot.prompt}.txt`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {plot.prompt}
                  </a>
                </td>
                <td>{plot.date}</td>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/${plot.dandiset_id}/blob/main/${plot.subfolder}/plot_images/${plot.plot_id}.png`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {plot.plot_id}
                  </a>
                </td>
                <td className="score-cell">{plot.quality_score.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        {pageCount > 1 && (
          <>
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span>
              Page {currentPage} of {pageCount}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(pageCount, p + 1))}
              disabled={currentPage === pageCount}
            >
              Next
            </button>
          </>
        )}
      </div>
    </div>
  );
}

const promptFromSubfolder = (subfolder: string) => {
  const prompt = subfolder.split('prompt-')[1];
  if (!prompt) return '';
  return 'prompt-' + prompt;
}

const dateFromSubfolder = (subfolder: string) => {
  return subfolder.split('-').slice(0, 3).join('-');
}
