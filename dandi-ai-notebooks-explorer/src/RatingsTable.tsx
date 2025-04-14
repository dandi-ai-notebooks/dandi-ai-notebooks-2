import { useMemo, useState } from 'react';
import './RatingsTable.css';
import { Rating } from './types';
import { FormControl, Select, MenuItem, InputLabel } from '@mui/material';

type SortConfig = {
  key: string;
  direction: 'asc' | 'desc';
};

interface Props {
  ratings: Rating[];
}

export default function RatingsTable({ ratings }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDandiset, setSelectedDandiset] = useState<string>('');
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'overall_score',
    direction: 'desc'
  });

  const uniqueDandisets = useMemo(() => {
    const dandisets = [...new Set(ratings.map(r => r.dandiset_id))];
    return dandisets.sort();
  }, [ratings]);
  const rowsPerPage = 1000;

  const handleSort = (key: string) => {
    const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
    setCurrentPage(1); // Reset to first page when sorting changes
  };

  const filteredAndSortedRatings = useMemo(() => {
    const filtered = selectedDandiset
      ? ratings.filter(r => r.dandiset_id === selectedDandiset)
      : ratings;

    const sorted = [...filtered];
    sorted.sort((a, b) => {
      let aValue: string | number = '';
      let bValue: string | number = '';

      if (sortConfig.key === 'dandiset_id') {
        aValue = a.dandiset_id;
        bValue = b.dandiset_id;
      } else if (sortConfig.key === 'model') {
        aValue = a.subfolder.split('-').slice(1).join('-');
        bValue = b.subfolder.split('-').slice(1).join('-');
      } else if (sortConfig.key === 'overall_score') {
        aValue = a.overall_score;
        bValue = b.overall_score;
      } else if (sortConfig.key.startsWith('score_')) {
        const scoreIndex = parseInt(sortConfig.key.split('_')[1]);
        aValue = a.scores[scoreIndex]?.score ?? -Infinity;
        bValue = b.scores[scoreIndex]?.score ?? -Infinity;
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
  }, [ratings, sortConfig, selectedDandiset]);

  const pageCount = Math.ceil(filteredAndSortedRatings.length / rowsPerPage);
  const currentRatings = filteredAndSortedRatings.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const ScoreTooltip = ({ content }: { content: React.ReactNode }) => (
    <div className="tooltip-container">
      <div className="tooltip-content">
        {content}
      </div>
    </div>
  );

  return (
    <div className="ratings-table-container">
      <h2>DANDI AI Notebooks Explorer</h2>

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
              <th onClick={() => handleSort('dandiset_id')} className="sortable">
                <span>Dandiset ID</span>
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
              <th onClick={() => handleSort('overall_score')} className="sortable">
                <span>Overall Score</span>
                {sortConfig.key === 'overall_score' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              {ratings[0]?.scores.map((score, index) => (
                <th
                  key={score.name}
                  onClick={() => handleSort(`score_${index}`)}
                  className="sortable"
                >
                  <span>{score.name}</span>
                  {sortConfig.key === `score_${index}` && (
                    <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRatings.map((rating, index) => (
              <tr key={index}>
                <td>{rating.dandiset_id}</td>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/${rating.dandiset_id}/blob/main/${rating.subfolder}/${rating.dandiset_id}.ipynb`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {rating.subfolder.split('-').slice(1).join('-')}
                  </a>
                </td>
                <td className="score-cell">
                  {rating.overall_score.toFixed(1)}
                </td>
                {rating.scores.map((score, i) => (
                  <td key={i} className="score-cell">
                    <div className="tooltip-wrapper">
                      {score.score.toFixed(1)}
                      <ScoreTooltip
                        content={
                          <div>
                            {score.reps.map((rep, i) => (
                              <div key={i}>
                                <strong>Rep {rep.repnum}:</strong> {rep.score.toFixed(1)}
                              </div>
                            ))}
                          </div>
                        }
                      />
                    </div>
                  </td>
                ))}
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
