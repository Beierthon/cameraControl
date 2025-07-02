# Robot Automation NUC (Host/Server/Brain)

This repository contains the software for the ASUS NUC, acting as the central orchestrator for our 3D print automation system. It manages the workflow, communicates with the Raspberry Pi (robot arm), controls the camera, performs image analysis, and interacts with the Supabase database.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Setup and Installation](#setup-and-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create and Configure Environment Variables](#2-create-and-configure-environment-variables)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Database Setup (Supabase)](#4-database-setup-supabase)
  - [5. Firewall Configuration](#5-firewall-configuration)
- [Running the Orchestrator](#running-the-orchestrator)
- [Workflow Overview](#workflow-overview)
- [Extending and Customizing](#extending-and-customizing)
- [Troubleshooting](#troubleshooting)

## Features

-   **Supabase Integration:** Monitors and updates print job statuses in real-time.
-   **Socket Server:** Establishes and maintains communication with the Raspberry Pi robot client.
-   **Camera Control:** Captures images of 3D printed objects.
-   **Image Analysis:** Placeholder for computer vision algorithms to determine print quality.
-   **Workflow Orchestration:** Manages the sequence of operations (e.g., waiting for print, initiating robot action, taking photo, analyzing, updating DB).

## System Requirements

-   ASUS NUC running a Linux distribution (e.g., Ubuntu, Debian)
-   Python 3.8+
-   Internet connection (for Supabase and initial setup)
-   Webcam connected to the NUC (for image capture)
-   Access to your Supabase project URL and API Key

## Setup and Installation

### 1. Clone the Repository

SSH into your ASUS NUC:
```bash
ssh lernfabrik@192.168.68.201
```
Navigate to your desired directory (e.g., `Documents`):
```bash
cd ~/Documents
```
Clone the repository:
```bash
git clone https://github.com/yourusername/robot-automation-nuc.git
cd robot-automation-nuc
```

### 2. Create and Configure Environment Variables

Create a `.env` file from the example:
```bash
cp .env.example .env
```
Open the `.env` file using `nano` and fill in your Supabase project details:
```bash
nano .env
```
Replace the placeholder values with your actual Supabase URL and public API key:

SUPABASE_URL="https://your_project_ref.supabase.co"
SUPABASE_KEY="YOUR_ACTUAL_SUPABASE_ANON_PUBLIC_KEY"

Save and exit `nano` (`Ctrl+O`, `Enter`, `Ctrl+X`).

### 3. Install Dependencies

It's highly recommended to use a Python virtual environment to manage dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
