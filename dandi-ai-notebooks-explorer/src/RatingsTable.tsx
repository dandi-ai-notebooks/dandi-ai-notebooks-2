import { useMemo, useState } from 'react';
import './RatingsTable.css';
import { Rating } from './types';
import { FormControl, Select, MenuItem, InputLabel } from '@mui/material';

const calculateEstimatedCost = (rating: Rating) => {
  const getModelCost = (model: string): [number | undefined, number | undefined] => {
    if (model === 'google/gemini-2.0-flash-001') return [0.1, 0.4];
    else if (model === 'openai/gpt-4o') return [2.5, 10];
    else if (model === 'anthropic/claude-3.5-sonnet') return [3, 15];
    else if (model === 'anthropic/claude-3.7-sonnet') return [3, 15];
    else if (model === 'anthropic/claude-3.7-sonnet:thinking') return [3, 15];
    else if (model === 'deepseek/deepseek-r1') return [0.55, 2.19];
    else if (model === 'deepseek/deepseek-chat-v3-0324') return [0.27, 1.1];
    return [undefined, undefined];
  };

  if (!rating.metadata) return 0;

  const [promptCost, completionCost] = getModelCost(rating.metadata.model);
  if (promptCost === undefined || completionCost === undefined) return undefined;
  if (!rating.metadata) return undefined;
  const totalPromptTokens = (rating.metadata.total_prompt_tokens || 0) + (rating.metadata.total_vision_prompt_tokens || 0);
  const totalCompletionTokens = (rating.metadata.total_completion_tokens || 0) + (rating.metadata.total_vision_completion_tokens || 0);

  return ((totalPromptTokens / 1e6 * promptCost) + (totalCompletionTokens / 1e6 * completionCost));
};

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
    key: 'date',
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
        aValue = a.metadata?.model?.split('/')[1] || '';
        bValue = b.metadata?.model?.split('/')[1] || '';
      } else if (sortConfig.key === 'prompt') {
        aValue = promptFromSubfolder(a.subfolder);
        bValue = promptFromSubfolder(b.subfolder);
      }
      else if (sortConfig.key === 'date') {
        aValue = dateFromSubfolder(a.subfolder);
        bValue = dateFromSubfolder(b.subfolder);
      }
      else if (sortConfig.key === 'overall_score') {
        aValue = a.overall_score;
        bValue = b.overall_score;
      } else if (sortConfig.key === 'est_cost') {
        aValue = calculateEstimatedCost(a) || 0;
        bValue = calculateEstimatedCost(b) || 0;
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
              <th onClick={() => handleSort('est_cost')} className="sortable">
                <span>Est. Cost ($)</span>
                {sortConfig.key === 'est_cost' && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            </tr>
          </thead>
          <tbody>
            {currentRatings.map((rating, index) => (
              <tr key={index}>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/${rating.dandiset_id}/blob/main/${rating.subfolder}/${rating.dandiset_id}.ipynb`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {
                      rating.dandiset_id + ".ipynb"
                    }
                  </a>
                </td>
                <td>{rating.dandiset_id}</td>
                <td>
                  {
                    rating.metadata?.model?.split("/")[1] || ""
                  }
                </td>
                <td>
                  <a
                    href={`https://github.com/dandi-ai-notebooks/dandi-ai-notebooks-2/blob/main/templates/${promptFromSubfolder(rating.subfolder)}.txt`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {promptFromSubfolder(rating.subfolder)}
                  </a>
                </td>
                <td>
                  {
                    dateFromSubfolder(rating.subfolder)
                  }
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
                <td className="score-cell">
                  {calculateEstimatedCost(rating) ? calculateEstimatedCost(rating)?.toFixed(2) : '--'}
                </td>
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
  // subfolder is going to be 2025-04-15-model-name-prompt-a-1
  // we need to get everything after "prompt-"
  const prompt = subfolder.split('prompt-')[1];
  if (!prompt) return '';
  return 'prompt-' + prompt;
}

const dateFromSubfolder = (subfolder: string) => {
  // subfolder is going to be 2025-04-15-model-name-prompt-a-1
  return subfolder.split('-').slice(0, 3).join('-');
}
