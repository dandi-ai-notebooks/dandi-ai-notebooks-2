# Notebook review 000673/2025-04-15-claude-3.7-sonnet-prompt-a-3

https://neurosift.app/nwb?url=https://api.dandiarchive.org/api/assets/65a7e913-45c7-48db-bf19-b9f5e910110a/download/&dandisetId=000673&dandisetVersion=draft

GRADE: FAIL

⚠️ Title is not formatted as a heading

✅ Caution statement about AI

✅ Overview of Dandiset

❌ Does not provide neurosift link to the Dandiset

✅ Outline of what the notebook will cover

✅ Listing of required packages

✅ Loading dandiset with DandiAPIClient

❌ Does not load Dandiset metadata

✅ List assets

✅ Load remote nwb file for streaming using NWBHDF5IO

❌ Does not specify which session is being loaded, just has URL and doesn't specify how to get it

❌ Displays contents of nwb file - however the output cell is **way** too long, especially with showing the data for waveforms. This is a problem with pynwb render of nwb.

✅ Get metadata for NWB file (identifier, session_description, session_start_time)

✅ Load LFP data and visualize a subset

✅ Load stimulus data and visualize a subset

✅ Load stimulus images and visualize a subset

❌ Does not show trials data - start_times, stop_times and a bunch of other data in a rich table. This is a failure of get-nwbfile-info (see below)

❌ Does not show units data. This is a failure of get-nwbfile-info (see below)

✅ Summary and future directions

❌ get-nwbfile-info does not show details about the trials table. It just includes the following

```python
nwb.trials # (TimeIntervals)
# nwb.trials.to_dataframe() # (DataFrame) Convert to a pandas DataFrame with 140 rows and 19 columns
# nwb.trials.to_dataframe().head() # (DataFrame) Show the first few rows of the pandas DataFrame
nwb.trials.description # (str) Intervals for the Sternberg Task
nwb.trials.colnames # (tuple)
nwb.trials.columns # (tuple)
nwb.trials.id # (ElementIdentifiers)
```

Should show start_times, stop_times, and list all of the columns with their descriptions and how to access them.

❌ get-nwbfile-info does not show details about the units table. Similar to above.
