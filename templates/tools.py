from typing import Dict, Any, Optional
import requests

# needs to be installed from source: https://github.com/rly/get-nwbfile-info
from get_nwbfile_info import get_nwbfile_usage_script

def dandiset_assets(
    dandiset_id: str,
    version: str = "draft",
    page: int = 1,
    page_size: int = 20,
    glob: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a list of assets/files in a dandiset version.

    The output provides:
    - count: total number of assets
    - results: array of assets with asset_id, path, and size

    Parameters
    ----------
    dandiset_id : str
        DANDI dataset ID
    version : str, optional
        Version of the dataset to retrieve, by default "draft"
    page : int, optional
        Page number, by default 1
    page_size : int, optional
        Number of results per page, by default 20
    glob : str, optional
        Optional glob pattern to filter files (e.g., '*.nwb' for NWB files)

    Returns
    -------
    Dict[str, Any]
        Dictionary containing count and results
    """
    url = "https://neurosift-chat-agent-tools.vercel.app/api/dandiset_assets"
    payload = {
        "dandiset_id": dandiset_id,
        "version": version,
        "page": page,
        "page_size": page_size,
    }
    if glob:
        payload["glob"] = glob

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch dandiset assets: {response.text}")
    return response.json()

def nwb_file_info(dandiset_id: str, nwb_file_url: str) -> str:
    """Get information about an NWB file.

    Includes metadata and information about how to load the neurodata objects
    using pynwb and lindi.

    Parameters
    ----------
    dandiset_id : str
        DANDI dataset ID
    nwb_file_url : str
        URL of the NWB file in the DANDI archive

    Returns
    -------
    Dict[str, Any]
        Dictionary containing NWB file information
    """
    # old method:
    # url = "https://neurosift-chat-agent-tools.vercel.app/api/nwb_file_info"
    # payload = {"dandiset_id": dandiset_id, "nwb_file_url": nwb_file_url}
    # response = requests.post(url, json=payload)
    # if response.status_code != 200:
    #     raise RuntimeError(f"Failed to fetch NWB file info: {response.text}")
    # return response.json()

    # new method:
    script = get_nwbfile_usage_script(nwb_file_url)
    return script

def dandiset_info(dandiset_id: str, version: str = "draft") -> Dict[str, Any]:
    """Get information about a specific version of a DANDI dataset.

    When the version is unknown, use "draft".

    This will return detailed information about the dandiset including:
    name, description, access, license, citation, keywords, protocol,
    contributor names, date created, size, number of files, number of
    subjects, variables measured, and measurement technique.

    Parameters
    ----------
    dandiset_id : str
        DANDI dataset ID
    version : str, optional
        Version of the dataset to retrieve, by default "draft"

    Returns
    -------
    Dict[str, Any]
        Dictionary containing detailed dataset information
    """
    url = "https://neurosift-chat-agent-tools.vercel.app/api/dandiset_info"
    payload = {"dandiset_id": dandiset_id, "version": version}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch dandiset info: {response.text}")
    return response.json()

dandiset_info_spec = {
    "type": "function",
    "function": {
        "name": "dandiset_info",
        "description": """Get information about a specific version of a DANDI dataset.

When the version is unknown, use "draft".

This will return detailed information about the dandiset including:
name, description, access, license, citation, keywords, protocol, contributor names, date created, size, number of files, number of subjects, variables measured, and measurement technique.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "dandiset_id": {"type": "string", "description": "DANDI dataset ID"},
                "version": {
                    "type": "string",
                    "description": "Version of the dataset (optional, defaults to 'draft')",
                },
            },
            "required": ["dandiset_id"],
        },
    },
}
setattr(dandiset_info, "spec", dandiset_info_spec)

dandiset_assets_spec = {
    "type": "function",
    "function": {
        "name": "dandiset_assets",
        "description": """Get a list of assets/files in a dandiset version.

The output provides:
- count: total number of assets
- results: array of assets with asset_id, path, and size

The URL for the asset can be constructed as follows:
https://api.dandiarchive.org/api/assets/<asset_id>/download/

where XXXXXX is the dandiset ID and XXXXX is the version.""",
        "parameters": {
            "type": "object",
            "properties": {
                "dandiset_id": {"type": "string", "description": "DANDI dataset ID"},
                "version": {
                    "type": "string",
                    "description": "Version of the dataset (optional)",
                },
                "page": {"type": "integer", "description": "Page number (optional)"},
                "page_size": {
                    "type": "integer",
                    "description": "Results per page (optional)",
                },
                "glob": {
                    "type": "string",
                    "description": "File pattern filter (optional)",
                },
            },
            "required": ["dandiset_id"],
        },
    },
}
setattr(dandiset_assets, "spec", dandiset_assets_spec)

nwb_file_info_spec = {
    "type": "function",
    "function": {
        "name": "nwb_file_info",
        "description": """Get information about an NWB file, including metadata and information about how to load the neurodata objects using pynwb and lindi.

Be careful not to load too much data at once, as it can be slow and use a lot of memory.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "dandiset_id": {"type": "string", "description": "DANDI dataset ID"},
                "nwb_file_url": {
                    "type": "string",
                    "description": "URL of the NWB file in DANDI",
                },
            },
            "required": ["dandiset_id", "nwb_file_url"],
        },
    },
}
setattr(nwb_file_info, "spec", nwb_file_info_spec)

