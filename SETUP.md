# Daily Quote Auto-Update Setup Guide

This repository automatically updates the GitHub Profile README with a daily inspirational quote from mathematicians, statisticians, or computer scientists using Google's Gemini API.

## Setup Instructions

### 1. Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Add API Key as GitHub Secret

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `GEMINI_API_KEY`
5. Value: Paste your Gemini API key
6. Click **Add secret**

### 3. Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **Read and write permissions**
3. Check **Allow GitHub Actions to create and approve pull requests**
4. Save changes

### 4. Test the Workflow

1. Go to **Actions** tab in your repository
2. Select **Update Daily Quote** workflow
3. Click **Run workflow** → **Run workflow** (manual trigger)
4. Wait for it to complete and verify the README was updated

## How It Works

- The workflow runs automatically every day at **00:00 UTC**
- It calls the Gemini 1.5 Flash API to generate a fresh quote
- The quote is inserted into README.md between `<!-- DAILY QUOTE -->` markers
- Changes are automatically committed and pushed

## Manual Trigger

You can manually trigger the workflow anytime:
- Go to **Actions** → **Update Daily Quote** → **Run workflow**

## Troubleshooting

- **Workflow fails**: Check that `GEMINI_API_KEY` secret is set correctly
- **No quote appears**: Verify the API key has access to Gemini API
- **Quote format issues**: The workflow includes fallback handling for parsing errors

