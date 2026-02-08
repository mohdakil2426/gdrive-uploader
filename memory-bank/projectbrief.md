# Project Brief: Universal Google Drive Uploader

## Project Overview
A universal file uploader that transfers files from any URL directly to Google Drive without using local bandwidth or storage. Designed to run on Google Colab (primary) or Google Cloud VM (secondary).

## Core Requirements

### Primary Goal
- Upload any file from any URL directly to Google Drive
- Zero local network/storage usage (all transfers happen on Google's servers)
- Support for all file types and formats

### Target Platforms
1. **Google Colab** (Primary) - Free, fast, no setup
2. **Google Cloud VM** (Secondary) - For automation/scripting

### Key Features
- Direct URL → Google Drive streaming
- Progress tracking with percentage and speed
- Support for video sites via yt-dlp
- Folder organization in Drive
- Resumable uploads for large files
- Storage quota checking

## User Profile
- Owner: Akila
- Google One AI Premium subscriber (2TB storage)
- Use case: Transfer large files without consuming local bandwidth

## Success Criteria
1. Paste any URL → File appears in Google Drive
2. No local download required
3. Works with direct links and video sites
4. Shows upload progress
5. Handles files of any size
